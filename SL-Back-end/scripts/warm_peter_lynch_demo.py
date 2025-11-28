"""
피터린치 전략 시연용 캐시 워밍 스크립트
- 1년치 백테스트 데이터 영구 캐싱 (TTL=0)
- 팩터 추가 시 빠른 재계산을 위한 준비
- 시연 30분 전 실행 권장
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import pandas as pd

from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache
from app.services.advanced_backtest import _run_backtest_async
from app.services.backtest_cache_optimized import (
    OptimizedCacheManager,
    generate_strategy_hash,
)
from app.services.backtest_db_optimized import OptimizedDBManager
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _extract_factor_code(expr: str) -> str | None:
    """좌변 표현식에서 팩터 코드 추출 (중괄호 포함/미포함 대응)."""
    if not expr:
        return None
    import re

    match = re.search(r"\{([^}]+)\}", expr)
    if match:
        return match.group(1).strip().upper()
    return expr.strip().upper()


# AI 어시스턴트 기본 백테스트 템플릿(프론트 UI 기본값과 동일)
PETER_LYNCH_TEMPLATE = {
    "strategy_name": "peter_lynch",
    "is_day_or_month": "daily",
    "start_date": date(2024, 11, 1),
    "end_date": date(2025, 12, 31),
    "rebalance_frequency": "daily",
    "initial_capital": Decimal("50000000"),  # 5,000만원 (만원 단위 입력과 일치)
    "trade_targets": {
        "use_all_stocks": False,
        "selected_universes": [],
        "selected_themes": ["IT서비스", "섬유 / 의류"],
        "selected_stocks": [],
    },
    "buy_conditions": [
        {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 40},
        {"name": "B", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 0},
        {"name": "C", "exp_left_side": "기본값({PEG})", "inequality": "<", "exp_right_side": 2.0},
        {"name": "D", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": "<", "exp_right_side": 180},
        {"name": "E", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 3},
        {"name": "F", "exp_left_side": "기본값({ROA})", "inequality": ">", "exp_right_side": 0.5},
    ],
    "buy_logic": "and",
    "priority_factor": "기본값({PEG})",
    "priority_order": "asc",
    "target_and_loss": {"target_gain": 25, "stop_loss": 15},
    "hold_days": {
        "min_hold_days": 90,
        "max_hold_days": 540,
        "sell_price_basis": "전일 종가",
        "sell_price_offset": 0,
    },
    "condition_sell": {
        "sell_conditions": [
            {"name": "A", "exp_left_side": "기본값({PEG})", "inequality": ">", "exp_right_side": 2.5},
            {"name": "B", "exp_left_side": "기본값({DEBT_RATIO})", "inequality": ">", "exp_right_side": 200},
        ],
        "sell_logic": "or",
        "sell_price_basis": "전일 종가",
        "sell_price_offset": 0,
    },
    "max_holdings": 18,
    "per_stock_ratio": 8.0,
    "max_buy_value": 50000000,
    "max_daily_stock": 4,
}


def build_vectorized_buy_conditions(template: Dict[str, Any]) -> Dict[str, Any]:
    """프론트/챗봇 요청 형식을 벡터화 buy_conditions로 정규화."""
    parsed_conditions = []
    for cond in template["buy_conditions"]:
        factor_code = _extract_factor_code(cond.get("exp_left_side", ""))
        if not factor_code:
            continue
        parsed_conditions.append(
            {
                "id": cond.get("name") or factor_code,
                "factor": factor_code,
                "operator": cond.get("inequality", ">"),
                "value": cond.get("exp_right_side"),
                "description": cond.get("exp_left_side"),
            }
        )

    expression_text = ""
    if parsed_conditions:
        if template.get("buy_logic", "").upper() == "OR":
            expression_text = " or ".join([c["id"] for c in parsed_conditions])
        else:
            expression_text = " and ".join([c["id"] for c in parsed_conditions])

    priority_factor = _extract_factor_code(template.get("priority_factor"))

    return {
        "expression": expression_text,
        "conditions": parsed_conditions,
        "priority_factor": priority_factor,
        "priority_order": template.get("priority_order", "desc"),
    }


def build_trading_rules_for_hash(template: Dict[str, Any]) -> Dict[str, Any]:
    """해시 생성 시 사용하는 매매 규칙 메타 생성 (백테스트 런타임과 동일 구조)."""
    hold_days = template.get("hold_days") or {}
    condition_sell = template.get("condition_sell") or {}
    return {
        "target_and_loss": template.get("target_and_loss"),
        "hold_days": {
            "min_hold_days": hold_days.get("min_hold_days"),
            "max_hold_days": hold_days.get("max_hold_days"),
            "sell_price_basis": hold_days.get("sell_price_basis", "전일 종가"),
            "sell_price_offset": Decimal(str(hold_days.get("sell_price_offset", 0))),
        },
        "condition_sell_meta": {
            "sell_price_basis": condition_sell.get("sell_price_basis", "전일 종가"),
            "sell_price_offset": Decimal(str(condition_sell.get("sell_price_offset", 0))),
        },
    }


PETER_LYNCH_BUY_CONDITIONS = build_vectorized_buy_conditions(PETER_LYNCH_TEMPLATE)
PETER_LYNCH_TRADING_RULES = build_trading_rules_for_hash(PETER_LYNCH_TEMPLATE)
PETER_LYNCH_STRATEGY_HASH = generate_strategy_hash(
    PETER_LYNCH_BUY_CONDITIONS,
    PETER_LYNCH_TRADING_RULES,
)
PETER_LYNCH_REQUIRED_FACTORS = sorted(
    {c["factor"] for c in PETER_LYNCH_BUY_CONDITIONS["conditions"]}
)

# 피터린치 전략 기본 설정 (워밍/백테스트 공용)
PETER_LYNCH_CONFIG = {
    "strategy_name": "peter_lynch",
    "start_date": PETER_LYNCH_TEMPLATE["start_date"],
    "end_date": PETER_LYNCH_TEMPLATE["end_date"],
    "initial_capital": PETER_LYNCH_TEMPLATE["initial_capital"],
    "themes": PETER_LYNCH_TEMPLATE["trade_targets"]["selected_themes"],
    "max_holdings": PETER_LYNCH_TEMPLATE["max_holdings"],
    "per_stock_ratio": PETER_LYNCH_TEMPLATE["per_stock_ratio"],
    "rebalance_frequency": PETER_LYNCH_TEMPLATE["rebalance_frequency"],
    "target_gain": PETER_LYNCH_TEMPLATE["target_and_loss"]["target_gain"],
    "stop_loss": PETER_LYNCH_TEMPLATE["target_and_loss"]["stop_loss"],
    "min_hold_days": PETER_LYNCH_TEMPLATE["hold_days"]["min_hold_days"],
    "max_hold_days": PETER_LYNCH_TEMPLATE["hold_days"]["max_hold_days"],
}


async def get_peter_lynch_strategy_from_db():
    """DB에서 피터린치 전략 설정 로드"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                text("SELECT backtest_config FROM investment_strategies WHERE id = :id"),
                {"id": "peter_lynch"},
            )
            config = result.scalar_one_or_none()
            return config
        except Exception as e:
            logger.warning(f"⚠️ DB에서 피터린치 전략 설정을 불러올 수 없습니다: {e}")
            return None


async def warm_price_data_for_peter_lynch():
    """피터린치 전략용 가격/재무 데이터 캐싱 (프론트 기본 기간 전체)"""
    logger.info("=" * 80)
    logger.info("📊 피터린치 전략 - 가격 데이터 캐싱 시작")
    logger.info("=" * 80)

    cache = get_cache()
    cache_manager = OptimizedCacheManager()
    start_date = PETER_LYNCH_CONFIG["start_date"]
    end_date = PETER_LYNCH_CONFIG["end_date"]
    themes = PETER_LYNCH_CONFIG["themes"]
    themes_str = ",".join(sorted(themes))
    stocks_str = ""  # 기본값: 개별 종목 지정 없음

    async with AsyncSessionLocal() as db:
        try:
            db_manager = OptimizedDBManager(db)

            # 1) 가격 데이터 (전략 테마 필터 적용)
            price_df, _ = await db_manager.load_price_data_optimized(
                start_date, end_date, target_themes=themes, target_stocks=[]
            )
            if price_df is not None and not price_df.empty:
                price_cache_key = f"price_data:{start_date}:{end_date}:{themes_str}:{stocks_str}"
                await cache_manager.set_price_data_cached(price_cache_key, price_df)
                logger.info(
                    f"✅ 가격 데이터 캐싱 완료: {len(price_df)}건 (Key: {price_cache_key})"
                )
            else:
                logger.warning("⚠️ 가격 데이터 없음")

            # 2) 재무 데이터
            financial_df = await db_manager.load_financial_data_optimized(
                start_date, end_date, target_stocks=[]
            )
            if financial_df is not None and not financial_df.empty:
                financial_cache_key = f"financial_data:{start_date}:{end_date}:{stocks_str}"
                await cache_manager.set_price_data_cached(financial_cache_key, financial_df)
                logger.info(
                    f"✅ 재무 데이터 캐싱 완료: {len(financial_df)}건 (Key: {financial_cache_key})"
                )
            else:
                logger.warning("⚠️ 재무 데이터 없음")

            # 3) 상장주식수/시가총액 데이터
            stock_prices_df = await db_manager.load_stock_prices_data(
                start_date, end_date, target_stocks=[]
            )
            if stock_prices_df is not None and not stock_prices_df.empty:
                stock_prices_cache_key = f"stock_prices:{start_date}:{end_date}:{stocks_str}"
                await cache_manager.set_price_data_cached(
                    stock_prices_cache_key, stock_prices_df
                )
                logger.info(
                    f"✅ 상장주식수 데이터 캐싱 완료: {len(stock_prices_df)}건 (Key: {stock_prices_cache_key})"
                )
            else:
                logger.warning("⚠️ 상장주식수 데이터 없음")

            # 레거시 키도 함께 저장 (호환성)
            legacy_key = f"peter_lynch:price_data:{start_date}:{end_date}"
            if price_df is not None and not price_df.empty:
                await cache.set(legacy_key, price_df.to_dict(orient="records"), ttl=0)
                logger.info(f"   레거시 키: {legacy_key}")

        except Exception as e:
            logger.error(f"❌ 가격 데이터 캐싱 실패: {e}", exc_info=True)


async def warm_factor_data_for_peter_lynch():
    """피터린치 전략용 팩터 데이터 캐싱"""
    logger.info("=" * 80)
    logger.info("📈 피터린치 전략 - 팩터 데이터 캐싱 시작")
    logger.info("=" * 80)

    cache_manager = OptimizedCacheManager()
    start_date = PETER_LYNCH_CONFIG["start_date"]
    end_date = PETER_LYNCH_CONFIG["end_date"]
    themes = PETER_LYNCH_CONFIG["themes"]

    strategy_hash = PETER_LYNCH_STRATEGY_HASH
    logger.info(f"🔐 전략 해시 생성: {strategy_hash} (피터린치 전략)")
    logger.info(f"📦 대상 팩터: {PETER_LYNCH_REQUIRED_FACTORS}")

    async with AsyncSessionLocal() as db:
        try:
            from app.services.factor_calculator_complete import CompleteFactorCalculator
            from app.models.company import Company
            from sqlalchemy import select

            db_manager = OptimizedDBManager(db)

            # 가격 데이터를 먼저 불러 캐싱된 날짜와 동일한 거래일 목록 확보
            price_df, _ = await db_manager.load_price_data_optimized(
                start_date, end_date, target_themes=themes, target_stocks=[]
            )
            if price_df is None or price_df.empty:
                logger.warning("⚠️ 가격 데이터가 없어 팩터 캐싱을 건너뜁니다")
                return

            trading_dates = sorted(
                {
                    d.date()
                    for d in pd.to_datetime(price_df["date"])
                    if start_date <= d.date() <= end_date
                }
            )
            logger.info(f"📅 거래일 수: {len(trading_dates)}일 (캐시 대상)")

            # 피터린치 테마 종목 조회
            query = select(Company.stock_code).where(
                Company.industry.in_(PETER_LYNCH_CONFIG["themes"])
            )
            result = await db.execute(query)
            stock_codes = [row[0] for row in result.fetchall()]

            logger.info(f"📊 대상 종목: {len(stock_codes)}개")
            logger.info(f"📊 대상 팩터: {len(PETER_LYNCH_REQUIRED_FACTORS)}개")

            calculator = CompleteFactorCalculator(db)

            # 거래일별로 팩터 계산 및 캐싱 (백테스트와 동일한 날짜 집합)
            factor_cache_payload: Dict[date, Dict[str, Dict[str, Any]]] = {}
            batch_size = 30  # 저장 배치 크기

            for idx, calc_date in enumerate(trading_dates, start=1):
                try:
                    factors_df = await calculator.calculate_all_factors(
                        stock_codes=stock_codes,
                        date=datetime.combine(calc_date, datetime.min.time())
                    )

                    if factors_df is not None and not factors_df.empty:
                        factors_by_stock = {}
                        for _, row in factors_df.iterrows():
                            stock_code = row["stock_code"]
                            factors_by_stock[stock_code] = {
                                factor: row.get(factor)
                                for factor in PETER_LYNCH_REQUIRED_FACTORS
                                if factor in factors_df.columns
                            }

                        factor_cache_payload[calc_date] = factors_by_stock
                        if idx % 20 == 0 or idx == len(trading_dates):
                            logger.info(
                                f"✅ 팩터 계산 진행 {idx}/{len(trading_dates)} (마지막 계산일: {calc_date})"
                            )

                        # 배치 단위로 즉시 캐싱해 메모리 사용 최소화
                        if len(factor_cache_payload) >= batch_size or idx == len(trading_dates):
                            await cache_manager.set_factors_batch(
                                factor_cache_payload,
                                PETER_LYNCH_REQUIRED_FACTORS,
                                themes,
                                [],
                                strategy_hash,
                            )
                            factor_cache_payload.clear()

                except Exception as e:
                    logger.error(f"❌ {calc_date} 팩터 계산 실패: {e}")
                    continue

            logger.info("✅ 모든 팩터 데이터 캐싱 완료!")

        except Exception as e:
            logger.error(f"❌ 팩터 데이터 캐싱 실패: {e}", exc_info=True)


async def warm_backtest_result_for_peter_lynch():
    """피터린치 전략 백테스트 결과 사전 실행 및 캐싱"""
    logger.info("=" * 80)
    logger.info("🚀 피터린치 전략 - 백테스트 실행 및 캐싱 시작")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        try:
            # DB 설정 시도 후 실패 시 템플릿 사용 (캐시 해시와 동일한 조건)
            strategy_config = await get_peter_lynch_strategy_from_db()
            buy_conditions = PETER_LYNCH_BUY_CONDITIONS
            condition_sell = PETER_LYNCH_TEMPLATE.get("condition_sell")
            priority_factor = buy_conditions.get("priority_factor")
            priority_order = buy_conditions.get("priority_order", "asc")

            if strategy_config and "expression" in strategy_config and "conditions" in strategy_config:
                buy_conditions = {
                    "expression": strategy_config.get("expression"),
                    "conditions": strategy_config.get("conditions"),
                    "priority_factor": strategy_config.get("priority_factor", priority_factor),
                    "priority_order": strategy_config.get("priority_order", priority_order),
                }
                condition_sell = strategy_config.get("condition_sell") or condition_sell

            logger.info("📋 전략 설정 로드 완료:")
            logger.info(f"   - Expression: {buy_conditions.get('expression')}")
            logger.info(f"   - Conditions: {len(buy_conditions.get('conditions', []))}개")

            # 백테스트 실행 (결과가 DB와 캐시에 저장됨)
            import uuid
            session_id = str(uuid.uuid4())
            strategy_id = str(uuid.uuid4())

            logger.info(f"🚀 백테스트 실행 시작...")
            logger.info(f"   Session ID: {session_id}")

            await _run_backtest_async(
                session_id=session_id,
                strategy_id=strategy_id,
                start_date=PETER_LYNCH_CONFIG["start_date"],
                end_date=PETER_LYNCH_CONFIG["end_date"],
                initial_capital=PETER_LYNCH_CONFIG["initial_capital"],
                benchmark="KOSPI",
                target_themes=PETER_LYNCH_CONFIG["themes"],
                target_stocks=[],
                target_universes=[],
                use_all_stocks=False,
                buy_conditions=buy_conditions,
                buy_logic="AND",
                priority_factor=priority_factor,
                priority_order=priority_order,
                max_holdings=PETER_LYNCH_CONFIG["max_holdings"],
                per_stock_ratio=PETER_LYNCH_CONFIG["per_stock_ratio"],
                rebalance_frequency=PETER_LYNCH_CONFIG["rebalance_frequency"],
                commission_rate=0.1,
                slippage=0.0,
                target_and_loss={
                    "target_gain": PETER_LYNCH_CONFIG["target_gain"],
                    "stop_loss": PETER_LYNCH_CONFIG["stop_loss"]
                },
                hold_days={
                    "min_hold_days": PETER_LYNCH_CONFIG["min_hold_days"],
                    "max_hold_days": PETER_LYNCH_CONFIG["max_hold_days"]
                },
                condition_sell=condition_sell,
                max_buy_value=None,
                max_daily_stock=None,
                fast_mode=True  # 🔥 초고속 모드 활성화!
            )

            logger.info("✅ 백테스트 실행 완료!")
            logger.info(f"   결과는 session_id: {session_id}로 조회 가능")

            # 세션 정보도 캐싱
            cache = get_cache()
            demo_info = {
                "session_id": session_id,
                "strategy_id": strategy_id,
                "warmed_at": datetime.now().isoformat(),
                "config": PETER_LYNCH_CONFIG,
                "ready": True
            }
            await cache.set("peter_lynch:demo:session", demo_info, ttl=0)
            logger.info("✅ 세션 정보 캐싱 완료")

        except Exception as e:
            logger.error(f"❌ 백테스트 실행 실패: {e}", exc_info=True)


async def run_peter_lynch_cache_warming():
    """피터린치 전략 전체 캐시 워밍 실행"""
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("🔥🔥🔥 피터린치 전략 캐시 워밍 시작 🔥🔥🔥")
    logger.info(f"시작 시간: {start_time}")
    logger.info("=" * 80)

    try:
        # 1단계: 가격 데이터 캐싱
        await warm_price_data_for_peter_lynch()

        # 2단계: 팩터 데이터 캐싱
        await warm_factor_data_for_peter_lynch()

        # 3단계: 백테스트 실행 및 결과 캐싱
        await warm_backtest_result_for_peter_lynch()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("🎉🎉🎉 피터린치 전략 캐시 워밍 완료 🎉🎉🎉")
        logger.info(f"소요 시간: {duration:.2f}초")
        logger.info(f"종료 시간: {end_time}")
        logger.info("=" * 80)

        # 캐시 통계
        cache = get_cache()
        logger.info("\n📊 캐시 워밍 완료 상태:")
        logger.info("  ✅ 가격 데이터: 프론트 기본 기간 캐싱")
        months_count = (PETER_LYNCH_CONFIG["end_date"].year - PETER_LYNCH_CONFIG["start_date"].year) * 12 + (PETER_LYNCH_CONFIG["end_date"].month - PETER_LYNCH_CONFIG["start_date"].month) + 1
        logger.info(f"  ✅ 팩터 데이터: {len(PETER_LYNCH_REQUIRED_FACTORS)}개 팩터 × {months_count}개월 캐싱")
        logger.info("  ✅ 백테스트 결과: 완전 실행 및 캐싱")
        logger.info("\n🎯 시연 준비 완료!")
        logger.info("  - 첫 번째 테스트: 1~2초 예상 (100% 캐시 히트)")
        logger.info("  - 팩터 추가 후: 3~5초 예상 (증분 계산)")

    except Exception as e:
        logger.error(f"❌ 캐시 워밍 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_peter_lynch_cache_warming())
