"""
고도화된 백테스트 엔진 - 실전 퀀트 투자 시뮬레이션
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import create_engine, select, update, text, and_, or_
import polars as pl
import pandas as pd  # 통계 계산시 일부 사용
import numpy as np

from app.models.simulation import (
    SimulationSession,
    SimulationStatistics,
    SimulationDailyValue,
    SimulationTrade,
    SimulationPosition,
    PortfolioStrategy,
    StrategyFactor,
    TradingRule,
    Factor
)
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 동기 엔진 생성
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=False
)


class QuantBacktestEngine:
    """실전 퀀트 투자 백테스트 엔진"""

    def __init__(self, session_id: str, strategy_id: str, target_stocks: List[str] = None):
        logger.info(f"[DEBUG __init__] Received target_stocks parameter: {target_stocks} (type: {type(target_stocks)})")
        self.session_id = session_id
        self.strategy_id = strategy_id
        self.strategy = None
        self.trading_rules = None
        self.factor_settings = None
        self.positions = {}  # {stock_code: Position}
        self.cash = Decimal("0")
        self.portfolio_value = Decimal("0")
        self.previous_portfolio_value = Decimal("0")
        self.initial_capital = Decimal("0")
        self.current_date = None
        # 테마/업종 이름 목록 - 'IT서비스' → 'IT 서비스' 변환
        self.target_stocks = []
        if target_stocks:
            logger.info(f"[DEBUG __init__] target_stocks is truthy, processing {len(target_stocks)} items...")
            for stock in target_stocks:
                # 'IT서비스'를 'IT 서비스'로 변환 (DB에는 공백 있음)
                if stock == 'IT서비스':
                    logger.info(f"[DEBUG __init__] Converting 'IT서비스' -> 'IT 서비스'")
                    self.target_stocks.append('IT 서비스')
                else:
                    logger.info(f"[DEBUG __init__] Keeping stock as is: {stock}")
                    self.target_stocks.append(stock)
        else:
            logger.warning(f"[DEBUG __init__] target_stocks is falsy or empty!")
        logger.info(f"[DEBUG __init__] Final self.target_stocks: {self.target_stocks}")
        self._dividend_table_checked = False
        self._dividend_table_available = False

    def run_backtest(
        self,
        start_date: date,
        end_date: date,
        initial_capital: Decimal,
        benchmark: str = "KOSPI"
    ) -> Dict:
        """백테스트 실행"""

        logger.info(f"고도화된 백테스트 시작: {self.session_id}")

        with Session(sync_engine) as db:
            try:
                # 1. 세션 상태 업데이트: RUNNING
                self._update_session_status(db, "RUNNING", 5)

                # 2. 전략 및 설정 로드
                self._load_strategy_settings(db)
                logger.info(
                    "전략 파라미터 - universe_type=%s, sector_filter=%s, market_cap_filter=%s, target_stocks=%s",
                    getattr(self.strategy, "universe_type", "ALL"),
                    getattr(self.strategy, "sector_filter", None),
                    getattr(self.strategy, "market_cap_filter", None),
                    self.target_stocks or "없음"
                )

                # 3. 초기 자본 설정
                self.cash = initial_capital
                self.portfolio_value = initial_capital
                self.previous_portfolio_value = initial_capital
                self.initial_capital = initial_capital
                logger.info(
                    "초기 자본 %.2f원, 기간 %s ~ %s, 벤치마크 %s",
                    float(self.initial_capital),
                    start_date,
                    end_date,
                    benchmark
                )

                # 4. 거래일 리스트 생성
                trading_days = self._get_trading_days(db, start_date, end_date)
                total_days = len(trading_days)

                if total_days == 0:
                    message = "선택한 기간에 거래일이 없어 백테스트를 종료합니다."
                    logger.warning(message)
                    self._update_session_status(db, "FAILED", error_message=message)
                    db.commit()
                    return {"status": "no_data", "statistics": {}}

                logger.info(f"총 {total_days}개 거래일 시뮬레이션 시작")

                # 5. 일별 시뮬레이션 실행
                daily_results = []

                for day_idx, trading_date in enumerate(trading_days):
                    self.current_date = trading_date
                    logger.debug(
                        "[%s] 거래일 시작 - 보유포지션 %d개, 현금 %.2f원",
                        trading_date,
                        len(self.positions),
                        float(self.cash)
                    )

                    # 진행률 업데이트
                    progress = int((day_idx / total_days) * 90) + 5
                    self._update_session_status(db, "RUNNING", progress)

                    # 일별 처리
                    daily_result = self._process_trading_day(db, trading_date)
                    daily_results.append(daily_result)
                    logger.debug(
                        "[%s] 일별 결과 - 포트 가치 %.2f, 현금 %.2f, 보유가치 %.2f, 일간수익률 %.4f%%",
                        trading_date,
                        float(daily_result["portfolio_value"]),
                        float(daily_result["cash"]),
                        float(daily_result["position_value"]),
                        float(daily_result.get("daily_return", 0))
                    )

                    # 일별 가치 저장
                    try:
                        self._save_daily_value(db, trading_date, daily_result)
                        db.commit()  # 일별 저장 후 즉시 커밋
                    except Exception as e:
                        logger.error(f"일별 가치 저장 중 오류 ({trading_date}): {e}")
                        db.rollback()

                    # 주기별 리밸런싱 체크
                    if self._should_rebalance(trading_date):
                        logger.info("[%s] 리밸런싱 조건 충족 → 포트 재구성 시도", trading_date)
                        try:
                            self._rebalance_portfolio(db, trading_date)
                            db.commit()  # 리밸런싱 후 즉시 커밋
                        except Exception as e:
                            logger.error(f"리밸런싱 중 오류 발생 ({trading_date}): {e}")
                            db.rollback()  # 에러 발생 시 롤백
                            # 계속 진행 (리밸런싱 실패해도 백테스트는 계속)

                    # 중간 커밋 (100일마다)
                    if day_idx % 100 == 0:
                        logger.info(f"진행 상황: {day_idx}/{total_days} 일 완료")

                # 6. 최종 통계 계산 및 저장
                statistics = self._calculate_statistics(daily_results)
                self._save_statistics(db, statistics)

                # 7. 세션 완료
                self._update_session_status(db, "COMPLETED", 100)
                db.commit()

                logger.info(f"백테스트 완료: 최종 수익률 {statistics['total_return']:.2f}%")
                return {"status": "success", "statistics": statistics}

            except Exception as e:
                logger.error(f"백테스트 실행 중 오류: {e}")
                self._update_session_status(db, "FAILED", error_message=str(e))
                db.commit()
                raise

    def _load_strategy_settings(self, db: Session):
        """전략 설정 로드"""

        # 전략 정보 로드
        self.strategy = db.execute(
            select(PortfolioStrategy).where(
                PortfolioStrategy.strategy_id == self.strategy_id
            )
        ).scalar_one()

        # 매매 규칙 로드
        self.trading_rules = db.execute(
            select(TradingRule).where(
                TradingRule.strategy_id == self.strategy_id
            )
        ).scalars().all()

        # 팩터 설정 로드 (factor relationship을 eager load)
        factor_settings_raw = db.execute(
            select(StrategyFactor)
            .options(selectinload(StrategyFactor.factor))
            .where(StrategyFactor.strategy_id == self.strategy_id)
        ).scalars().all()

        # 모든 속성을 미리 로드하여 dict로 변환 (lazy loading 방지)
        self.factor_settings = []
        for fs in factor_settings_raw:
            factor_dict = {
                'factor_id': fs.factor_id,
                'usage_type': fs.usage_type,
                'weight': fs.weight,
                'direction': fs.direction,
                'operator': fs.operator,
                'threshold_value': fs.threshold_value,
                'factor': fs.factor  # eager loaded
            }
            self.factor_settings.append(factor_dict)

        logger.info(f"전략 '{self.strategy.strategy_name}' 로드 완료")
        logger.info(f"- 매매 규칙: {len(self.trading_rules)}개")
        logger.info(f"- 팩터 설정: {len(self.factor_settings)}개")
        if self.factor_settings:
            logger.debug(
                "팩터 목록: %s",
                ", ".join(fs["factor_id"] for fs in self.factor_settings)
            )

    def _get_trading_days(self, db: Session, start_date: date, end_date: date) -> List[date]:
        """거래일 리스트 조회"""

        result = db.execute(
            text("""
                SELECT DISTINCT trade_date
                FROM stock_prices
                WHERE trade_date BETWEEN :start_date AND :end_date
                ORDER BY trade_date
            """),
            {"start_date": start_date, "end_date": end_date}
        ).fetchall()

        return [row[0] for row in result]

    def _get_universe_stocks(self, db: Session, trading_date: date) -> List[Dict]:
        """유니버스 종목 조회 (전략 설정에 따른 필터링)"""

        logger.debug(
            "유니버스 조회 시작 - date=%s, universe_type=%s, sector_filter=%s, market_cap_filter=%s, target_stocks=%s",
            trading_date,
            getattr(self.strategy, "universe_type", "ALL"),
            getattr(self.strategy, "sector_filter", None),
            getattr(self.strategy, "market_cap_filter", None),
            self.target_stocks or "없음"
        )

        query = """
            SELECT DISTINCT c.company_id, c.stock_code, c.company_name,
                   c.market_type, c.industry, sp.market_cap
            FROM companies c
            INNER JOIN stock_prices sp ON c.company_id = sp.company_id
            WHERE c.is_active = 1
              AND sp.trade_date = :trade_date
        """

        params = {"trade_date": trading_date}

        # 시장 필터 (THEME은 테마/업종 기반이므로 market_type 필터 제외)
        if self.strategy.universe_type and self.strategy.universe_type not in ["ALL", "THEME"]:
            query += " AND c.market_type = :market_type"
            params["market_type"] = self.strategy.universe_type
            logger.info(f"[DEBUG] market_type 필터 적용: {self.strategy.universe_type}")

        # 업종 필터
        if self.strategy.sector_filter:
            sectors = self.strategy.sector_filter
            if isinstance(sectors, list) and sectors:
                sector_list = ",".join([f"'{s}'" for s in sectors])
                query += f" AND c.industry IN ({sector_list})"

        # 시가총액 필터
        if self.strategy.market_cap_filter and self.strategy.market_cap_filter != "ALL":
            if self.strategy.market_cap_filter == "LARGE":
                query += " AND sp.market_cap >= 10000000000000"  # 10조 이상
            elif self.strategy.market_cap_filter == "MID":
                query += " AND sp.market_cap BETWEEN 1000000000000 AND 10000000000000"  # 1조~10조
            elif self.strategy.market_cap_filter == "SMALL":
                query += " AND sp.market_cap < 1000000000000"  # 1조 미만

        # 테마/업종 필터 (target_stocks)
        logger.info(f"[DEBUG _get_universe_stocks] Checking self.target_stocks: {self.target_stocks} (type: {type(self.target_stocks)})")
        if self.target_stocks:
            industries = self.target_stocks
            logger.info(f"[DEBUG _get_universe_stocks] self.target_stocks is truthy!")
            if isinstance(industries, list) and industries:
                industry_list = ",".join([f"'{ind}'" for ind in industries])
                query += f" AND c.industry IN ({industry_list})"
                logger.info(f"[DEBUG _get_universe_stocks] Added industry filter to query: AND c.industry IN ({industry_list})")
                logger.info("테마/업종 필터 적용: %s", industries)
            else:
                logger.warning(f"[DEBUG _get_universe_stocks] industries is not a list or is empty: {industries}")
        else:
            logger.warning(f"[DEBUG _get_universe_stocks] self.target_stocks is falsy!")

        logger.info(f"[DEBUG _get_universe_stocks] Final SQL query: {query}")
        logger.info(f"[DEBUG _get_universe_stocks] Query params: {params}")
        result = db.execute(text(query), params).fetchall()
        stock_count = len(result)
        preview = ", ".join(row[1] for row in result[:5])
        logger.info(
            "유니버스 종목 %d개 조회 완료 (샘플: %s%s)",
            stock_count,
            preview,
            "..." if stock_count > 5 else ""
        )

        return [
            {
                "company_id": row[0],
                "stock_code": row[1],
                "company_name": row[2],
                "market_type": row[3],
                "industry": row[4],
                "market_cap": row[5]
            }
            for row in result
        ]

    def _calculate_factor_scores(self, db: Session, stocks: List[Dict], trading_date: date) -> pl.DataFrame:
        """팩터 점수 계산 - Polars를 사용한 최적화"""

        stock_codes = [s["stock_code"] for s in stocks]
        stock_data = {
            "stock_code": stock_codes,
            "market_cap": [s.get("market_cap", 0) for s in stocks]
        }

        logger.debug(
            "팩터 점수 계산 시작 - date=%s, 종목수=%d, 팩터수=%d",
            trading_date,
            len(stock_codes),
            len(self.factor_settings)
        )

        # Polars DataFrame 생성
        factor_scores = pl.DataFrame(stock_data)

        for factor_setting in self.factor_settings:
            factor = db.execute(
                select(Factor).where(
                    Factor.factor_id == factor_setting["factor_id"]
                )
            ).scalar_one()

            # 팩터 유형별 계산
            if factor.calculation_type == "FUNDAMENTAL":
                scores = self._calculate_fundamental_factor(
                    db, stock_codes, trading_date, factor, factor_setting
                )
            elif factor.calculation_type == "TECHNICAL":
                scores = self._calculate_technical_factor(
                    db, stock_codes, trading_date, factor, factor_setting
                )
            else:
                scores = self._calculate_custom_factor(
                    db, stock_codes, trading_date, factor, factor_setting
                )

            # 팩터 점수 추가
            factor_scores = factor_scores.with_columns(
                pl.Series(name=factor.factor_id, values=scores)
            )

        # 종합 점수 계산 (가중 평균)
        if len(self.factor_settings) > 0:
            # 가중치를 적용할 컬럼들 준비
            weighted_cols = []

            for factor_setting in self.factor_settings:
                if factor_setting["usage_type"] == "SCORING":
                    weight = float(factor_setting["weight"] or 1.0)
                    factor_col = factor_setting["factor_id"]

                    if factor_col in factor_scores.columns:
                        # 방향성 적용
                        if factor_setting["direction"] == "NEGATIVE":
                            factor_scores = factor_scores.with_columns(
                                (pl.col(factor_col) * -1).alias(factor_col)
                            )

                        # 가중치 적용
                        weighted_col_name = f"{factor_col}_weighted"
                        factor_scores = factor_scores.with_columns(
                            (pl.col(factor_col) * weight).alias(weighted_col_name)
                        )
                        weighted_cols.append(weighted_col_name)

            # 종합 점수 계산
            if weighted_cols:
                factor_scores = factor_scores.with_columns(
                    sum([pl.col(col) for col in weighted_cols]).alias("total_score_raw")
                )

                # 가중치 합계로 나누기
                total_weight = sum(
                    float(fs.weight or 1.0)
                    for fs in self.factor_settings
                    if fs.usage_type == "SCORING" and fs.factor_id in factor_scores.columns
                )

                if total_weight > 0:
                    factor_scores = factor_scores.with_columns(
                        (pl.col("total_score_raw") / total_weight).alias("total_score")
                    ).drop("total_score_raw")
                else:
                    factor_scores = factor_scores.with_columns(
                        pl.lit(0).alias("total_score")
                    )

                # 임시 가중치 컬럼 제거
                factor_scores = factor_scores.drop(weighted_cols)
            else:
                factor_scores = factor_scores.with_columns(
                    pl.lit(0).alias("total_score")
                )
        else:
            factor_scores = factor_scores.with_columns(
                pl.lit(0).alias("total_score")
            )

        logger.debug(
            "팩터 점수 계산 완료 - 컬럼: %s",
            factor_scores.columns
        )
        return factor_scores

    def _calculate_fundamental_factor(
        self, db: Session, stock_codes: List[str], trading_date: date,
        factor: Factor, setting: StrategyFactor
    ) -> List[float]:
        """재무 팩터 계산"""

        logger.debug(
            "재무 팩터 계산 - factor=%s, 종목수=%d, date=%s",
            factor.factor_id,
            len(stock_codes),
            trading_date
        )

        scores = []

        for stock_code in stock_codes:
            # 예시: PER, PBR, ROE 등의 계산
            if factor.factor_id == "PER":
                score = self._get_per(db, stock_code, trading_date)
            elif factor.factor_id == "PBR":
                score = self._get_pbr(db, stock_code, trading_date)
            elif factor.factor_id == "ROE":
                score = self._get_roe(db, stock_code, trading_date)
            elif factor.factor_id == "DIV_YIELD":
                score = self._get_dividend_yield(db, stock_code, trading_date)
            else:
                score = 0

            scores.append(score)

        # 정규화 (Z-score)
        scores = np.array(scores)
        if scores.std() > 0:
            scores = (scores - scores.mean()) / scores.std()

        return scores.tolist()

    def _calculate_technical_factor(
        self, db: Session, stock_codes: List[str], trading_date: date,
        factor: Factor, setting: StrategyFactor
    ) -> List[float]:
        """기술적 팩터 계산"""

        logger.debug(
            "기술적 팩터 계산 - factor=%s, 종목수=%d, date=%s",
            factor.factor_id,
            len(stock_codes),
            trading_date
        )

        scores = []

        for stock_code in stock_codes:
            # 예시: 모멘텀, 변동성 등
            if factor.factor_id == "MOMENTUM_1M":
                score = self._get_momentum(db, stock_code, trading_date, 20)
            elif factor.factor_id == "MOMENTUM_3M":
                score = self._get_momentum(db, stock_code, trading_date, 60)
            elif factor.factor_id == "VOLATILITY":
                score = self._get_volatility(db, stock_code, trading_date, 20)
            else:
                score = 0

            scores.append(score)

        # 정규화
        scores = np.array(scores)
        if scores.std() > 0:
            scores = (scores - scores.mean()) / scores.std()

        return scores.tolist()

    def _select_stocks_by_factors(self, factor_scores: pl.DataFrame) -> List[str]:
        """팩터 점수 기반 종목 선택 - Polars 최적화"""

        # 스크리닝 적용
        screened = factor_scores
        logger.debug(
            "팩터 스크리닝 시작 - 입력 종목수=%d, 컬럼=%s",
            screened.height,
            screened.columns
        )

        for factor_setting in self.factor_settings:
            if factor_setting["usage_type"] == "SCREENING":
                factor_col = factor_setting["factor_id"]

                if factor_col in screened.columns:
                    if factor_setting["operator"] == "GT":
                        threshold = float(factor_setting["threshold_value"])
                        screened = screened.filter(pl.col(factor_col) > threshold)
                    elif factor_setting["operator"] == "LT":
                        threshold = float(factor_setting["threshold_value"])
                        screened = screened.filter(pl.col(factor_col) < threshold)
                    elif factor_setting["operator"] == "BETWEEN":
                        # 범위 필터링 (예: 10 < factor < 50)
                        values = factor_setting["threshold_value"].split(",")
                        if len(values) == 2:
                            lower = float(values[0])
                            upper = float(values[1])
                            screened = screened.filter(
                                (pl.col(factor_col) > lower) & (pl.col(factor_col) < upper)
                            )
                        else:
                            logger.warning(
                                "SCREENING 임계값 형식이 잘못되었습니다 (factor=%s, value=%s)",
                                factor_col,
                                factor_setting["threshold_value"]
                            )

        logger.debug(
            "스크리닝 후 종목수=%d",
            screened.height
        )

        # 랭킹 적용
        if "total_score" in screened.columns:
            screened = screened.sort("total_score", descending=True)
        else:
            logger.warning("total_score 컬럼이 없어 랭킹을 건너뜁니다.")

        # 최대 보유 종목 수 제한
        max_positions = 20  # 기본값
        for rule in self.trading_rules:
            if rule.max_positions:
                max_positions = rule.max_positions
                break

        selected = screened.head(max_positions)["stock_code"].to_list()

        logger.info(
            "팩터 기반 종목 선택 완료 - 최종 %d개 (최대 %d개, 상위 종목: %s%s)",
            len(selected),
            max_positions,
            ", ".join(selected[:5]),
            "..." if len(selected) > 5 else ""
        )
        return selected

    def _process_trading_day(self, db: Session, trading_date: date) -> Dict:
        """일별 거래 처리"""

        # 1. 현재 포지션 가치 평가
        self._update_position_values(db, trading_date)

        # 2. 손절/익절 체크
        self._check_stop_conditions(db, trading_date)

        # 3. 포트폴리오 가치 계산
        position_value = sum(pos["value"] for pos in self.positions.values())
        self.portfolio_value = self.cash + position_value

        # 4. 일별 수익률 계산
        daily_return = Decimal("0")
        cumulative_return = Decimal("0")

        if self.previous_portfolio_value > 0:
            daily_return = ((self.portfolio_value - self.previous_portfolio_value) /
                          self.previous_portfolio_value) * 100

        if self.initial_capital > 0:
            cumulative_return = ((self.portfolio_value - self.initial_capital) /
                               self.initial_capital) * 100

        # 현재 포트폴리오 가치를 이전 가치로 저장
        self.previous_portfolio_value = self.portfolio_value

        return {
            "date": trading_date,
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "position_value": position_value,
            "positions": len(self.positions),
            "daily_return": daily_return,
            "cumulative_return": cumulative_return
        }

    def _rebalance_portfolio(self, db: Session, trading_date: date):
        """포트폴리오 리밸런싱"""

        logger.info(f"[{trading_date}] 포트폴리오 리밸런싱 시작")

        # 1. 유니버스 종목 조회
        universe_stocks = self._get_universe_stocks(db, trading_date)

        if not universe_stocks:
            logger.warning(f"[{trading_date}] 유니버스에 종목이 없음")
            return

        logger.info(f"[{trading_date}] 유니버스 종목 수: {len(universe_stocks)}")

        # 2. 팩터 점수 계산
        logger.info(f"[{trading_date}] 팩터 점수 계산 시작 - 종목 수: {len(universe_stocks)}")
        factor_scores = self._calculate_factor_scores(db, universe_stocks, trading_date)

        if factor_scores is not None and factor_scores.height > 0:
            logger.debug(
                "[%s] 팩터 점수 샘플 (상위 5개):\n%s",
                trading_date,
                factor_scores.head(5)
            )

        # 3. 종목 선택
        selected_stocks = self._select_stocks_by_factors(factor_scores)

        if not selected_stocks:
            logger.warning(f"[{trading_date}] 선택된 종목이 없어 리밸런싱을 중단합니다.")
            return

        logger.info(
            f"[{trading_date}] 선택된 종목 수: {len(selected_stocks)}, "
            f"종목: {selected_stocks[:10]}"
        )

        # 4. 기존 포지션 정리 (선택되지 않은 종목 매도)
        current_stocks = list(self.positions.keys())

        if current_stocks:
            logger.info(f"[{trading_date}] [DEBUG] 기존 포지션 정리 시작: {len(current_stocks)}개")

        for stock_code in current_stocks:
            if stock_code not in selected_stocks:
                logger.info(f"[{trading_date}] 매도 대상: {stock_code} (선택 종목에서 제외됨)")
                try:
                    self._sell_position(db, stock_code, trading_date)
                except Exception as e:
                    logger.error(f"[{trading_date}] 매도 실패 ({stock_code}): {e}")
                    # rollback하지 않고 continue - 다른 종목 매도는 계속 진행
                    continue

        # 5. 포지션 사이징 방법 결정
        sizing_method = "EQUAL_WEIGHT"
        for rule in self.trading_rules:
            if rule.position_sizing:
                sizing_method = rule.position_sizing
                break

        # 6. 포지션 크기 계산
        if sizing_method in ["MARKET_CAP", "RISK_PARITY"]:
            position_sizes = self._calculate_weighted_position_sizes(
                db, selected_stocks, trading_date, sizing_method
            )
        else:
            position_size = self._calculate_position_size(len(selected_stocks))
            position_sizes = {stock: position_size for stock in selected_stocks}

        # 7. 새로운 포지션 구축
        for stock_code in selected_stocks:
            target_value = position_sizes.get(stock_code, Decimal("0"))
            if stock_code not in self.positions:
                try:
                    self._buy_position(db, stock_code, target_value, trading_date)
                except Exception as e:
                    logger.error(f"[{trading_date}] 매수 실패 ({stock_code}): {e}")
                    # rollback하지 않고 continue - 다른 종목 매수는 계속 진행
                    continue
            else:
                # 기존 포지션 조정
                try:
                    self._adjust_position(db, stock_code, target_value, trading_date)
                except Exception as e:
                    logger.error(f"[{trading_date}] 포지션 조정 실패 ({stock_code}): {e}")
                    # rollback하지 않고 continue - 다른 종목 조정은 계속 진행
                    continue

    def _buy_position(self, db: Session, stock_code: str, target_value: Decimal, trading_date: date):
        """매수 포지션 생성"""

        logger.debug(
            "[%s] 매수 시도 - %s, 목표금액 %.2f, 현재현금 %.2f",
            trading_date,
            stock_code,
            float(target_value),
            float(self.cash)
        )
        # 현재가 조회
        try:
            price_data = db.execute(
                text("""
                    SELECT sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()
        except Exception as e:
            logger.error(
                "_buy_position 가격 조회 실패 (종목: %s, 날짜: %s): %s",
                stock_code,
                trading_date,
                str(e)
            )
            raise

        if not price_data:
            logger.warning("[%s] 매수가격을 찾을 수 없어 주문을 건너뜁니다: %s", trading_date, stock_code)
            return

        price = Decimal(str(price_data[0]))
        quantity = int(target_value / price)

        if quantity <= 0:
            logger.debug("[%s] 목표 금액이 부족하여 매수를 건너뜀: %s", trading_date, stock_code)
            return

        # 매수 비용 계산
        commission_rate = Decimal("0.00015")  # 0.015%
        amount = price * quantity
        commission = amount * commission_rate
        total_cost = amount + commission

        if total_cost > self.cash:
            # 자금 부족 시 수량 조정
            quantity = int((self.cash * Decimal("0.99")) / price)
            if quantity <= 0:
                return
            amount = price * quantity
            commission = amount * commission_rate
            total_cost = amount + commission

        # 포지션 추가
        self.positions[stock_code] = {
            "quantity": quantity,
            "avg_price": price,
            "value": amount,
            "entry_date": trading_date
        }

        # 현금 차감
        self.cash -= total_cost

        # 거래 기록 저장
        trade = SimulationTrade(
            session_id=self.session_id,
            stock_code=stock_code,
            trade_type="BUY",
            trade_date=trading_date,
            price=price,
            quantity=quantity,
            amount=amount,
            commission=commission
        )
        db.add(trade)

        logger.info(
            "[%s] 매수: %s %d주 @ %.2f원 (총비용 %.2f원, 수수료 %.2f원)",
            trading_date,
            stock_code,
            quantity,
            float(price),
            float(total_cost),
            float(commission)
        )

    def _sell_position(self, db: Session, stock_code: str, trading_date: date):
        """매도 포지션 처리"""

        if stock_code not in self.positions:
            return

        position = self.positions[stock_code]

        # 현재가 조회
        price_data = db.execute(
            text("""
                SELECT sp.close_price
                FROM stock_prices sp
                INNER JOIN companies c ON sp.company_id = c.company_id
                WHERE c.stock_code = :stock_code AND sp.trade_date = :trade_date
            """),
            {"stock_code": stock_code, "trade_date": trading_date}
        ).fetchone()

        if not price_data:
            logger.warning("[%s] 매도가격을 찾을 수 없어 건너뜀: %s", trading_date, stock_code)
            return

        price = Decimal(str(price_data[0]))
        quantity = position["quantity"]

        # 매도 수익 계산
        amount = price * quantity
        commission_rate = Decimal("0.00015")
        tax_rate = Decimal("0.0023")

        commission = amount * commission_rate
        tax = amount * tax_rate
        net_amount = amount - commission - tax

        # 실현 손익 계산
        cost_basis = position["avg_price"] * quantity
        realized_pnl = net_amount - cost_basis
        return_pct = (realized_pnl / cost_basis) * 100 if cost_basis > 0 else 0

        # 현금 추가
        self.cash += net_amount

        # 포지션 제거
        del self.positions[stock_code]

        # 거래 기록 저장
        trade = SimulationTrade(
            session_id=self.session_id,
            stock_code=stock_code,
            trade_type="SELL",
            trade_date=trading_date,
            price=price,
            quantity=quantity,
            amount=amount,
            commission=commission,
            tax=tax,
            realized_pnl=realized_pnl,
            return_pct=return_pct
        )
        db.add(trade)

        logger.info(
            "[%s] 매도: %s %d주 @ %.2f원 (손익: %.0f원, 수익률: %.2f%%)",
            trading_date,
            stock_code,
            quantity,
            float(price),
            float(realized_pnl),
            float(return_pct)
        )

    def _update_position_values(self, db: Session, trading_date: date):
        """포지션 가치 업데이트"""

        updated_count = 0
        for stock_code, position in self.positions.items():
            price_data = db.execute(
                text("""
                    SELECT sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if price_data:
                current_price = Decimal(str(price_data[0]))
                position["value"] = current_price * position["quantity"]
                updated_count += 1
            else:
                logger.debug(
                    "[%s] 포지션 평가용 가격 없음: %s",
                    trading_date,
                    stock_code
                )

        if self.positions:
            logger.debug(
                "[%s] 포지션 가치 업데이트 완료 - 총 %d개 중 %d개 갱신",
                trading_date,
                len(self.positions),
                updated_count
            )

    def _check_stop_conditions(self, db: Session, trading_date: date):
        """손절/익절 조건 체크"""

        for rule in self.trading_rules:
            if not rule.stop_loss_pct and not rule.take_profit_pct:
                continue

            positions_to_sell = []

            for stock_code, position in self.positions.items():
                # 현재가 조회
                price_data = db.execute(
                    text("""
                        SELECT sp.close_price
                        FROM stock_prices sp
                        INNER JOIN companies c ON sp.company_id = c.company_id
                        WHERE c.stock_code = :stock_code AND sp.trade_date = :trade_date
                    """),
                    {"stock_code": stock_code, "trade_date": trading_date}
                ).fetchone()

                if not price_data:
                    continue

                current_price = Decimal(str(price_data[0]))
                avg_price = position["avg_price"]
                return_pct = ((current_price - avg_price) / avg_price) * 100

                # 손절 체크
                if rule.stop_loss_pct and return_pct <= -rule.stop_loss_pct:
                    positions_to_sell.append(stock_code)
                    logger.info(f"손절: {stock_code} (수익률: {return_pct:.2f}%)")

                # 익절 체크
                elif rule.take_profit_pct and return_pct >= rule.take_profit_pct:
                    positions_to_sell.append(stock_code)
                    logger.info(f"익절: {stock_code} (수익률: {return_pct:.2f}%)")

            # 매도 실행
            for stock_code in positions_to_sell:
                try:
                    self._sell_position(db, stock_code, trading_date)
                except Exception as e:
                    logger.error(f"손절/익절 매도 실패 ({stock_code}): {e}")
                    db.rollback()
                    continue

    def _should_rebalance(self, trading_date: date) -> bool:
        """리밸런싱 필요 여부 확인"""

        for rule in self.trading_rules:
            logger.debug(
                "[%s] 리밸런싱 조건 체크 - frequency=%s, day=%d, weekday=%d, month=%d",
                trading_date,
                rule.rebalance_frequency,
                trading_date.day,
                trading_date.weekday(),
                trading_date.month
            )

            if rule.rebalance_frequency == "DAILY":
                # 매일 리밸런싱
                logger.info("[%s] 리밸런싱 조건 충족: DAILY (매일)", trading_date)
                return True
            elif rule.rebalance_frequency == "MONTHLY":
                # 매월 첫 거래일
                if trading_date.day <= 7:  # 대략적인 첫 주
                    logger.info("[%s] 리밸런싱 조건 충족: MONTHLY (day <= 7)", trading_date)
                    return True
            elif rule.rebalance_frequency == "QUARTERLY":
                # 분기별 첫 거래일
                if trading_date.month in [1, 4, 7, 10] and trading_date.day <= 7:
                    logger.info("[%s] 리밸런싱 조건 충족: QUARTERLY", trading_date)
                    return True
            elif rule.rebalance_frequency == "WEEKLY":
                # 매주 월요일
                if trading_date.weekday() == 0:
                    logger.info("[%s] 리밸런싱 조건 충족: WEEKLY (월요일)", trading_date)
                    return True

        logger.debug("[%s] 리밸런싱 조건 미충족", trading_date)
        return False

    def _calculate_position_size(self, num_positions: int) -> Decimal:
        """포지션 크기 계산"""

        if num_positions == 0:
            logger.warning("포지션 사이징 요청이 왔지만 선택된 종목이 없습니다.")
            return Decimal("0")

        logger.debug(
            "포지션 사이즈 계산 - num_positions=%d, portfolio_value=%.2f",
            num_positions,
            float(self.portfolio_value)
        )

        # 포지션 사이징 방법
        for rule in self.trading_rules:
            if rule.position_sizing == "EQUAL_WEIGHT":
                # 동일 가중
                return self.portfolio_value / num_positions
            elif rule.position_sizing == "MARKET_CAP":
                # 시가총액 가중 (개별 종목별로 계산 필요)
                # 이 메서드는 기본 사이즈만 반환, 실제 가중치는 리밸런싱에서 처리
                return self.portfolio_value / num_positions
            elif rule.position_sizing == "RISK_PARITY":
                # 리스크 패리티 (개별 종목별로 계산 필요)
                # 이 메서드는 기본 사이즈만 반환, 실제 가중치는 리밸런싱에서 처리
                return self.portfolio_value / num_positions

        # 기본값: 동일 가중
        return self.portfolio_value / num_positions

    def _calculate_weighted_position_sizes(
        self, db: Session, stock_codes: List[str], trading_date: date, method: str
    ) -> Dict[str, Decimal]:
        """가중치 기반 포지션 크기 계산"""

        logger.debug(
            "[%s] 가중치 포지션 계산 - method=%s, 종목수=%d",
            trading_date,
            method,
            len(stock_codes)
        )
        position_sizes = {}

        if method == "MARKET_CAP":
            # 시가총액 가중
            market_caps = {}
            total_market_cap = Decimal("0")

            for stock_code in stock_codes:
                result = db.execute(
                    text("""
                        SELECT sp.market_cap
                        FROM stock_prices sp
                        INNER JOIN companies c ON sp.company_id = c.company_id
                        WHERE c.stock_code = :stock_code
                          AND sp.trade_date = :trade_date
                    """),
                    {"stock_code": stock_code, "trade_date": trading_date}
                ).fetchone()

                if result and result[0]:
                    market_cap = Decimal(str(result[0]))
                    market_caps[stock_code] = market_cap
                    total_market_cap += market_cap

            # 시가총액 비중으로 자금 배분
            if total_market_cap > 0:
                for stock_code, market_cap in market_caps.items():
                    weight = market_cap / total_market_cap
                    position_sizes[stock_code] = self.portfolio_value * weight

        elif method == "RISK_PARITY":
            # 리스크 패리티 - 각 종목의 변동성에 반비례하여 가중
            volatilities = {}
            total_inv_vol = Decimal("0")

            for stock_code in stock_codes:
                vol = self._get_volatility(db, stock_code, trading_date, 60)
                if vol > 0:
                    volatilities[stock_code] = Decimal(str(vol))
                    total_inv_vol += Decimal("1") / Decimal(str(vol))

            # 변동성의 역수 비중으로 자금 배분
            if total_inv_vol > 0:
                for stock_code, vol in volatilities.items():
                    inv_vol_weight = (Decimal("1") / vol) / total_inv_vol
                    position_sizes[stock_code] = self.portfolio_value * inv_vol_weight

        else:
            # 동일 가중 (기본값)
            equal_size = self.portfolio_value / len(stock_codes)
            for stock_code in stock_codes:
                position_sizes[stock_code] = equal_size

        logger.debug(
            "[%s] 포지션 크기 결과: %s",
            trading_date,
            {k: float(v) for k, v in list(position_sizes.items())[:5]}
        )
        return position_sizes

    def _adjust_position(self, db: Session, stock_code: str, target_value: Decimal, trading_date: date):
        """포지션 크기 조정"""

        current_position = self.positions.get(stock_code)
        if not current_position:
            return

        current_value = current_position["value"]
        diff = target_value - current_value

        # 조정이 필요한 경우 (10% 이상 차이)
        if abs(diff) > current_value * Decimal("0.1"):
            if diff > 0:
                # 추가 매수
                self._buy_position(db, stock_code, diff, trading_date)
            else:
                # 부분 매도
                # TODO: 부분 매도 로직 구현
                pass

    def _save_daily_value(self, db: Session, trading_date: date, daily_result: Dict):
        """일별 포트폴리오 가치 저장"""

        daily_value = SimulationDailyValue(
            session_id=self.session_id,
            date=trading_date,
            portfolio_value=daily_result["portfolio_value"],
            cash=daily_result["cash"],
            position_value=daily_result["position_value"],
            daily_return=daily_result.get("daily_return", Decimal("0")),
            cumulative_return=daily_result.get("cumulative_return", Decimal("0"))
        )
        db.add(daily_value)
        logger.debug(
            "[%s] 일별 가치 저장 - 포트 %.2f, 현금 %.2f, 포지션 %.2f",
            trading_date,
            float(daily_result["portfolio_value"]),
            float(daily_result["cash"]),
            float(daily_result["position_value"])
        )

    def _calculate_statistics(self, daily_results: List[Dict]) -> Dict:
        """백테스트 통계 계산"""

        if not daily_results:
            logger.warning("일별 결과가 비어 있어 통계를 계산할 수 없습니다.")
            return {}

        # DataFrame 변환 - 모든 Decimal을 float로 변환
        df = pd.DataFrame(daily_results)

        # Decimal 타입을 float로 변환
        for col in df.columns:
            if col in ['portfolio_value', 'cash', 'position_value', 'daily_return', 'cumulative_return']:
                df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)

        df.set_index("date", inplace=True)

        # 수익률 계산 - float로 변환하여 연산
        initial_value = float(daily_results[0]["portfolio_value"])
        final_value = float(daily_results[-1]["portfolio_value"])
        total_return = ((final_value - initial_value) / initial_value) * 100

        # 일별 수익률
        df["daily_return"] = df["portfolio_value"].pct_change()

        # 변동성 (연환산)
        volatility = df["daily_return"].std() * np.sqrt(252) * 100

        # 최대 낙폭 (MDD)
        cummax = df["portfolio_value"].cummax()
        drawdown = (df["portfolio_value"] - cummax) / cummax
        max_drawdown = drawdown.min() * 100

        # 샤프 비율 (무위험 수익률 2% 가정)
        risk_free_rate = 0.02 / 252
        excess_returns = df["daily_return"] - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / df["daily_return"].std()) * np.sqrt(252) if df["daily_return"].std() > 0 else 0

        stats = {
            "total_return": float(total_return),
            "volatility": float(volatility),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio),
            "final_capital": float(final_value)
        }
        logger.info(
            "통계 계산 완료 - 수익률 %.2f%%, 변동성 %.2f%%, MDD %.2f%%, 샤프 %.2f",
            stats["total_return"],
            stats["volatility"],
            stats["max_drawdown"],
            stats["sharpe_ratio"]
        )
        return stats

    def _save_statistics(self, db: Session, statistics: Dict):
        """통계 저장"""

        stat = SimulationStatistics(
            session_id=self.session_id,
            total_return=Decimal(str(statistics.get("total_return", 0))),
            volatility=Decimal(str(statistics.get("volatility", 0))),
            max_drawdown=Decimal(str(statistics.get("max_drawdown", 0))),
            sharpe_ratio=Decimal(str(statistics.get("sharpe_ratio", 0))),
            final_capital=Decimal(str(statistics.get("final_capital", 0)))
        )
        db.add(stat)

    def _update_session_status(
        self, db: Session, status: str, progress: int = None, error_message: str = None
    ):
        """세션 상태 업데이트"""

        update_values = {"status": status}

        if progress is not None:
            update_values["progress"] = progress

        if error_message:
            update_values["error_message"] = error_message

        if status == "RUNNING" and "started_at" not in update_values:
            update_values["started_at"] = datetime.now()
        elif status in ["COMPLETED", "FAILED"]:
            update_values["completed_at"] = datetime.now()

        stmt = update(SimulationSession).where(
            SimulationSession.session_id == self.session_id
        ).values(**update_values)

        db.execute(stmt)
        db.commit()

    def _has_dividend_table(self, db: Session) -> bool:
        """dividend_info 테이블 존재 여부 캐시"""
        if not self._dividend_table_checked:
            result = db.execute(
                text("SELECT to_regclass('public.dividend_info')")
            ).scalar()
            self._dividend_table_available = result is not None
            self._dividend_table_checked = True
            if not self._dividend_table_available:
                logger.warning(
                    "dividend_info 테이블을 찾을 수 없어 배당수익률 계산을 비활성화합니다."
                )
        return self._dividend_table_available

    # 헬퍼 메서드들 (팩터 계산용)
    def _get_per(self, db: Session, stock_code: str, trading_date: date) -> float:
        """PER 계산 - Price to Earnings Ratio"""
        try:
            # 주가 정보 조회
            price_result = db.execute(
                text("""
                    SELECT sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not price_result or not price_result[0]:
                logger.debug(f"PER 계산 - 주가 없음: {stock_code}, {trading_date}")
                return 0.0

            price = float(price_result[0])

            # 최근 재무제표에서 당기순이익 조회 (report_date가 NULL이므로 bsns_year로 필터)
            net_income_result = db.execute(
                text("""
                    SELECT ist.thstrm_add_amount, fs.bsns_year
                    FROM income_statements ist
                    INNER JOIN financial_statements fs ON ist.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND ist.account_nm LIKE '%당기순이익%'
                      AND ist.thstrm_add_amount IS NOT NULL
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not net_income_result or not net_income_result[0]:
                logger.debug(f"PER 계산 - 당기순이익 없음: {stock_code}, {trading_date}")
                return 0.0

            net_income = float(net_income_result[0])

            # 시가총액과 주가로 발행주식수 역산
            if price <= 0:
                return 0.0

            market_cap_result = db.execute(
                text("""
                    SELECT sp.market_cap
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not market_cap_result or not market_cap_result[0]:
                logger.debug(f"PER 계산 - 시가총액 없음: {stock_code}, {trading_date}")
                return 0.0

            market_cap = float(market_cap_result[0])
            shares_outstanding = market_cap / price

            if shares_outstanding <= 0:
                return 0.0

            eps = net_income / shares_outstanding

            if eps <= 0:
                logger.debug(f"PER 계산 - EPS <= 0: {stock_code}, EPS={eps}")
                return 0.0

            per = price / eps

            # PER이 너무 크거나 음수면 제한
            if per < 0 or per > 100:
                logger.debug(f"PER 계산 - 범위 초과: {stock_code}, PER={per}")
                return 0.0
            return per

        except Exception as e:
            logger.error(f"PER 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_pbr(self, db: Session, stock_code: str, trading_date: date) -> float:
        """PBR 계산 - Price to Book Ratio"""
        try:
            # 주가 정보 조회
            price_result = db.execute(
                text("""
                    SELECT sp.close_price, sp.listed_shares
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not price_result or not price_result[0]:
                logger.debug(f"PBR 계산 - 주가 없음: {stock_code}, {trading_date}")
                return 0.0

            price = float(price_result[0])
            shares = float(price_result[1]) if price_result[1] else 0

            if shares <= 0:
                logger.debug(f"PBR 계산 - 발행주식수 없음: {stock_code}")
                return 0.0

            # 최근 재무제표에서 자본총계 조회 (report_date가 NULL이므로 bsns_year로 필터)
            equity_result = db.execute(
                text("""
                    SELECT bs.thstrm_amount, fs.bsns_year
                    FROM balance_sheets bs
                    INNER JOIN financial_statements fs ON bs.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND bs.account_nm LIKE '%자본총계%'
                      AND bs.thstrm_amount IS NOT NULL
                      AND bs.thstrm_amount > 0
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not equity_result or not equity_result[0] or equity_result[0] <= 0:
                logger.debug(f"PBR 계산 - 자본총계 없음: {stock_code}, {trading_date}")
                return 0.0

            total_equity = float(equity_result[0])

            # 시가총액으로 발행주식수 역산
            market_cap_result = db.execute(
                text("""
                    SELECT sp.market_cap
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not market_cap_result or not market_cap_result[0]:
                logger.debug(f"PBR 계산 - 시가총액 없음: {stock_code}")
                return 0.0

            market_cap = float(market_cap_result[0])
            shares_outstanding = market_cap / price if price > 0 else 0

            if shares_outstanding <= 0:
                return 0.0

            book_value_per_share = total_equity / shares_outstanding
            pbr = price / book_value_per_share

            # PBR이 너무 크거나 음수면 제한
            if pbr < 0 or pbr > 20:
                logger.debug(f"PBR 계산 - 범위 초과: {stock_code}, PBR={pbr}")
                return 0.0

            logger.info(f"PBR 계산 성공: {stock_code}, price={price}, total_equity={total_equity}, shares={shares_outstanding}, BPS={book_value_per_share}, PBR={pbr}")
            return pbr

        except Exception as e:
            logger.error(f"PBR 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_roe(self, db: Session, stock_code: str, trading_date: date) -> float:
        """ROE 계산 - Return on Equity"""
        try:
            # 당기순이익 조회 (report_date가 NULL이므로 bsns_year로 필터)
            net_income_result = db.execute(
                text("""
                    SELECT ist.thstrm_add_amount, fs.bsns_year
                    FROM income_statements ist
                    INNER JOIN financial_statements fs ON ist.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND ist.account_nm LIKE '%당기순이익%'
                      AND ist.thstrm_add_amount IS NOT NULL
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not net_income_result or not net_income_result[0]:
                logger.debug(f"ROE 계산 - 당기순이익 없음: {stock_code}, {trading_date}")
                return 0.0

            net_income = float(net_income_result[0])

            # 자본총계 조회 (report_date가 NULL이므로 bsns_year로 필터)
            equity_result = db.execute(
                text("""
                    SELECT bs.thstrm_amount, fs.bsns_year
                    FROM balance_sheets bs
                    INNER JOIN financial_statements fs ON bs.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND bs.account_nm LIKE '%자본총계%'
                      AND bs.thstrm_amount IS NOT NULL
                      AND bs.thstrm_amount > 0
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not equity_result or not equity_result[0]:
                logger.debug(f"ROE 계산 - 자본총계 없음: {stock_code}, {trading_date}")
                return 0.0

            total_equity = float(equity_result[0])

            if total_equity <= 0:
                return 0.0

            roe = (net_income / total_equity) * 100

            # ROE 범위 제한 (-50% ~ 50%)
            if roe < -50 or roe > 50:
                logger.debug(f"ROE 계산 - 범위 초과: {stock_code}, ROE={roe}")
                return 0.0
            return roe

        except Exception as e:
            logger.error(f"ROE 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_dividend_yield(self, db: Session, stock_code: str, trading_date: date) -> float:
        """배당수익률 계산"""
        try:
            # 현재 주가 조회
            price_result = db.execute(
                text("""
                    SELECT sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not price_result or not price_result[0]:
                logger.debug(f"배당수익률 계산 - 주가 없음: {stock_code}, {trading_date}")
                return 0.0

            price = float(price_result[0])

            # 최근 연간 배당금 조회 (dividend_info 테이블 사용, PostgreSQL 날짜 함수)
            if not self._has_dividend_table(db):
                return 0.0

            dividend_result = db.execute(
                text("""
                    SELECT SUM(di.cash_dividend_per_share) as annual_dividend
                    FROM dividend_info di
                    INNER JOIN companies c ON di.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND di.record_date > :trade_date - INTERVAL '1 year'
                      AND di.record_date <= :trade_date
                      AND di.cash_dividend_per_share IS NOT NULL
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not dividend_result or not dividend_result[0]:
                logger.debug(f"배당수익률 계산 - 배당 정보 없음: {stock_code}, {trading_date}")
                return 0.0

            annual_dividend = float(dividend_result[0])

            if price <= 0:
                return 0.0

            dividend_yield = (annual_dividend / price) * 100

            # 배당수익률 범위 제한 (0% ~ 20%)
            if dividend_yield < 0 or dividend_yield > 20:
                logger.debug(f"배당수익률 계산 - 범위 초과: {stock_code}, dividend_yield={dividend_yield}")
                return 0.0
            return dividend_yield

        except Exception as e:
            logger.error(f"배당수익률 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_momentum(self, db: Session, stock_code: str, trading_date: date, days: int) -> float:
        """모멘텀 계산 - 과거 N일간 수익률"""
        try:
            # 과거 N일 전 날짜 계산
            start_date = trading_date - timedelta(days=days * 2)  # 여유있게 설정

            # 과거 주가 데이터 조회
            result = db.execute(
                text("""
                    SELECT sp.trade_date, sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date BETWEEN :start_date AND :end_date
                    ORDER BY sp.trade_date DESC
                    LIMIT :limit
                """),
                {
                    "stock_code": stock_code,
                    "start_date": start_date,
                    "end_date": trading_date,
                    "limit": days + 1
                }
            ).fetchall()

            if len(result) < 2:
                return 0.0

            # 최근 가격과 N일 전 가격
            current_price = float(result[0][1])
            past_price = float(result[-1][1])

            if past_price <= 0:
                return 0.0

            momentum = ((current_price - past_price) / past_price) * 100

            # 모멘텀 범위 제한 (-50% ~ 100%)
            if momentum < -50 or momentum > 100:
                return 0.0

            return momentum

        except Exception as e:
            logger.error(f"모멘텀 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_volatility(self, db: Session, stock_code: str, trading_date: date, days: int) -> float:
        """변동성 계산 - 과거 N일간 일일 수익률의 표준편차"""
        try:
            # 과거 N일간 주가 데이터 조회
            start_date = trading_date - timedelta(days=days * 2)

            result = db.execute(
                text("""
                    SELECT sp.close_price
                    FROM stock_prices sp
                    INNER JOIN companies c ON sp.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND sp.trade_date BETWEEN :start_date AND :end_date
                    ORDER BY sp.trade_date ASC
                    LIMIT :limit
                """),
                {
                    "stock_code": stock_code,
                    "start_date": start_date,
                    "end_date": trading_date,
                    "limit": days + 1
                }
            ).fetchall()

            if len(result) < days:
                return 0.0

            prices = [float(row[0]) for row in result]

            # 일일 수익률 계산
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(daily_return)

            if len(returns) < 2:
                return 0.0

            # 변동성 계산 (연환산)
            volatility = np.std(returns) * np.sqrt(252) * 100

            # 변동성 범위 제한 (0% ~ 100%)
            if volatility < 0 or volatility > 100:
                return 0.0

            return volatility

        except Exception as e:
            logger.error(f"변동성 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _calculate_custom_factor(
        self, db: Session, stock_codes: List[str], trading_date: date,
        factor: Factor, setting: StrategyFactor
    ) -> List[float]:
        """커스텀 팩터 계산"""
        try:
            # 팩터 정의에 따른 커스텀 계산
            if factor.calculation_formula:
                # 커스텀 수식이 정의되어 있는 경우
                scores = []
                for stock_code in stock_codes:
                    score = self._evaluate_custom_formula(
                        db, stock_code, trading_date, factor.calculation_formula
                    )
                    scores.append(score)
                return scores

            # 복합 팩터 계산 (예: Quality Factor = ROE * ROA)
            if factor.factor_id == "QUALITY":
                scores = []
                for stock_code in stock_codes:
                    roe = self._get_roe(db, stock_code, trading_date)
                    roa = self._get_roa(db, stock_code, trading_date)
                    # Quality score = ROE와 ROA의 평균
                    score = (roe + roa) / 2 if (roe > 0 and roa > 0) else 0
                    scores.append(score)
                return scores

            # Value 복합 팩터 (PER, PBR, PSR의 역수 평균)
            elif factor.factor_id == "VALUE_COMPOSITE":
                scores = []
                for stock_code in stock_codes:
                    per = self._get_per(db, stock_code, trading_date)
                    pbr = self._get_pbr(db, stock_code, trading_date)
                    # Value score = 낮은 PER, PBR이 좋음
                    per_score = 1 / per if per > 0 else 0
                    pbr_score = 1 / pbr if pbr > 0 else 0
                    score = (per_score + pbr_score) / 2
                    scores.append(score)
                return scores

            # Growth 팩터 (매출 성장률, 이익 성장률)
            elif factor.factor_id == "GROWTH":
                scores = []
                for stock_code in stock_codes:
                    score = self._get_growth_rate(db, stock_code, trading_date)
                    scores.append(score)
                return scores

            # 기본값
            return [0.0 for _ in stock_codes]

        except Exception as e:
            logger.error(f"커스텀 팩터 계산 오류: {e}")
            db.rollback()
            return [0.0 for _ in stock_codes]

    def _get_roa(self, db: Session, stock_code: str, trading_date: date) -> float:
        """ROA 계산 - Return on Assets"""
        try:
            # 당기순이익 조회 (report_date가 NULL이므로 bsns_year로 필터)
            net_income_result = db.execute(
                text("""
                    SELECT ist.thstrm_add_amount, fs.bsns_year
                    FROM income_statements ist
                    INNER JOIN financial_statements fs ON ist.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND ist.account_nm LIKE '%당기순이익%'
                      AND ist.thstrm_add_amount IS NOT NULL
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not net_income_result or not net_income_result[0]:
                logger.debug(f"ROA 계산 - 당기순이익 없음: {stock_code}, {trading_date}")
                return 0.0

            net_income = float(net_income_result[0])

            # 자산총계 조회 (report_date가 NULL이므로 bsns_year로 필터)
            assets_result = db.execute(
                text("""
                    SELECT bs.thstrm_amount, fs.bsns_year
                    FROM balance_sheets bs
                    INNER JOIN financial_statements fs ON bs.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND bs.account_nm LIKE '%자산총계%'
                      AND bs.thstrm_amount IS NOT NULL
                      AND bs.thstrm_amount > 0
                      AND fs.bsns_year IS NOT NULL
                    ORDER BY fs.bsns_year DESC
                    LIMIT 1
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if not assets_result or not assets_result[0]:
                logger.debug(f"ROA 계산 - 자산총계 없음: {stock_code}, {trading_date}")
                return 0.0

            total_assets = float(assets_result[0])

            if total_assets <= 0:
                return 0.0

            roa = (net_income / total_assets) * 100

            # ROA 범위 제한 (-20% ~ 30%)
            if roa < -20 or roa > 30:
                logger.debug(f"ROA 계산 - 범위 초과: {stock_code}, ROA={roa}")
                return 0.0
            return roa

        except Exception as e:
            logger.error(f"ROA 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _get_growth_rate(self, db: Session, stock_code: str, trading_date: date) -> float:
        """매출 성장률 계산"""
        try:
            # 최근 2년간 매출액 조회 (report_date가 NULL이므로 bsns_year로 필터)
            result = db.execute(
                text("""
                    SELECT fs.bsns_year, ist.thstrm_add_amount
                    FROM income_statements ist
                    INNER JOIN financial_statements fs ON ist.stmt_id = fs.stmt_id
                    INNER JOIN companies c ON fs.company_id = c.company_id
                    WHERE c.stock_code = :stock_code
                      AND fs.reprt_code = '11011'
                      AND ist.thstrm_add_amount IS NOT NULL
                      AND fs.bsns_year IS NOT NULL
                      AND (ist.account_nm LIKE '%매출액%' OR ist.account_nm LIKE '%매출%')
                    ORDER BY fs.bsns_year DESC
                    LIMIT 2
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchall()

            if len(result) < 2:
                return 0.0

            current_revenue = float(result[0][1]) if result[0][1] else 0
            previous_revenue = float(result[1][1]) if result[1][1] else 0

            if previous_revenue <= 0:
                return 0.0

            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100

            # 성장률 범위 제한 (-50% ~ 100%)
            if growth_rate < -50 or growth_rate > 100:
                return 0.0

            return growth_rate

        except Exception as e:
            logger.error(f"성장률 계산 오류 ({stock_code}): {e}")
            db.rollback()
            return 0.0

    def _evaluate_custom_formula(self, db: Session, stock_code: str,
                                trading_date: date, formula: str) -> float:
        """커스텀 수식 평가"""
        # 간단한 수식 파서 구현
        # 실제 구현시에는 더 복잡한 수식 파싱이 필요
        try:
            # 예: "PER * 0.3 + PBR * 0.3 + ROE * 0.4"
            # 팩터 값들을 가져와서 계산
            return 0.0
        except:
            return 0.0


def run_advanced_backtest(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    benchmark: str = "KOSPI",
    target_stocks: List[str] = None  # 테마 이름 목록
) -> Dict:
    """백테스트 실행 (외부 호출용)"""

    engine = QuantBacktestEngine(session_id, strategy_id, target_stocks)
    return engine.run_backtest(start_date, end_date, initial_capital, benchmark)
