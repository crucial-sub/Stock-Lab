"""
자동매매 서비스
- 모의투자 계좌 전용
- 매일 오전 8시 종목 선정
- 오전 9시 주문 실행
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete, update, func, desc
import pandas as pd
import time
import requests

from app.models.auto_trading import (
    AutoTradingStrategy,
    LivePosition,
    LiveTrade,
    LiveDailyPerformance,
    AutoTradingLog
)
from app.models.simulation import (
    SimulationSession,
    PortfolioStrategy,
    TradingRule,
    StrategyFactor,
    SimulationDailyValue
)
from app.models.user import User
from app.services.kiwoom_service import KiwoomService
from app.utils.market_utils import is_market_hours

logger = logging.getLogger(__name__)


class AutoTradingService:
    """자동매매 서비스"""

    @staticmethod
    async def activate_strategy(
        db: AsyncSession,
        user_id: UUID,
        session_id: str,
        initial_capital: Decimal = None,
        allocated_capital: Decimal = None,
        strategy_name: Optional[str] = None
    ) -> AutoTradingStrategy:
        """
        자동매매 전략 활성화

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 백테스트 세션 ID
            initial_capital: 초기 자본금
            allocated_capital: 전략에 할당할 자본금 (여러 전략에 나누어 배분 가능)
            strategy_name: 자동매매 전략 이름 (미입력시 자동 생성)

        Returns:
            생성된 자동매매 전략
        """
        try:
            # 1. 백테스트 세션 확인
            session_query = select(SimulationSession).where(
                and_(
                    SimulationSession.session_id == session_id,
                    SimulationSession.user_id == user_id,
                    SimulationSession.status == "COMPLETED"
                )
            )
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                raise ValueError("완료된 백테스트 세션을 찾을 수 없습니다.")

            # 2. 기존 활성화된 전략 조회 (여러 전략 동시 활성화 가능)
            active_query = select(AutoTradingStrategy).where(
                and_(
                    AutoTradingStrategy.user_id == user_id,
                    AutoTradingStrategy.is_active == True
                )
            )
            active_result = await db.execute(active_query)
            active_strategies = active_result.scalars().all()

            # 2-1. allocated_capital 검증: 총 할당 금액이 계좌 잔고를 초과하지 않는지 확인
            if allocated_capital is None:
                raise ValueError("allocated_capital은 필수 항목입니다.")

            # 3. 백테스트 전략의 매매 조건 조회
            trading_rule_query = select(TradingRule).where(
                TradingRule.strategy_id == session.strategy_id
            )
            trading_rule_result = await db.execute(trading_rule_query)
            trading_rule = trading_rule_result.scalar_one_or_none()

            if not trading_rule:
                raise ValueError("백테스트 전략의 매매 조건을 찾을 수 없습니다.")

            # 백테스트 조건에서 데이터 추출
            buy_condition = trading_rule.buy_condition or {}
            sell_condition = trading_rule.sell_condition or {}

            # 4. 사용자 조회 (키움 토큰 필요)
            user_query = select(User).where(User.user_id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            # 디버깅 로그
            logger.info(f"🔍 activate_strategy - initial_capital: {initial_capital}")
            logger.info(f"🔍 activate_strategy - user found: {user is not None}")
            if user:
                logger.info(f"🔍 activate_strategy - has kiwoom_access_token: {user.kiwoom_access_token is not None}")
                if user.kiwoom_access_token:
                    logger.info(f"🔍 activate_strategy - token length: {len(user.kiwoom_access_token)}")

            # 5. initial_capital이 없으면 키움 계좌에서 실제 잔고 조회
            if initial_capital is None and user and user.kiwoom_access_token:
                try:
                    logger.info("🔍 키움 API 호출 시작...")
                    from app.services.kiwoom_service import KiwoomService

                    # 토큰 유효성 자동 검증 및 갱신
                    valid_token = await KiwoomService.ensure_valid_token(db, user)

                    deposit_info = KiwoomService.get_deposit_info(
                        access_token=valid_token,
                        qry_tp="3"  # 추정조회
                    )

                    logger.info(f"🔍 키움 API 응답: {deposit_info}")

                    # API 에러 체크
                    if deposit_info.get("return_code") != 0:
                        error_msg = deposit_info.get("return_msg", "알 수 없는 오류")
                        logger.warning(f"⚠️ 키움 API 에러: {error_msg}")
                        raise ValueError(f"키움 계좌 조회 실패: {error_msg}")

                    # API 응답에서 실제 주문가능금액 추출
                    # 키움 모의투자 API는 output1이 아니라 최상위 레벨에 데이터가 있음
                    actual_cash_str = (
                        deposit_info.get("ord_alow_amt") or        # 주문가능금액
                        deposit_info.get("ord_psbl_cash") or       # 주문가능현금
                        deposit_info.get("pymn_alow_amt") or       # 지불가능금액
                        deposit_info.get("dnca_tot_amt") or        # 예수금총액
                        deposit_info.get("d2_pymn_alow_amt") or    # D+2 지불가능금액
                        "0"
                    )

                    logger.info(f"🔍 actual_cash_str: {actual_cash_str}")
                    initial_capital = Decimal(str(actual_cash_str))

                    # 0원이면 에러로 처리
                    if initial_capital == 0:
                        raise ValueError("키움 계좌 잔고가 0원입니다. 계좌를 확인해주세요.")

                    logger.info(f"💰 키움 계좌 잔고 조회 성공: {initial_capital:,}원")

                except Exception as e:
                    logger.error(f"❌ 키움 계좌 잔고 조회 실패: {e}", exc_info=True)
                    # 실패 시 기본값 사용
                    initial_capital = Decimal("50000000")
                    logger.info(f"⚠️ 기본값 사용: {initial_capital:,}원")

            # initial_capital이 여전히 None이면 기본값 사용
            if initial_capital is None:
                initial_capital = Decimal("50000000")

            # 5-1. 총 할당 금액 검증
            total_allocated = sum(s.allocated_capital for s in active_strategies)
            total_allocated_after = total_allocated + allocated_capital

            if total_allocated_after > initial_capital:
                raise ValueError(
                    f"할당 금액 초과: 계좌 잔고 {initial_capital:,}원, "
                    f"기존 할당 {total_allocated:,}원, 신규 할당 {allocated_capital:,}원, "
                    f"총 {total_allocated_after:,}원. 계좌 잔고를 초과할 수 없습니다."
                )

            logger.info(
                f"💰 자본 할당 현황: 계좌 잔고 {initial_capital:,}원, "
                f"기존 전략 {len(active_strategies)}개에 {total_allocated:,}원 할당, "
                f"신규 할당 {allocated_capital:,}원, 남은 금액: {initial_capital - total_allocated_after:,}원"
            )

            # 5-1. strategy_name 생성 (미입력시 자동 생성)
            if not strategy_name:
                # 백테스트 전략 이름 조회
                portfolio_query = select(PortfolioStrategy).where(
                    PortfolioStrategy.strategy_id == session.strategy_id
                )
                portfolio_result = await db.execute(portfolio_query)
                portfolio_strategy = portfolio_result.scalar_one_or_none()

                base_name = portfolio_strategy.strategy_name if portfolio_strategy else "전략"
                strategy_name = f"{base_name} 연동"

            # 6. 새로운 자동매매 전략 생성 (백테스트 조건 전부 복사)
            strategy = AutoTradingStrategy(
                user_id=user_id,
                simulation_session_id=session_id,
                strategy_name=strategy_name,
                is_active=True,
                initial_capital=initial_capital,
                current_capital=allocated_capital,  # 할당된 자본으로 시작
                cash_balance=allocated_capital,  # 할당된 자본만 사용
                allocated_capital=allocated_capital,  # 전략에 할당된 자본
                activated_at=datetime.now(),
                # 기본 설정
                per_stock_ratio=Decimal(str(buy_condition.get('per_stock_ratio', 5.0))),
                max_positions=buy_condition.get('max_holdings', 20),
                rebalance_frequency=buy_condition.get('rebalance_frequency', 'DAILY').upper(),
                # 매수 조건
                buy_conditions=buy_condition.get('conditions'),
                buy_logic=buy_condition.get('logic'),
                priority_factor=buy_condition.get('priority_factor'),
                priority_order=buy_condition.get('priority_order', 'desc'),
                max_buy_value=Decimal(str(buy_condition['max_buy_value'])) if buy_condition.get('max_buy_value') else None,
                max_daily_stock=buy_condition.get('max_daily_stock'),
                buy_price_basis=buy_condition.get('buy_price_basis', '전일 종가'),
                buy_price_offset=Decimal(str(buy_condition.get('buy_price_offset', 0))),
                # 매도 조건 - 목표가/손절가
                target_gain=Decimal(str(sell_condition['target_and_loss']['target_gain'])) if sell_condition.get('target_and_loss') and sell_condition['target_and_loss'].get('target_gain') else None,
                stop_loss=Decimal(str(sell_condition['target_and_loss']['stop_loss'])) if sell_condition.get('target_and_loss') and sell_condition['target_and_loss'].get('stop_loss') else None,
                # 매도 조건 - 보유 기간
                min_hold_days=sell_condition['hold_days']['min_hold_days'] if sell_condition.get('hold_days') else None,
                max_hold_days=sell_condition['hold_days']['max_hold_days'] if sell_condition.get('hold_days') else None,
                hold_days_sell_price_basis=sell_condition['hold_days'].get('sell_price_basis') if sell_condition.get('hold_days') else None,
                hold_days_sell_price_offset=Decimal(str(sell_condition['hold_days']['sell_price_offset'])) if sell_condition.get('hold_days') and sell_condition['hold_days'].get('sell_price_offset') is not None else None,
                # 매도 조건 - 조건 매도
                sell_conditions=sell_condition['condition_sell'].get('sell_conditions') if sell_condition.get('condition_sell') else None,
                sell_logic=sell_condition['condition_sell'].get('sell_logic') if sell_condition.get('condition_sell') else None,
                condition_sell_price_basis=sell_condition['condition_sell'].get('sell_price_basis') if sell_condition.get('condition_sell') else None,
                condition_sell_price_offset=Decimal(str(sell_condition['condition_sell']['sell_price_offset'])) if sell_condition.get('condition_sell') and sell_condition['condition_sell'].get('sell_price_offset') is not None else None,
                # 수수료/슬리피지
                commission_rate=Decimal(str(trading_rule.commission_rate)) if trading_rule.commission_rate else Decimal("0.00015"),
                slippage=Decimal("0.001"),
                # 매매 대상
                trade_targets=buy_condition.get('trade_targets')
            )

            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)

            # 4. 로그 기록
            log = AutoTradingLog(
                strategy_id=strategy.strategy_id,
                event_type="ACTIVATED",
                event_level="INFO",
                message=f"자동매매 전략 활성화 - 할당 자본: {allocated_capital:,}원 (계좌 잔고: {initial_capital:,}원)",
                details={
                    "session_id": session_id,
                    "initial_capital": float(initial_capital),
                    "allocated_capital": float(allocated_capital),
                    "total_active_strategies": len(active_strategies) + 1,
                    "total_allocated": float(total_allocated_after)
                }
            )
            db.add(log)
            await db.commit()

            logger.info(
                f"✅ 자동매매 활성화: strategy_id={strategy.strategy_id}, user_id={user_id}, "
                f"할당 자본: {allocated_capital:,}원"
            )

            return strategy

        except Exception as e:
            await db.rollback()
            logger.error(f"자동매매 활성화 실패: {e}", exc_info=True)
            raise

    @staticmethod
    async def check_deactivation_conditions(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        비활성화 조건 검증

        Args:
            db: 데이터베이스 세션
            strategy_id: 전략 ID
            user_id: 사용자 ID

        Returns:
            {
                "can_deactivate_immediately": bool,  # 즉시 비활성화 가능 (보유 종목 0개)
                "can_sell_and_deactivate": bool,     # 매도 후 비활성화 가능 (장시간 + 보유종목 있음)
                "needs_scheduled_sell": bool,         # 예약 매도 필요 (장시간 외 + 보유종목 있음)
                "position_count": int,                # 보유 종목 수
                "is_market_hours": bool,              # 현재 장시간 여부
                "recommended_mode": str               # 추천 모드
            }
        """
        try:
            # 1. 전략 조회
            query = select(AutoTradingStrategy).where(
                and_(
                    AutoTradingStrategy.strategy_id == strategy_id,
                    AutoTradingStrategy.user_id == user_id
                )
            )
            result = await db.execute(query)
            strategy = result.scalar_one_or_none()

            if not strategy:
                raise ValueError("자동매매 전략을 찾을 수 없습니다.")

            # 2. 보유 종목 수 조회
            position_query = select(func.count(LivePosition.position_id)).where(
                LivePosition.strategy_id == strategy_id
            )
            position_result = await db.execute(position_query)
            position_count = position_result.scalar() or 0

            # 3. 현재 시각이 장시간인지 확인
            market_hours = is_market_hours()

            # 4. 조건 판단
            can_immediate = position_count == 0  # 보유 종목 0개면 즉시 비활성화
            can_sell = position_count > 0 and market_hours  # 보유 종목 있고 장시간이면 매도 후 비활성화
            needs_scheduled = position_count > 0 and not market_hours  # 보유 종목 있고 장시간 외면 예약 매도

            # 5. 추천 모드 결정
            if can_immediate:
                recommended_mode = "immediate"
            elif can_sell:
                recommended_mode = "sell_and_deactivate"
            else:
                recommended_mode = "scheduled_sell"

            return {
                "can_deactivate_immediately": can_immediate,
                "can_sell_and_deactivate": can_sell,
                "needs_scheduled_sell": needs_scheduled,
                "position_count": position_count,
                "is_market_hours": market_hours,
                "recommended_mode": recommended_mode
            }

        except Exception as e:
            logger.error(f"비활성화 조건 검증 실패: {e}", exc_info=True)
            raise

    @staticmethod
    async def deactivate_strategy(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID,
        sell_all: bool = True,
        deactivation_mode: Optional[str] = None
    ) -> Tuple[AutoTradingStrategy, int]:
        """
        자동매매 전략 비활성화

        Args:
            db: 데이터베이스 세션
            strategy_id: 전략 ID
            user_id: 사용자 ID
            sell_all: 보유 종목 전량 매도 여부
            deactivation_mode: 비활성화 모드 (immediate, sell_and_deactivate, scheduled_sell)

        Returns:
            (비활성화된 전략, 매도한 종목 수)
        """
        try:
            # 1. 전략 조회 및 권한 확인
            query = select(AutoTradingStrategy).where(
                and_(
                    AutoTradingStrategy.strategy_id == strategy_id,
                    AutoTradingStrategy.user_id == user_id
                )
            )
            result = await db.execute(query)
            strategy = result.scalar_one_or_none()

            if not strategy:
                raise ValueError("자동매매 전략을 찾을 수 없습니다.")

            sold_count = 0

            # 2. 비활성화 모드에 따른 처리
            if deactivation_mode == "immediate":
                # 즉시 비활성화 (보유 종목 없을 때)
                strategy.is_active = False
                strategy.deactivated_at = datetime.now()
                strategy.deactivation_mode = "immediate"

            elif deactivation_mode == "sell_and_deactivate":
                # 매도 후 비활성화 (장시간)
                sold_count = await AutoTradingService._sell_all_positions(db, strategy)
                strategy.is_active = False
                strategy.deactivated_at = datetime.now()
                strategy.deactivation_mode = "sell_and_deactivate"

            elif deactivation_mode == "scheduled_sell":
                # 예약 매도 (장시간 외)
                strategy.scheduled_deactivation = True
                strategy.deactivation_mode = "scheduled_sell"
                strategy.deactivation_requested_at = datetime.now()
                # is_active는 유지 (스케줄러가 처리할 때까지)

            else:
                # 기존 방식 호환 (sell_all 파라미터 사용)
                if sell_all:
                    sold_count = await AutoTradingService._sell_all_positions(db, strategy)
                strategy.is_active = False
                strategy.deactivated_at = datetime.now()

            # 3. 연결된 SimulationSession 비활성화 (즉시 비활성화일 때만)
            if not strategy.is_active and strategy.simulation_session_id:
                session_query = select(SimulationSession).where(
                    SimulationSession.session_id == strategy.simulation_session_id
                )
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                if session:
                    session.is_active = False

            await db.commit()
            await db.refresh(strategy)

            # 4. 로그 기록
            log_message = f"자동매매 비활성화 요청 - 모드: {deactivation_mode or 'legacy'}, 매도: {sold_count}개"
            if deactivation_mode == "scheduled_sell":
                log_message = f"자동매매 예약 비활성화 - 다음 장 시작 시 매도 예정"

            log = AutoTradingLog(
                strategy_id=strategy.strategy_id,
                event_type="DEACTIVATED" if not strategy.is_active else "SCHEDULED_DEACTIVATION",
                event_level="INFO",
                message=log_message,
                details={
                    "sold_count": sold_count,
                    "sell_all": sell_all,
                    "deactivation_mode": deactivation_mode,
                    "scheduled": deactivation_mode == "scheduled_sell"
                }
            )
            db.add(log)
            await db.commit()

            logger.info(f"✅ 자동매매 비활성화: strategy_id={strategy_id}, 모드={deactivation_mode}, 매도={sold_count}개")

            return strategy, sold_count

        except Exception as e:
            await db.rollback()
            logger.error(f"자동매매 비활성화 실패: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_strategy_logs(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AutoTradingLog]:
        """전략 이벤트 로그 조회"""
        strategy = await AutoTradingService._get_strategy(db, strategy_id, user_id)

        query = select(AutoTradingLog).where(
            AutoTradingLog.strategy_id == strategy.strategy_id
        ).order_by(desc(AutoTradingLog.created_at)).limit(limit)

        if event_type:
            query = query.where(AutoTradingLog.event_type == event_type)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_latest_rebalance_preview(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> Optional[AutoTradingLog]:
        """가장 최근 리밸런싱 프리뷰 로그"""
        logs = await AutoTradingService.get_strategy_logs(
            db=db,
            strategy_id=strategy_id,
            user_id=user_id,
            event_type="REBALANCE_PREVIEW",
            limit=1
        )
        return logs[0] if logs else None

    @staticmethod
    async def generate_rebalance_preview(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """즉시 리밸런싱 프리뷰 생성"""
        from app.services.auto_trading_executor import AutoTradingExecutor
        from app.models.auto_trading import AutoTradingLog
        from datetime import datetime

        strategy = await AutoTradingService._get_strategy(db, strategy_id, user_id)
        if not strategy.is_active:
            raise ValueError("비활성화된 전략입니다.")

        stocks = await AutoTradingExecutor.select_stocks_for_strategy(db, strategy)

        # 🔥 리밸런싱 프리뷰 로그 저장 (9시 매매 실행 시 필요)
        log_entry = AutoTradingLog(
            strategy_id=strategy_id,
            event_type='REBALANCE_PREVIEW',
            event_level='INFO',
            message=f"리밸런싱 프리뷰: {len(stocks)}개 종목 선정",
            details={"stocks": stocks}
        )
        db.add(log_entry)
        await db.commit()

        return stocks

    @staticmethod
    async def get_risk_snapshot(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """현재 포지션 기반 위험 스냅샷"""
        strategy = await AutoTradingService._get_strategy(db, strategy_id, user_id)

        positions_query = select(LivePosition).where(
            LivePosition.strategy_id == strategy.strategy_id
        )
        positions_result = await db.execute(positions_query)
        positions = positions_result.scalars().all()

        cash_balance = strategy.cash_balance or Decimal("0")
        invested_value = Decimal("0")
        positions_payload = []
        alerts: List[Dict[str, Any]] = []

        for position in positions:
            current_price = position.current_price or position.avg_buy_price
            market_value = current_price * position.quantity
            invested_value += market_value

            cost_basis = position.avg_buy_price * position.quantity
            unrealized = market_value - cost_basis
            pct = (unrealized / cost_basis * Decimal("100")) if cost_basis > 0 else Decimal("0")
            hold_days = position.hold_days if position.hold_days is not None else max(
                0, (date.today() - position.buy_date).days
            )

            positions_payload.append({
                "stock_code": position.stock_code,
                "stock_name": position.stock_name,
                "quantity": position.quantity,
                "market_value": market_value,
                "avg_buy_price": position.avg_buy_price,
                "current_price": current_price,
                "unrealized_profit": unrealized,
                "unrealized_profit_pct": pct,
                "hold_days": hold_days
            })

            if strategy.max_hold_days and hold_days >= strategy.max_hold_days:
                alerts.append({
                    "type": "MAX_HOLD",
                    "severity": "warning",
                    "message": f"{position.stock_code} 보유일 {hold_days}일 - 최대 보유일 초과",
                    "metadata": {"stock_code": position.stock_code}
                })

            if strategy.stop_loss is not None:
                stop_loss = Decimal(str(strategy.stop_loss))
                if pct <= -stop_loss:
                    alerts.append({
                        "type": "STOP_LOSS",
                        "severity": "critical",
                        "message": f"{position.stock_code} 손실률 {pct:.2f}%",
                        "metadata": {"stock_code": position.stock_code}
                    })

        total_value = cash_balance + invested_value
        exposure_ratio = float(invested_value / total_value) if total_value > 0 else 0.0

        return {
            "as_of": datetime.utcnow(),
            "cash_balance": cash_balance,
            "invested_value": invested_value,
            "total_value": total_value,
            "exposure_ratio": exposure_ratio,
            "alerts": alerts,
            "positions": positions_payload
        }

    @staticmethod
    async def enforce_risk_controls(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """위험 통제 자동 실행"""
        strategy = await AutoTradingService._get_strategy(db, strategy_id, user_id)

        positions_query = select(LivePosition).where(
            LivePosition.strategy_id == strategy.strategy_id
        )
        positions_result = await db.execute(positions_query)
        positions = positions_result.scalars().all()

        actions: List[Dict[str, Any]] = []

        for position in positions:
            current_price = position.current_price or position.avg_buy_price
            hold_days = position.hold_days if position.hold_days is not None else max(
                0, (date.today() - position.buy_date).days
            )
            cost_basis = position.avg_buy_price * position.quantity
            pnl_pct = (
                ((current_price * position.quantity) - cost_basis) / cost_basis * Decimal("100")
            ) if cost_basis > 0 else Decimal("0")

            triggered = False
            reason = None

            if strategy.max_hold_days and hold_days >= strategy.max_hold_days:
                triggered = True
                reason = "최대 보유기간 초과"

            if strategy.stop_loss is not None:
                stop_loss = Decimal(str(strategy.stop_loss))
                if pnl_pct <= -stop_loss:
                    triggered = True
                    reason = f"손절 조건 충족 ({pnl_pct:.2f}%)"

            if triggered:
                success = await AutoTradingService._execute_sell_order(
                    db, strategy, position, reason=reason or "위험 통제"
                )
                actions.append({
                    "stock_code": position.stock_code,
                    "quantity": position.quantity,
                    "reason": reason,
                    "executed": success
                })

        if actions:
            log = AutoTradingLog(
                strategy_id=strategy.strategy_id,
                event_type="RISK_CONTROL",
                event_level="INFO",
                message=f"위험 통제 실행 - {len(actions)}건",
                details={"actions": actions}
            )
            db.add(log)
            await db.commit()

        return actions

    @staticmethod
    async def get_execution_report(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """실거래 vs 백테스트 비교"""
        strategy = await AutoTradingService._get_strategy(db, strategy_id, user_id)

        live_query = select(LiveDailyPerformance).where(
            LiveDailyPerformance.strategy_id == strategy.strategy_id
        ).order_by(desc(LiveDailyPerformance.date)).limit(days)
        live_result = await db.execute(live_query)
        live_rows = list(reversed(live_result.scalars().all()))

        if not live_rows:
            return {"rows": [], "summary": {"days": 0}, "session_id": strategy.simulation_session_id}

        dates = [row.date for row in live_rows]
        backtest_query = select(SimulationDailyValue).where(
            and_(
                SimulationDailyValue.session_id == strategy.simulation_session_id,
                SimulationDailyValue.date.in_(dates)
            )
        )
        backtest_result = await db.execute(backtest_query)
        backtest_map = {row.date: row for row in backtest_result.scalars().all()}

        rows = []
        tracking_errors: List[Decimal] = []

        for live in live_rows:
            backtest = backtest_map.get(live.date)
            te = None
            if live.daily_return is not None and backtest and backtest.daily_return is not None:
                te = live.daily_return - backtest.daily_return
                tracking_errors.append(te)

            rows.append({
                "date": live.date,
                "live_total_value": live.total_value,
                "live_daily_return": live.daily_return,
                "backtest_total_value": backtest.portfolio_value if backtest else None,
                "backtest_daily_return": backtest.daily_return if backtest else None,
                "tracking_error": te
            })

        cumulative_live = live_rows[-1].cumulative_return if live_rows[-1].cumulative_return is not None else None
        cumulative_backtest = None
        if backtest_map:
            latest_date = max(backtest_map.keys())
            cumulative_backtest = backtest_map[latest_date].cumulative_return

        realized_vs_expected = None
        if rows and rows[-1]["live_total_value"] and rows[-1]["backtest_total_value"]:
            realized_vs_expected = rows[-1]["live_total_value"] - rows[-1]["backtest_total_value"]

        avg_te = None
        if tracking_errors:
            avg_te = sum(tracking_errors) / len(tracking_errors)

        summary = {
            "days": len(rows),
            "average_tracking_error": avg_te,
            "cumulative_live_return": cumulative_live,
            "cumulative_backtest_return": cumulative_backtest,
            "realized_vs_expected": realized_vs_expected
        }

        return {
            "rows": rows,
            "summary": summary,
            "session_id": strategy.simulation_session_id
        }

    @staticmethod
    async def _sell_all_positions(db: AsyncSession, strategy: AutoTradingStrategy) -> int:
        """
        보유 종목 전량 매도

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략

        Returns:
            매도한 종목 수
        """
        # 보유 종목 조회
        positions_query = select(LivePosition).where(
            LivePosition.strategy_id == strategy.strategy_id
        )
        positions_result = await db.execute(positions_query)
        positions = positions_result.scalars().all()

        sold_count = 0

        for position in positions:
            try:
                # 매도 주문 실행
                success = await AutoTradingService._execute_sell_order(
                    db, strategy, position, reason="전략 비활성화"
                )

                if success:
                    sold_count += 1

            except Exception as e:
                logger.error(f"종목 매도 실패: {position.stock_code}, {e}")
                continue

        return sold_count

    @staticmethod
    async def _execute_sell_order(
        db: AsyncSession,
        strategy: AutoTradingStrategy,
        position: LivePosition,
        reason: str = "매도 조건 충족"
    ) -> bool:
        """
        매도 주문 실행 (키움 API)

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략
            position: 보유 포지션
            reason: 매도 사유

        Returns:
            성공 여부
        """
        try:
            # 사용자 조회 (키움 토큰 필요)
            user_query = select(User).where(User.user_id == strategy.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if not user or not user.kiwoom_access_token:
                logger.error("키움 토큰이 없습니다.")
                return False

            # 키움 API 매도 주문 (429 대응 재시도)
            order_result = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    order_result = KiwoomService.sell_stock(
                        access_token=user.kiwoom_access_token,
                        stock_code=position.stock_code,
                        quantity=str(position.quantity),
                        price="",
                        trade_type="3",  # 시장가
                        dmst_stex_tp="KRX"  # 국내주식
                    )
                    break
                except requests.RequestException as req_err:
                    status_code = getattr(getattr(req_err, "response", None), "status_code", None)
                    if status_code == 429 and attempt < max_retries - 1:
                        wait_sec = 1 + attempt
                        logger.warning(
                            f"⚠️  매도 Rate limit 감지 (429) - {position.stock_code} 재시도 {attempt+1}/{max_retries}, {wait_sec}s 대기"
                        )
                        time.sleep(wait_sec)
                        continue
                    raise

            # 현재가 조회 (손익 계산용)
            current_price = position.current_price or position.avg_buy_price

            # 손익 계산
            sell_amount = current_price * position.quantity
            buy_amount = position.avg_buy_price * position.quantity
            profit = sell_amount - buy_amount
            profit_rate = (profit / buy_amount) * 100 if buy_amount > 0 else 0

            # 수수료 및 세금 계산
            commission = sell_amount * Decimal("0.00015")  # 0.015%
            tax = sell_amount * Decimal("0.0023")  # 0.23% 거래세

            net_profit = profit - commission - tax

            # 매매 내역 저장
            trade = LiveTrade(
                strategy_id=strategy.strategy_id,
                trade_date=date.today(),
                trade_type="SELL",
                stock_code=position.stock_code,
                stock_name=position.stock_name,
                quantity=position.quantity,
                price=current_price,
                amount=sell_amount,
                commission=commission,
                tax=tax,
                profit=net_profit,
                profit_rate=profit_rate,
                hold_days=position.hold_days,
                selection_reason=reason,
                order_number=order_result.get("order_no"),
                order_status="FILLED"
            )

            db.add(trade)

            # 현금 잔액 업데이트 (내부 추적용)
            strategy.cash_balance += (sell_amount - commission - tax)

            # 포지션 삭제
            await db.delete(position)

            await db.commit()

            logger.info(f"✅ 매도 완료: {position.stock_code}, 수량={position.quantity}, 손익={net_profit:,.0f}원")

            # 🔄 매도 후 실제 계좌 잔고 확인 (검증 목적)
            try:
                deposit_info = KiwoomService.get_deposit_info(
                    access_token=user.kiwoom_access_token,
                    qry_tp="3"  # 추정조회
                )

                # 키움 모의투자 API는 최상위 레벨에 데이터가 있음
                actual_cash_str = (
                    deposit_info.get("ord_alow_amt") or        # 주문가능금액
                    deposit_info.get("ord_psbl_cash") or       # 주문가능현금
                    deposit_info.get("pymn_alow_amt") or       # 지불가능금액
                    deposit_info.get("dnca_tot_amt") or        # 예수금총액
                    deposit_info.get("d2_pymn_alow_amt") or    # D+2 지불가능금액
                    "0"
                )
                actual_cash = Decimal(str(actual_cash_str))

                # ✅ 중요: cash_balance는 전략 내부에서만 관리, 키움 잔고는 검증만
                logger.info(f"💰 매도 후 계좌 잔고 확인: {actual_cash:,.0f}원 (전략 내부 잔고: {strategy.cash_balance:,.0f}원)")

            except Exception as sync_err:
                logger.warning(f"⚠️  매도 후 잔고 확인 실패 (무시): {sync_err}")

            return True

        except Exception as e:
            logger.error(f"매도 주문 실행 실패: {e}", exc_info=True)
            return False

    @staticmethod
    async def check_and_execute_sell_signals(
        db: AsyncSession,
        strategy: AutoTradingStrategy
    ) -> int:
        """
        보유 포지션 중 매도 조건에 해당하는 종목 매도

        Args:
            db: 데이터베이스 세션
            strategy: 자동매매 전략

        Returns:
            매도한 종목 수
        """
        from app.utils.date_utils import count_business_days
        from datetime import date

        # 보유 포지션 조회
        positions_query = select(LivePosition).where(
            LivePosition.strategy_id == strategy.strategy_id
        )
        positions_result = await db.execute(positions_query)
        positions = positions_result.scalars().all()

        if not positions:
            logger.info(f"전략 {strategy.strategy_id}: 보유 포지션 없음")
            return 0

        sold_count = 0
        failed_positions: List[Tuple[LivePosition, str]] = []  # (position, reason)
        today = date.today()

        for position in positions:
            try:
                # 🔥 hold_days 동적 계산 (영업일 기준)
                actual_hold_days = count_business_days(position.buy_date, today)

                # DB 값과 다르면 업데이트 (정합성 유지)
                if position.hold_days != actual_hold_days:
                    position.hold_days = actual_hold_days

                # 현재가 업데이트 필요 (실제로는 키움 API로 조회)
                # 여기서는 position.current_price 사용
                current_price = position.current_price or position.avg_buy_price
                profit_rate = (
                    (current_price - position.avg_buy_price) / position.avg_buy_price * 100
                )

                should_sell = False
                sell_reason = None

                # 1. 손절가 체크
                if strategy.stop_loss and profit_rate <= -float(strategy.stop_loss):
                    should_sell = True
                    sell_reason = f"손절 ({profit_rate:.2f}%)"

                # 2. 목표가 체크
                elif strategy.target_gain and profit_rate >= float(strategy.target_gain):
                    should_sell = True
                    sell_reason = f"익절 ({profit_rate:.2f}%)"

                # 3. 최소 보유일 미달이면 매도 안함
                if should_sell and strategy.min_hold_days:
                    if actual_hold_days < strategy.min_hold_days:
                        logger.info(
                            f"   {position.stock_code}: 매도 조건 충족하나 "
                            f"최소 보유일({strategy.min_hold_days}일) 미달 (보유: {actual_hold_days}일, 매수일: {position.buy_date})"
                        )
                        continue

                # 4. 최대 보유일 체크
                if not should_sell and strategy.max_hold_days:
                    if actual_hold_days >= strategy.max_hold_days:
                        should_sell = True
                        sell_reason = f"최대 보유일 도달 ({actual_hold_days}일, 매수일: {position.buy_date})"

                # 5. 매도 조건 충족 시 매도 실행
                if should_sell:
                    logger.info(f"   매도 신호: {position.stock_code} - {sell_reason}")
                    success = await AutoTradingService._execute_sell_order(
                        db=db,
                        strategy=strategy,
                        position=position,
                        reason=sell_reason
                    )
                    if success:
                        sold_count += 1
                    else:
                        # 실패한 포지션 기록
                        failed_positions.append((position, sell_reason))

            except Exception as e:
                logger.error(f"   매도 체크 실패: {position.stock_code}, {e}")

        # 실패한 매도 주문 재시도 (1회)
        if failed_positions:
            logger.info(f"🔄 실패한 매도 주문 {len(failed_positions)}개 재시도 중...")
            retry_success = 0

            for position, sell_reason in failed_positions:
                try:
                    # 재시도 대기
                    time.sleep(2)

                    logger.info(f"   재시도 매도: {position.stock_code} - {sell_reason}")
                    success = await AutoTradingService._execute_sell_order(
                        db=db,
                        strategy=strategy,
                        position=position,
                        reason=f"{sell_reason} (재시도)"
                    )

                    if success:
                        retry_success += 1
                        sold_count += 1
                        logger.info(f"✅ 재시도 성공: {position.stock_code}")

                except Exception as e:
                    logger.error(f"재시도 매도 실패: {position.stock_code}, {e}")

            if retry_success > 0:
                logger.info(f"✅ 매도 재시도 결과: {retry_success}/{len(failed_positions)}개 성공")

        logger.info(f"전략 {strategy.strategy_id}: {sold_count}개 종목 매도")
        return sold_count

    @staticmethod
    async def get_strategy_status(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        자동매매 전략 상태 조회

        Args:
            db: 데이터베이스 세션
            strategy_id: 전략 ID
            user_id: 사용자 ID

        Returns:
            전략 상태 정보
        """
        # 전략 조회
        strategy_query = select(AutoTradingStrategy).where(
            and_(
                AutoTradingStrategy.strategy_id == strategy_id,
                AutoTradingStrategy.user_id == user_id
            )
        )
        strategy_result = await db.execute(strategy_query)
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise ValueError("자동매매 전략을 찾을 수 없습니다.")

        # 보유 종목 조회
        positions_query = select(LivePosition).where(
            LivePosition.strategy_id == strategy_id
        )
        positions_result = await db.execute(positions_query)
        positions = positions_result.scalars().all()

        # 실시간 가격 업데이트 (키움 API에서 현재가 조회)
        if positions:
            try:
                from app.models.user import User
                from app.services.kiwoom_service import KiwoomService

                # 사용자의 키움 토큰 조회
                user_query = select(User).where(User.user_id == strategy.user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()

                if user and user.kiwoom_access_token:
                    logger.info(f"💰 키움 API를 통한 {len(positions)}개 종목 실시간 가격 업데이트 시작")

                    try:
                        # 키움 API에서 계좌 평가 잔고 조회
                        account_data = KiwoomService.get_account_evaluation(
                            access_token=user.kiwoom_access_token
                        )

                        # API 응답에서 보유 종목 정보 추출
                        holdings = account_data.get("acnt_evlt_remn_indv_tot", [])
                        logger.info(f"📊 키움 API에서 {len(holdings)}개 종목 데이터 수신")

                        # 종목코드를 key로 하는 딕셔너리로 변환 (빠른 검색)
                        # 키움 API는 "A005930" 형식으로 오므로 "A"를 제거하여 "005930" 형식으로 변환
                        holdings_dict = {}
                        for holding in holdings:
                            if holding.get("stk_cd"):
                                stock_code = holding["stk_cd"].replace("A", "", 1)  # 첫 번째 "A"만 제거
                                holdings_dict[stock_code] = holding

                        logger.info(f"📋 holdings_dict 종목 코드: {list(holdings_dict.keys())[:5]}...")  # 처음 5개만
                        logger.info(f"📋 live_positions 종목 코드: {[p.stock_code for p in positions[:5]]}...")  # 처음 5개만

                        updated_count = 0
                        for position in positions:
                            try:
                                # 키움 API에서 해당 종목 정보 찾기
                                holding_info = holdings_dict.get(position.stock_code)

                                if not holding_info:
                                    logger.warning(f"⚠️  종목 {position.stock_code} 키움 API 응답에 없음")
                                    continue

                                cur_prc = holding_info.get("cur_prc")
                                if not cur_prc:
                                    logger.warning(f"⚠️  종목 {position.stock_code} cur_prc 없음: {holding_info}")
                                    continue

                                old_price = position.current_price or position.avg_buy_price
                                current_price = Decimal(str(int(cur_prc)))  # 문자열 숫자를 int로 변환 후 Decimal로

                                # 키움 API의 실제 평가손익 사용 (수수료, 세금 포함)
                                evltv_prft = holding_info.get("evltv_prft")  # 평가손익
                                prft_rt = holding_info.get("prft_rt")  # 수익률

                                position.current_price = current_price

                                if evltv_prft:
                                    position.unrealized_profit = Decimal(str(int(evltv_prft)))
                                else:
                                    # fallback: 수수료 제외하고 계산
                                    position.unrealized_profit = (position.current_price - position.avg_buy_price) * position.quantity

                                if prft_rt:
                                    position.unrealized_profit_pct = Decimal(str(float(prft_rt)))
                                else:
                                    # fallback: 수수료 제외하고 계산
                                    position.unrealized_profit_pct = ((position.current_price - position.avg_buy_price) / position.avg_buy_price) * Decimal("100")

                                updated_count += 1
                                logger.debug(f"  📈 {position.stock_code}: {old_price:,.0f}원 → {position.current_price:,.0f}원 (손익률: {position.unrealized_profit_pct:+.2f}%)")

                            except Exception as price_err:
                                logger.warning(f"종목 {position.stock_code} 가격 조회 실패: {price_err}")
                                continue

                        # 키움 API의 이 전략 종목들의 평가액/손익 계산
                        strategy_stock_codes = {pos.stock_code for pos in positions}
                        strategy_eval_sum = Decimal("0")
                        strategy_profit_sum = Decimal("0")

                        for holding in account_data.get("acnt_evlt_remn_indv_tot", []):
                            stock_code = holding.get("stk_cd", "")
                            # 'A'로 시작하는 경우 제거 (예: A005930 -> 005930)
                            if stock_code.startswith("A"):
                                stock_code = stock_code[1:]

                            if stock_code in strategy_stock_codes:
                                # 평가금액 (보유수량 * 현재가)
                                evltv_amt = holding.get("evlt_amt")
                                if evltv_amt:
                                    strategy_eval_sum += Decimal(str(int(evltv_amt)))

                                # 평가손익 (수수료 포함)
                                evltv_prft = holding.get("evltv_prft")
                                if evltv_prft:
                                    strategy_profit_sum += Decimal(str(int(evltv_prft)))

                        # 현금 잔고 추가
                        strategy_eval_sum += strategy.cash_balance

                        # allocated_capital 기준 수익률 계산
                        kiwoom_total_eval = strategy_eval_sum
                        kiwoom_total_profit = strategy_profit_sum
                        kiwoom_total_profit_rate = Decimal("0")

                        if strategy.allocated_capital > 0:
                            kiwoom_total_profit_rate = (strategy_profit_sum / strategy.allocated_capital) * Decimal("100")

                        # 전략 객체에 키움 실제 데이터 추가 (DB에는 저장 안 함, 응답용)
                        strategy.kiwoom_total_eval = kiwoom_total_eval
                        strategy.kiwoom_total_profit = kiwoom_total_profit
                        strategy.kiwoom_total_profit_rate = kiwoom_total_profit_rate

                        # 변경사항 저장
                        await db.commit()
                        logger.info(f"✅ 키움 API를 통해 {updated_count}개 종목 가격 업데이트 완료 (평가액: {kiwoom_total_eval:,.0f}원, 손익: {kiwoom_total_profit:,.0f}원, 수익률: {kiwoom_total_profit_rate:.2f}%)")

                    except Exception as kiwoom_err:
                        logger.warning(f"키움 API 호출 실패, StockPrice 테이블에서 조회: {kiwoom_err}")

                        # 키움 API 실패 시 StockPrice 테이블에서 조회 (fallback)
                        from app.models.stock_price import StockPrice
                        from app.models.company import Company

                        updated_count = 0
                        for position in positions:
                            try:
                                company_query = select(Company).where(Company.stock_code == position.stock_code)
                                company_result = await db.execute(company_query)
                                company = company_result.scalar_one_or_none()

                                if not company:
                                    continue

                                latest_price_query = select(StockPrice).where(
                                    StockPrice.company_id == company.company_id
                                ).order_by(StockPrice.trade_date.desc()).limit(1)
                                latest_price_result = await db.execute(latest_price_query)
                                latest_price = latest_price_result.scalar_one_or_none()

                                if latest_price and latest_price.close_price:
                                    old_price = position.current_price or position.avg_buy_price
                                    position.current_price = Decimal(str(latest_price.close_price))
                                    position.unrealized_profit = (position.current_price - position.avg_buy_price) * position.quantity
                                    position.unrealized_profit_pct = ((position.current_price - position.avg_buy_price) / position.avg_buy_price) * Decimal("100")
                                    updated_count += 1

                            except Exception as price_err:
                                continue

                        await db.commit()
                        logger.info(f"✅ StockPrice 테이블에서 {updated_count}개 종목 가격 업데이트 완료")

                else:
                    logger.warning("키움 토큰이 없어 StockPrice 테이블에서 조회")
                    # 키움 토큰 없을 경우 기존 로직 사용
                    from app.models.stock_price import StockPrice
                    from app.models.company import Company

                    updated_count = 0
                    for position in positions:
                        try:
                            company_query = select(Company).where(Company.stock_code == position.stock_code)
                            company_result = await db.execute(company_query)
                            company = company_result.scalar_one_or_none()

                            if not company:
                                continue

                            latest_price_query = select(StockPrice).where(
                                StockPrice.company_id == company.company_id
                            ).order_by(StockPrice.trade_date.desc()).limit(1)
                            latest_price_result = await db.execute(latest_price_query)
                            latest_price = latest_price_result.scalar_one_or_none()

                            if latest_price and latest_price.close_price:
                                position.current_price = Decimal(str(latest_price.close_price))
                                position.unrealized_profit = (position.current_price - position.avg_buy_price) * position.quantity
                                position.unrealized_profit_pct = ((position.current_price - position.avg_buy_price) / position.avg_buy_price) * Decimal("100")
                                updated_count += 1

                        except Exception as price_err:
                            continue

                    await db.commit()
                    logger.info(f"✅ StockPrice 테이블에서 {updated_count}개 종목 가격 업데이트 완료")

            except Exception as e:
                logger.error(f"실시간 가격 업데이트 실패: {e}")
                # 실패해도 기존 데이터 반환

        # 오늘 매매 내역 조회
        today_trades_query = select(LiveTrade).where(
            and_(
                LiveTrade.strategy_id == strategy_id,
                LiveTrade.trade_date == date.today()
            )
        ).order_by(LiveTrade.created_at.desc())
        today_trades_result = await db.execute(today_trades_query)
        today_trades = today_trades_result.scalars().all()

        # 최근 성과 조회
        latest_performance_query = select(LiveDailyPerformance).where(
            LiveDailyPerformance.strategy_id == strategy_id
        ).order_by(LiveDailyPerformance.date.desc()).limit(1)
        latest_performance_result = await db.execute(latest_performance_query)
        latest_performance = latest_performance_result.scalar_one_or_none()

        return {
            "strategy": strategy,
            "positions": positions,
            "today_trades": today_trades,
            "latest_performance": latest_performance,
            "total_positions": len(positions),
            "total_trades": len(today_trades)
        }

    @staticmethod
    async def _get_strategy(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID
    ) -> AutoTradingStrategy:
        """전략 조회 + 권한 확인"""
        query = select(AutoTradingStrategy).where(
            and_(
                AutoTradingStrategy.strategy_id == strategy_id,
                AutoTradingStrategy.user_id == user_id
            )
        )
        result = await db.execute(query)
        strategy = result.scalar_one_or_none()
        if not strategy:
            raise ValueError("자동매매 전략을 찾을 수 없습니다.")
        return strategy

    @staticmethod
    async def get_portfolio_dashboard(
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        포트폴리오 대시보드 데이터 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            대시보드 통계 데이터
        """
        from sqlalchemy import func
        from decimal import Decimal

        # 1. 활성화된 전략 목록 조회
        strategies_query = select(AutoTradingStrategy).where(
            and_(
                AutoTradingStrategy.user_id == user_id,
                AutoTradingStrategy.is_active == True
            )
        )
        strategies_result = await db.execute(strategies_query)
        active_strategies = strategies_result.scalars().all()

        # 2. 전체 통계 계산 - 먼저 할당 자본 계산
        total_allocated_capital = Decimal("0")
        if active_strategies:
            total_allocated_capital = sum(s.allocated_capital for s in active_strategies)
            
        total_current_value = Decimal("0")
        total_positions_count = 0
        total_trades_today = 0

        # 키움 API를 통한 실제 평가액 조회 시도 (전체 계좌 정보)
        from app.models.user import User
        from app.services.kiwoom_service import KiwoomService

        user_query = select(User).where(User.user_id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()

        kiwoom_total_eval = None
        kiwoom_total_profit = None
        kiwoom_total_profit_rate = None

        if user and user.kiwoom_access_token:
            try:
                # 키움 API에서 전체 계좌 평가 조회
                account_data = KiwoomService.get_account_evaluation(
                    access_token=user.kiwoom_access_token
                )

                tot_evlt_amt = account_data.get("tot_evlt_amt")
                tot_evlt_pl = account_data.get("tot_evlt_pl")
                tot_prft_rt = account_data.get("tot_prft_rt")

                if tot_evlt_amt:
                    kiwoom_total_eval = Decimal(str(int(tot_evlt_amt)))
                if tot_evlt_pl:
                    kiwoom_total_profit = Decimal(str(int(tot_evlt_pl)))
                if tot_prft_rt:
                    kiwoom_total_profit_rate = Decimal(str(float(tot_prft_rt)))

                logger.info(f"💰 키움 API 전체 계좌 대시보드: 평가액={kiwoom_total_eval:,.0f}원, 손익={kiwoom_total_profit:,.0f}원, 수익률={kiwoom_total_profit_rate:.2f}%")

            except Exception as kiwoom_err:
                logger.warning(f"키움 API 대시보드 데이터 조회 실패: {kiwoom_err}")

        for strategy in active_strategies:

            # 현재 가치 계산 (현금 + 보유 주식 평가액)
            positions_query = select(LivePosition).where(
                LivePosition.strategy_id == strategy.strategy_id
            )
            positions_result = await db.execute(positions_query)
            positions = positions_result.scalars().all()

            stock_value = sum(
                (pos.current_price or pos.avg_buy_price) * pos.quantity
                for pos in positions
            )

            total_current_value += (strategy.cash_balance + stock_value)
            total_positions_count += len(positions)

        # 3. 오늘 매매 건수
        today_trades_query = select(func.count(LiveTrade.trade_id)).where(
            and_(
                LiveTrade.strategy_id.in_([s.strategy_id for s in active_strategies]),
                LiveTrade.trade_date == date.today()
            )
        )
        today_trades_result = await db.execute(today_trades_query)
        total_trades_today = today_trades_result.scalar() or 0

        # 4. 수익률 계산 (키움 API 전체 계좌 데이터 우선 사용)
        if kiwoom_total_eval is not None:
            # 키움 API 전체 계좌 데이터 사용
            final_total_assets = kiwoom_total_eval
            final_total_profit = kiwoom_total_profit or Decimal("0")
            final_total_return = kiwoom_total_profit_rate or Decimal("0")
        else:
            # DB 계산 데이터 사용 (fallback)
            final_total_assets = total_current_value
            final_total_profit = total_current_value - total_allocated_capital
            final_total_return = (
                (final_total_profit / total_allocated_capital * 100)
                if total_allocated_capital > 0
                else Decimal("0")
            )

        return {
            "total_assets": final_total_assets,
            "total_return": final_total_return,
            "total_profit": final_total_profit,
            "active_strategy_count": len(active_strategies),
            "total_positions": total_positions_count,
            "total_trades_today": total_trades_today,
            "total_allocated_capital": total_allocated_capital  # 자동매매에 할당된 총 금액
        }
