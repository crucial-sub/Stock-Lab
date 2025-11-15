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
from sqlalchemy import select, and_, or_, delete, update, func
import pandas as pd

from app.models.auto_trading import (
    AutoTradingStrategy,
    LivePosition,
    LiveTrade,
    LiveDailyPerformance,
    AutoTradingLog
)
from app.models.simulation import SimulationSession, PortfolioStrategy, TradingRule, StrategyFactor
from app.models.user import User
from app.services.kiwoom_service import KiwoomService

logger = logging.getLogger(__name__)


class AutoTradingService:
    """자동매매 서비스"""

    @staticmethod
    async def activate_strategy(
        db: AsyncSession,
        user_id: UUID,
        session_id: str,
        initial_capital: Decimal = Decimal("50000000")
    ) -> AutoTradingStrategy:
        """
        자동매매 전략 활성화

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            session_id: 백테스트 세션 ID
            initial_capital: 초기 자본금

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

            # 2. 기존 활성화된 전략이 있는지 확인
            active_query = select(AutoTradingStrategy).where(
                and_(
                    AutoTradingStrategy.user_id == user_id,
                    AutoTradingStrategy.is_active == True
                )
            )
            active_result = await db.execute(active_query)
            active_strategy = active_result.scalar_one_or_none()

            if active_strategy:
                raise ValueError("이미 활성화된 자동매매 전략이 있습니다. 먼저 비활성화 해주세요.")

            # 3. 새로운 자동매매 전략 생성
            strategy = AutoTradingStrategy(
                user_id=user_id,
                simulation_session_id=session_id,
                is_active=True,
                initial_capital=initial_capital,
                current_capital=initial_capital,
                cash_balance=initial_capital,
                activated_at=datetime.now()
            )

            db.add(strategy)
            await db.commit()
            await db.refresh(strategy)

            # 4. 로그 기록
            log = AutoTradingLog(
                strategy_id=strategy.strategy_id,
                event_type="ACTIVATED",
                event_level="INFO",
                message=f"자동매매 전략 활성화 - 초기 자본금: {initial_capital:,}원",
                details={"session_id": session_id, "initial_capital": float(initial_capital)}
            )
            db.add(log)
            await db.commit()

            logger.info(f"✅ 자동매매 활성화: strategy_id={strategy.strategy_id}, user_id={user_id}")

            return strategy

        except Exception as e:
            await db.rollback()
            logger.error(f"자동매매 활성화 실패: {e}", exc_info=True)
            raise

    @staticmethod
    async def deactivate_strategy(
        db: AsyncSession,
        strategy_id: UUID,
        user_id: UUID,
        sell_all: bool = True
    ) -> Tuple[AutoTradingStrategy, int]:
        """
        자동매매 전략 비활성화

        Args:
            db: 데이터베이스 세션
            strategy_id: 전략 ID
            user_id: 사용자 ID
            sell_all: 보유 종목 전량 매도 여부

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

            # 2. 보유 종목 전량 매도 (선택)
            if sell_all:
                sold_count = await AutoTradingService._sell_all_positions(db, strategy)

            # 3. 전략 비활성화
            strategy.is_active = False
            strategy.deactivated_at = datetime.now()

            await db.commit()
            await db.refresh(strategy)

            # 4. 로그 기록
            log = AutoTradingLog(
                strategy_id=strategy.strategy_id,
                event_type="DEACTIVATED",
                event_level="INFO",
                message=f"자동매매 전략 비활성화 - 매도 종목: {sold_count}개",
                details={"sold_count": sold_count, "sell_all": sell_all}
            )
            db.add(log)
            await db.commit()

            logger.info(f"✅ 자동매매 비활성화: strategy_id={strategy_id}, 매도={sold_count}개")

            return strategy, sold_count

        except Exception as e:
            await db.rollback()
            logger.error(f"자동매매 비활성화 실패: {e}", exc_info=True)
            raise

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

            # 키움 API 매도 주문
            order_result = KiwoomService.sell_stock(
                access_token=user.kiwoom_access_token,
                stock_code=position.stock_code,
                quantity=position.quantity,
                price=0,  # 시장가
                trade_type="03",  # 시장가 매도
                dmst_stex_tp="1"  # 국내주식
            )

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

            # 현금 잔액 업데이트
            strategy.cash_balance += (sell_amount - commission - tax)

            # 포지션 삭제
            await db.delete(position)

            await db.commit()

            logger.info(f"✅ 매도 완료: {position.stock_code}, 수량={position.quantity}, 손익={net_profit:,.0f}원")

            return True

        except Exception as e:
            logger.error(f"매도 주문 실행 실패: {e}", exc_info=True)
            return False

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
