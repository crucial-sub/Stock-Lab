"""
모멘텀/펀더멘털 점수 일괄 계산 스크립트

사용 예시:
    python scripts/update_company_scores.py
    python scripts/update_company_scores.py --dry-run
"""
import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.orm import Session

# 프로젝트 루트를 PYTHONPATH에 추가
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.models.balance_sheet import BalanceSheet  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.income_statement import IncomeStatement  # noqa: E402


def build_sync_engine(db_url: str):
    """async URL을 sync URL로 변환해 엔진 생성"""
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return create_engine(db_url, future=True)


def fetch_price_snapshot(engine) -> pd.DataFrame:
    """최근 260거래일 시세 데이터를 company_id별로 가져온다."""
    price_sql = """
        WITH ranked AS (
            SELECT
                c.company_id,
                c.stock_code,
                sp.trade_date,
                sp.close_price,
                sp.market_cap,
                sp.listed_shares,
                ROW_NUMBER() OVER (
                    PARTITION BY c.company_id
                    ORDER BY sp.trade_date DESC
                ) AS rn
            FROM stock_prices sp
            JOIN companies c ON c.company_id = sp.company_id
            WHERE c.is_active = 1
        )
        SELECT *
        FROM ranked
        WHERE rn <= 260;
    """
    df = pd.read_sql_query(price_sql, engine)
    logger.info("시세 데이터 로드 완료: %d rows", len(df))
    return df


def percentile(series: pd.Series, reverse: bool = False) -> pd.Series:
    """백분위 점수(0~100). reverse=True면 낮을수록 고득점."""
    pct = series.rank(pct=True, method="average") * 100
    if reverse:
        pct = 100 - pct
    return pct


def safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """0 나눗셈/INF를 NaN으로 처리하는 안전 나눗셈."""
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    result = num / den
    return result.replace([np.inf, -np.inf], np.nan)


def compute_momentum_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    """모멘텀/변동성 지표 계산"""
    rn_map = {
        1: "price_latest",
        21: "price_1m",
        63: "price_3m",
        126: "price_6m",
        252: "price_12m",
    }
    price_subset = prices[prices["rn"].isin(rn_map.keys())].copy()
    price_subset["rn_label"] = price_subset["rn"].map(rn_map)
    pivot = price_subset.pivot_table(
        index="company_id", columns="rn_label", values="close_price"
    )

    pivot = pivot.reindex(columns=rn_map.values(), fill_value=np.nan)

    momentum_df = pd.DataFrame(index=pivot.index)
    momentum_df["mom_1m"] = (pivot["price_latest"] - pivot["price_1m"]) / pivot["price_1m"] * 100
    momentum_df["mom_3m"] = (pivot["price_latest"] - pivot["price_3m"]) / pivot["price_3m"] * 100
    momentum_df["mom_6m"] = (pivot["price_latest"] - pivot["price_6m"]) / pivot["price_6m"] * 100
    momentum_df["mom_12m"] = (pivot["price_latest"] - pivot["price_12m"]) / pivot["price_12m"] * 100
    momentum_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    recent = prices[prices["rn"] <= 21].copy()
    recent.sort_values(["company_id", "rn"], ascending=[True, False], inplace=True)
    recent["return"] = recent.groupby("company_id")["close_price"].pct_change()
    vol = recent.groupby("company_id")["return"].std(ddof=0) * math.sqrt(252) * 100
    momentum_df["volatility_20d"] = vol
    return momentum_df


def fetch_financial_statements(session: Session) -> Dict[int, Dict[str, Tuple[int, int]]]:
    """각 기업의 최신/직전 재무제표 ID 맵."""
    stmt_rows = session.execute(
        text(
            """
            WITH ranked AS (
                SELECT
                    fs.company_id,
                    fs.stmt_id,
                    fs.bsns_year,
                    fs.reprt_code,
                    ROW_NUMBER() OVER (
                        PARTITION BY fs.company_id
                        ORDER BY COALESCE(NULLIF(fs.bsns_year, '')::int, 0) DESC,
                             CASE fs.reprt_code
                                 WHEN '11011' THEN 4
                                 WHEN '11012' THEN 3
                                 WHEN '11014' THEN 2
                                 WHEN '11013' THEN 1
                                 ELSE 0
                             END DESC
                    ) AS rn
                FROM financial_statements fs
                JOIN companies c ON c.company_id = fs.company_id
                WHERE c.is_active = 1
            )
            SELECT company_id, stmt_id, bsns_year, reprt_code, rn
            FROM ranked
            WHERE rn <= 2
            """
        )
    ).fetchall()

    statements: Dict[int, Dict[str, Tuple[int, int]]] = defaultdict(dict)
    for row in stmt_rows:
        comp_id = row.company_id
        bucket = "current" if row.rn == 1 else "previous"
        try:
            year = int(row.bsns_year)
        except (TypeError, ValueError):
            year = 0
        statements[comp_id][bucket] = (row.stmt_id, year)
    logger.info("재무제표 매핑 완료: %d개 기업", len(statements))
    return statements


def load_statement_items(
    session: Session, stmt_ids: List[int]
) -> Tuple[Dict[int, List[Tuple[str, Optional[int]]]], Dict[int, List[Tuple[str, Optional[int]]]]]:
    """재무제표 ID별 손익/재무 상태표 항목을 한 번에 로드."""
    if not stmt_ids:
        return {}, {}

    income_rows = session.execute(
        select(
            IncomeStatement.stmt_id,
            IncomeStatement.account_nm,
            IncomeStatement.thstrm_amount,
        ).where(IncomeStatement.stmt_id.in_(stmt_ids))
    ).all()

    balance_rows = session.execute(
        select(
            BalanceSheet.stmt_id,
            BalanceSheet.account_nm,
            BalanceSheet.thstrm_amount,
        ).where(BalanceSheet.stmt_id.in_(stmt_ids))
    ).all()

    income_map: Dict[int, List[Tuple[str, Optional[int]]]] = defaultdict(list)
    balance_map: Dict[int, List[Tuple[str, Optional[int]]]] = defaultdict(list)

    for row in income_rows:
        income_map[row.stmt_id].append((row.account_nm or "", row.thstrm_amount))

    for row in balance_rows:
        balance_map[row.stmt_id].append((row.account_nm or "", row.thstrm_amount))

    logger.info(
        "손익(%d rows) / 재무상태(%d rows) 로드 완료",
        len(income_rows),
        len(balance_rows),
    )
    return income_map, balance_map


def parse_income(items: List[Tuple[str, Optional[int]]]) -> Dict[str, Optional[float]]:
    """손익계산서에서 필요한 항목 추출."""
    metrics = {
        "revenue": None,
        "operating_income": None,
        "net_income": None,
    }
    for raw_name, amount in items:
        if amount is None:
            continue
        name = raw_name.replace(" ", "")
        if ("매출액" in name or "Revenue" in name) and "매출원가" not in name and "총매출" not in name:
            metrics["revenue"] = float(amount)
        elif "매출원가" in name or "CostOfRevenue" in name:
            # currently unused but placeholder
            continue
        elif "영업이익" in name or "영업손실" in name or "OperatingProfit" in name:
            metrics["operating_income"] = float(amount)
        elif "당기순이익" in name or "당기순손실" in name or "ProfitLoss" in name:
            metrics["net_income"] = float(amount)
    return metrics


def parse_balance(items: List[Tuple[str, Optional[int]]]) -> Dict[str, Optional[float]]:
    """재무상태표에서 필요한 항목 추출."""
    metrics = {
        "total_assets": None,
        "total_liabilities": None,
        "total_equity": None,
        "current_assets": None,
        "current_liabilities": None,
    }
    for raw_name, amount in items:
        if amount is None:
            continue
        name = raw_name.replace(" ", "")
        value = float(amount)
        if "자산총계" in name or "TotalAssets" in name:
            metrics["total_assets"] = value
        elif "부채총계" in name or "TotalLiabilities" in name:
            metrics["total_liabilities"] = value
        elif "자본총계" in name or "TotalEquity" in name:
            metrics["total_equity"] = value
        elif "유동자산" in name or "CurrentAssets" in name:
            metrics["current_assets"] = value
        elif "유동부채" in name or "CurrentLiabilities" in name:
            metrics["current_liabilities"] = value
    return metrics


def build_fundamental_frame(
    session: Session,
    statements: Dict[int, Dict[str, Tuple[int, int]]],
) -> pd.DataFrame:
    """기업별 펀더멘털 계산에 필요한 기초 데이터프레임 생성."""
    all_stmt_ids = [data[0] for company in statements.values() for data in company.values()]
    income_map, balance_map = load_statement_items(session, all_stmt_ids)

    records = []
    for company_id, stmt_dict in statements.items():
        latest_stmt = stmt_dict.get("current")
        previous_stmt = stmt_dict.get("previous")
        if not latest_stmt:
            continue

        latest_income = parse_income(income_map.get(latest_stmt[0], []))
        latest_balance = parse_balance(balance_map.get(latest_stmt[0], []))

        prev_income = parse_income(income_map.get(previous_stmt[0], [])) if previous_stmt else {"revenue": None, "operating_income": None, "net_income": None}

        record = {
            "company_id": company_id,
            "net_income": latest_income["net_income"],
            "operating_income": latest_income["operating_income"],
            "revenue": latest_income["revenue"],
            "total_equity": latest_balance["total_equity"],
            "total_assets": latest_balance["total_assets"],
            "total_liabilities": latest_balance["total_liabilities"],
            "current_assets": latest_balance["current_assets"],
            "current_liabilities": latest_balance["current_liabilities"],
            "prev_revenue": prev_income["revenue"],
            "prev_operating_income": prev_income["operating_income"],
            "prev_net_income": prev_income["net_income"],
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    logger.info("펀더멘털 기본 데이터프레임 생성: %d개 기업", len(df))
    return df


def compute_fundamental_metrics(
    fundamentals: pd.DataFrame, latest_prices: pd.DataFrame
) -> pd.DataFrame:
    """밸류에이션/성장/재무안정 지표 계산."""
    merged = fundamentals.merge(
        latest_prices[["company_id", "stock_code", "market_cap", "listed_shares"]],
        on="company_id",
        how="left",
    )

    merged["roe"] = safe_div(merged["net_income"], merged["total_equity"]) * 100
    merged["roa"] = safe_div(merged["net_income"], merged["total_assets"]) * 100
    merged["oper_margin"] = safe_div(merged["operating_income"], merged["revenue"]) * 100

    merged["sales_yoy"] = safe_div(merged["revenue"] - merged["prev_revenue"], merged["prev_revenue"]) * 100
    merged["op_income_yoy"] = safe_div(
        merged["operating_income"] - merged["prev_operating_income"],
        merged["prev_operating_income"],
    ) * 100

    merged["eps"] = safe_div(merged["net_income"], merged["listed_shares"])
    merged["eps_prev"] = safe_div(merged["prev_net_income"], merged["listed_shares"])
    merged["eps_yoy"] = safe_div(merged["eps"] - merged["eps_prev"], merged["eps_prev"]) * 100

    merged["per"] = safe_div(merged["market_cap"], merged["net_income"])
    merged["pbr"] = safe_div(merged["market_cap"], merged["total_equity"])
    merged["psr"] = safe_div(merged["market_cap"], merged["revenue"])

    merged["debt_ratio"] = safe_div(merged["total_liabilities"], merged["total_equity"])
    merged["current_ratio"] = safe_div(merged["current_assets"], merged["current_liabilities"])
    merged["net_debt_to_cf"] = np.nan  # placeholder (데이터 부족 시)
    return merged


def calculate_scores(momentum_df: pd.DataFrame, fundamentals_df: pd.DataFrame) -> pd.DataFrame:
    """모멘텀/펀더멘털 점수를 0~100으로 계산."""
    metrics = fundamentals_df.set_index("company_id").join(momentum_df, how="left")

    metrics["mom_1m_pct"] = percentile(metrics["mom_1m"])
    metrics["mom_3m_pct"] = percentile(metrics["mom_3m"])
    metrics["mom_6m_pct"] = percentile(metrics["mom_6m"])
    metrics["mom_12m_pct"] = percentile(metrics["mom_12m"])
    metrics["volatility_pct"] = percentile(metrics["volatility_20d"], reverse=True)

    metrics["momentum_score"] = (
        0.35 * metrics["mom_12m_pct"]
        + 0.30 * metrics["mom_6m_pct"]
        + 0.20 * metrics["mom_3m_pct"]
        + 0.05 * metrics["mom_1m_pct"]
        + 0.10 * metrics["volatility_pct"]
    ).clip(0, 100)

    metrics["roe_pct"] = percentile(metrics["roe"])
    metrics["oper_margin_pct"] = percentile(metrics["oper_margin"])
    metrics["roa_pct"] = percentile(metrics["roa"])
    profitability = metrics[["roe_pct", "oper_margin_pct", "roa_pct"]].mean(axis=1)

    metrics["sales_yoy_pct"] = percentile(metrics["sales_yoy"])
    metrics["op_income_yoy_pct"] = percentile(metrics["op_income_yoy"])
    metrics["eps_yoy_pct"] = percentile(metrics["eps_yoy"])
    growth = metrics[["sales_yoy_pct", "op_income_yoy_pct", "eps_yoy_pct"]].mean(axis=1)

    metrics["per_pct"] = percentile(metrics["per"], reverse=True)
    metrics["pbr_pct"] = percentile(metrics["pbr"], reverse=True)
    metrics["psr_pct"] = percentile(metrics["psr"], reverse=True)
    value = metrics[["per_pct", "pbr_pct", "psr_pct"]].mean(axis=1)

    metrics["debt_ratio_pct"] = percentile(metrics["debt_ratio"], reverse=True)
    metrics["current_ratio_pct"] = percentile(metrics["current_ratio"])
    stability = metrics[["debt_ratio_pct", "current_ratio_pct"]].mean(axis=1)

    metrics["fundamental_score"] = (
        0.30 * profitability
        + 0.25 * growth
        + 0.25 * value
        + 0.20 * stability
    ).clip(0, 100)

    scores = metrics[["momentum_score", "fundamental_score"]].reset_index()
    return scores


def update_company_scores(
    session: Session, scores: pd.DataFrame, dry_run: bool = False
) -> int:
    """companies 테이블에 점수 저장."""
    scores = scores.replace({np.nan: None})
    updated = 0
    for row in scores.itertuples(index=False):
        session.execute(
            update(Company)
            .where(Company.company_id == row.company_id)
            .values(
                momentum_score=row.momentum_score,
                fundamental_score=row.fundamental_score,
            )
        )
        updated += 1

    if dry_run:
        session.rollback()
    else:
        session.commit()
    return updated


def main():
    parser = argparse.ArgumentParser(description="모멘텀/펀더멘털 점수 계산")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="계산만 수행하고 DB에는 반영하지 않습니다.",
    )
    args = parser.parse_args()

    load_dotenv()
    settings = get_settings()
    engine = build_sync_engine(settings.DATABASE_URL)

    price_df = fetch_price_snapshot(engine)
    latest_prices = price_df[price_df["rn"] == 1].rename(columns={"close_price": "latest_close"})

    momentum_df = compute_momentum_metrics(price_df)

    with Session(engine) as session:
        stmt_map = fetch_financial_statements(session)
        fundamentals = build_fundamental_frame(session, stmt_map)

    if fundamentals.empty:
        logger.warning("재무 데이터가 없어 점수를 계산할 수 없습니다.")
        return

    fundamental_metrics = compute_fundamental_metrics(fundamentals, latest_prices)
    score_df = calculate_scores(momentum_df, fundamental_metrics)

    with Session(engine) as session:
        updated = update_company_scores(session, score_df, dry_run=args.dry_run)

    if args.dry_run:
        logger.info("Dry-run 완료: %d개 기업 점수 계산 (DB 미적용)", updated)
    else:
        logger.info("점수 업데이트 완료: %d개 기업", updated)


if __name__ == "__main__":
    main()
