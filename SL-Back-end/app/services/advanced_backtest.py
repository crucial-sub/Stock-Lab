"""
고도화된 백테스트 엔진 - 실전 퀀트 투자 시뮬레이션
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, update, text, and_, or_
import pandas as pd
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

    def __init__(self, session_id: str, strategy_id: str):
        self.session_id = session_id
        self.strategy_id = strategy_id
        self.strategy = None
        self.trading_rules = None
        self.factor_settings = None
        self.positions = {}  # {stock_code: Position}
        self.cash = Decimal("0")
        self.portfolio_value = Decimal("0")
        self.current_date = None

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

                # 3. 초기 자본 설정
                self.cash = initial_capital
                self.portfolio_value = initial_capital

                # 4. 거래일 리스트 생성
                trading_days = self._get_trading_days(db, start_date, end_date)
                total_days = len(trading_days)

                logger.info(f"총 {total_days}개 거래일 시뮬레이션 시작")

                # 5. 일별 시뮬레이션 실행
                daily_results = []

                for day_idx, trading_date in enumerate(trading_days):
                    self.current_date = trading_date

                    # 진행률 업데이트
                    progress = int((day_idx / total_days) * 90) + 5
                    self._update_session_status(db, "RUNNING", progress)

                    # 일별 처리
                    daily_result = self._process_trading_day(db, trading_date)
                    daily_results.append(daily_result)

                    # 일별 가치 저장
                    self._save_daily_value(db, trading_date, daily_result)

                    # 주기별 리밸런싱 체크
                    if self._should_rebalance(trading_date):
                        self._rebalance_portfolio(db, trading_date)

                    # 중간 커밋 (100일마다)
                    if day_idx % 100 == 0:
                        db.commit()
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

        # 팩터 설정 로드
        self.factor_settings = db.execute(
            select(StrategyFactor).where(
                StrategyFactor.strategy_id == self.strategy_id
            )
        ).scalars().all()

        logger.info(f"전략 '{self.strategy.strategy_name}' 로드 완료")
        logger.info(f"- 매매 규칙: {len(self.trading_rules)}개")
        logger.info(f"- 팩터 설정: {len(self.factor_settings)}개")

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

        query = """
            SELECT DISTINCT c.company_id, c.stock_code, c.company_name,
                   c.market_type, c.industry, sp.market_cap
            FROM companies c
            INNER JOIN stock_prices sp ON c.company_id = sp.company_id
            WHERE c.is_active = 1
              AND sp.trade_date = :trade_date
        """

        params = {"trade_date": trading_date}

        # 시장 필터
        if self.strategy.universe_type and self.strategy.universe_type != "ALL":
            query += " AND c.market_type = :market_type"
            params["market_type"] = self.strategy.universe_type

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

        result = db.execute(text(query), params).fetchall()

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

    def _calculate_factor_scores(self, db: Session, stocks: List[Dict], trading_date: date) -> pd.DataFrame:
        """팩터 점수 계산"""

        stock_codes = [s["stock_code"] for s in stocks]

        # 팩터별 점수 계산
        factor_scores = pd.DataFrame()
        factor_scores["stock_code"] = stock_codes

        for factor_setting in self.factor_settings:
            factor = db.execute(
                select(Factor).where(
                    Factor.factor_id == factor_setting.factor_id
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
            factor_scores[factor.factor_id] = scores

        # 종합 점수 계산 (가중 평균)
        if len(self.factor_settings) > 0:
            weighted_sum = 0
            total_weight = 0

            for factor_setting in self.factor_settings:
                if factor_setting.usage_type == "SCORING":
                    weight = float(factor_setting.weight or 1.0)
                    factor_col = factor_setting.factor_id

                    if factor_col in factor_scores.columns:
                        # 방향성 적용
                        if factor_setting.direction == "NEGATIVE":
                            factor_scores[factor_col] = -factor_scores[factor_col]

                        weighted_sum += factor_scores[factor_col] * weight
                        total_weight += weight

            if total_weight > 0:
                factor_scores["total_score"] = weighted_sum / total_weight
            else:
                factor_scores["total_score"] = 0

        return factor_scores

    def _calculate_fundamental_factor(
        self, db: Session, stock_codes: List[str], trading_date: date,
        factor: Factor, setting: StrategyFactor
    ) -> List[float]:
        """재무 팩터 계산"""

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

    def _select_stocks_by_factors(self, factor_scores: pd.DataFrame) -> List[str]:
        """팩터 점수 기반 종목 선택"""

        # 스크리닝 적용
        screened = factor_scores.copy()

        for factor_setting in self.factor_settings:
            if factor_setting.usage_type == "SCREENING":
                factor_col = factor_setting.factor_id

                if factor_col in screened.columns:
                    if factor_setting.operator == "GT":
                        threshold = float(factor_setting.threshold_value)
                        screened = screened[screened[factor_col] > threshold]
                    elif factor_setting.operator == "LT":
                        threshold = float(factor_setting.threshold_value)
                        screened = screened[screened[factor_col] < threshold]

        # 랭킹 적용
        if "total_score" in screened.columns:
            screened = screened.sort_values("total_score", ascending=False)

        # 최대 보유 종목 수 제한
        max_positions = 20  # 기본값
        for rule in self.trading_rules:
            if rule.max_positions:
                max_positions = rule.max_positions
                break

        selected = screened.head(max_positions)["stock_code"].tolist()

        logger.info(f"팩터 기반 {len(selected)}개 종목 선택")
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
        # TODO: 전일 대비 수익률 계산

        return {
            "date": trading_date,
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "position_value": position_value,
            "positions": len(self.positions)
        }

    def _rebalance_portfolio(self, db: Session, trading_date: date):
        """포트폴리오 리밸런싱"""

        logger.info(f"{trading_date}: 포트폴리오 리밸런싱 시작")

        # 1. 유니버스 종목 조회
        universe_stocks = self._get_universe_stocks(db, trading_date)

        if not universe_stocks:
            logger.warning("유니버스에 종목이 없음")
            return

        # 2. 팩터 점수 계산
        factor_scores = self._calculate_factor_scores(db, universe_stocks, trading_date)

        # 3. 종목 선택
        selected_stocks = self._select_stocks_by_factors(factor_scores)

        # 4. 기존 포지션 정리 (선택되지 않은 종목 매도)
        current_stocks = list(self.positions.keys())
        for stock_code in current_stocks:
            if stock_code not in selected_stocks:
                self._sell_position(db, stock_code, trading_date)

        # 5. 새로운 포지션 구축
        position_size = self._calculate_position_size(len(selected_stocks))

        for stock_code in selected_stocks:
            if stock_code not in self.positions:
                self._buy_position(db, stock_code, position_size, trading_date)
            else:
                # 기존 포지션 조정
                self._adjust_position(db, stock_code, position_size, trading_date)

    def _buy_position(self, db: Session, stock_code: str, target_value: Decimal, trading_date: date):
        """매수 포지션 생성"""

        # 현재가 조회
        price_data = db.execute(
            text("""
                SELECT close_price FROM stock_prices
                WHERE stock_code = :stock_code AND trade_date = :trade_date
            """),
            {"stock_code": stock_code, "trade_date": trading_date}
        ).fetchone()

        if not price_data:
            return

        price = Decimal(str(price_data[0]))
        quantity = int(target_value / price)

        if quantity <= 0:
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

        logger.debug(f"매수: {stock_code} {quantity}주 @ {price}")

    def _sell_position(self, db: Session, stock_code: str, trading_date: date):
        """매도 포지션 처리"""

        if stock_code not in self.positions:
            return

        position = self.positions[stock_code]

        # 현재가 조회
        price_data = db.execute(
            text("""
                SELECT close_price FROM stock_prices
                WHERE stock_code = :stock_code AND trade_date = :trade_date
            """),
            {"stock_code": stock_code, "trade_date": trading_date}
        ).fetchone()

        if not price_data:
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

        logger.debug(f"매도: {stock_code} {quantity}주 @ {price}, 손익: {realized_pnl:.0f}")

    def _update_position_values(self, db: Session, trading_date: date):
        """포지션 가치 업데이트"""

        for stock_code, position in self.positions.items():
            price_data = db.execute(
                text("""
                    SELECT close_price FROM stock_prices
                    WHERE stock_code = :stock_code AND trade_date = :trade_date
                """),
                {"stock_code": stock_code, "trade_date": trading_date}
            ).fetchone()

            if price_data:
                current_price = Decimal(str(price_data[0]))
                position["value"] = current_price * position["quantity"]

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
                        SELECT close_price FROM stock_prices
                        WHERE stock_code = :stock_code AND trade_date = :trade_date
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
                self._sell_position(db, stock_code, trading_date)

    def _should_rebalance(self, trading_date: date) -> bool:
        """리밸런싱 필요 여부 확인"""

        for rule in self.trading_rules:
            if rule.rebalance_frequency == "MONTHLY":
                # 매월 첫 거래일
                if trading_date.day <= 7:  # 대략적인 첫 주
                    return True
            elif rule.rebalance_frequency == "QUARTERLY":
                # 분기별 첫 거래일
                if trading_date.month in [1, 4, 7, 10] and trading_date.day <= 7:
                    return True
            elif rule.rebalance_frequency == "WEEKLY":
                # 매주 월요일
                if trading_date.weekday() == 0:
                    return True

        return False

    def _calculate_position_size(self, num_positions: int) -> Decimal:
        """포지션 크기 계산"""

        if num_positions == 0:
            return Decimal("0")

        # 포지션 사이징 방법
        for rule in self.trading_rules:
            if rule.position_sizing == "EQUAL_WEIGHT":
                # 동일 가중
                return self.portfolio_value / num_positions
            # TODO: MARKET_CAP, RISK_PARITY 등 추가 구현

        # 기본값: 동일 가중
        return self.portfolio_value / num_positions

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
            # TODO: 수익률 계산 추가
            daily_return=Decimal("0"),
            cumulative_return=Decimal("0")
        )
        db.add(daily_value)

    def _calculate_statistics(self, daily_results: List[Dict]) -> Dict:
        """백테스트 통계 계산"""

        if not daily_results:
            return {}

        # DataFrame 변환
        df = pd.DataFrame(daily_results)
        df.set_index("date", inplace=True)

        # 수익률 계산
        initial_value = daily_results[0]["portfolio_value"]
        final_value = daily_results[-1]["portfolio_value"]
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

        return {
            "total_return": float(total_return),
            "volatility": float(volatility),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio),
            "final_capital": float(final_value)
        }

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

    # 헬퍼 메서드들 (팩터 계산용)
    def _get_per(self, db: Session, stock_code: str, trading_date: date) -> float:
        """PER 계산"""
        # TODO: 실제 PER 계산 로직 구현
        return np.random.randn()

    def _get_pbr(self, db: Session, stock_code: str, trading_date: date) -> float:
        """PBR 계산"""
        # TODO: 실제 PBR 계산 로직 구현
        return np.random.randn()

    def _get_roe(self, db: Session, stock_code: str, trading_date: date) -> float:
        """ROE 계산"""
        # TODO: 실제 ROE 계산 로직 구현
        return np.random.randn()

    def _get_dividend_yield(self, db: Session, stock_code: str, trading_date: date) -> float:
        """배당수익률 계산"""
        # TODO: 실제 배당수익률 계산 로직 구현
        return np.random.randn()

    def _get_momentum(self, db: Session, stock_code: str, trading_date: date, days: int) -> float:
        """모멘텀 계산"""
        # TODO: 실제 모멘텀 계산 로직 구현
        return np.random.randn()

    def _get_volatility(self, db: Session, stock_code: str, trading_date: date, days: int) -> float:
        """변동성 계산"""
        # TODO: 실제 변동성 계산 로직 구현
        return np.random.randn()

    def _calculate_custom_factor(
        self, db: Session, stock_codes: List[str], trading_date: date,
        factor: Factor, setting: StrategyFactor
    ) -> List[float]:
        """커스텀 팩터 계산"""
        # TODO: 커스텀 팩터 계산 로직 구현
        return [np.random.randn() for _ in stock_codes]


def run_advanced_backtest(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    benchmark: str = "KOSPI"
) -> Dict:
    """고도화된 백테스트 실행 (외부 호출용)"""

    engine = QuantBacktestEngine(session_id, strategy_id)
    return engine.run_backtest(start_date, end_date, initial_capital, benchmark)