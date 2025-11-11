"""
고도화된 백테스트 실행 함수
- BacktestEngine을 사용하여 백테스트 실행
- API 라우터에서 호출
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine

logger = logging.getLogger(__name__)


def run_advanced_backtest(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    benchmark: str,
    target_themes: List[str],  # 선택된 산업/테마 목록
    target_stocks: List[str],  # 선택된 개별 종목 코드 목록
    use_all_stocks: bool = False,  # 전체 종목 사용 여부
    buy_conditions: List[dict] = None,  # 매수 조건
    buy_logic: str = "AND",
    priority_factor: str = None,
    priority_order: str = "desc",
    max_holdings: int = 20,
    per_stock_ratio: float = 5.0,
    rebalance_frequency: str = "MONTHLY",
    commission_rate: float = 0.015,
    slippage: float = 0.1,
    target_and_loss: dict = None,
    hold_days: dict = None,
    condition_sell: dict = None,
    max_buy_value: Optional[float] = None,
    max_daily_stock: Optional[int] = None
):
    """
    고도화된 백테스트 실행 (동기 함수 - 백그라운드 실행용)

    Args:
        session_id: 시뮬레이션 세션 ID
        strategy_id: 전략 ID
        start_date: 백테스트 시작일
        end_date: 백테스트 종료일
        initial_capital: 초기 자본금 (원 단위)
        benchmark: 벤치마크 (KOSPI, KOSDAQ 등)
        target_themes: 선택된 산업/테마 목록
        target_stocks: 선택된 개별 종목 코드 목록
        use_all_stocks: 전체 종목 사용 여부
        buy_conditions: 매수 조건 리스트
        buy_logic: 매수 로직 (AND/OR)
        priority_factor: 우선순위 팩터
        priority_order: 우선순위 정렬 (asc/desc)
        max_holdings: 최대 보유 종목 수
        per_stock_ratio: 종목당 투자 비율 (%)
        rebalance_frequency: 리밸런싱 주기 (DAILY/MONTHLY)
        commission_rate: 수수료율 (%)
        slippage: 슬리피지 (%)
        target_and_loss: 목표가/손절가 조건
        hold_days: 보유 기간 조건
        condition_sell: 조건부 매도 조건
    """
    import asyncio

    # 새로운 이벤트 루프에서 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _run_backtest_async(
                session_id,
                strategy_id,
                start_date,
                end_date,
                initial_capital,
                benchmark,
                target_themes,
                target_stocks,
                use_all_stocks,
                buy_conditions,
                buy_logic,
                priority_factor,
                priority_order,
                max_holdings,
                per_stock_ratio,
                rebalance_frequency,
                commission_rate,
                slippage,
                target_and_loss,
                hold_days,
                condition_sell,
                max_buy_value,
                max_daily_stock
            )
        )
        return result
    finally:
        loop.close()


async def _run_backtest_async(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: Decimal,
    benchmark: str,
    target_themes: List[str],
    target_stocks: List[str],
    use_all_stocks: bool,
    buy_conditions: List[dict],
    buy_logic: str,
    priority_factor: str,
    priority_order: str,
    max_holdings: int,
    per_stock_ratio: float,
    rebalance_frequency: str,
    commission_rate: float,
    slippage: float,
    target_and_loss: dict,
    hold_days: dict,
    condition_sell: dict,
    max_buy_value: Optional[float],
    max_daily_stock: Optional[int]
):
    """비동기 백테스트 실행"""

    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"백테스트 시작 - Session: {session_id}")
            logger.info(f"기간: {start_date} ~ {end_date}")
            logger.info(f"초기 자본금: {initial_capital:,}원")
            logger.info(f"전체 종목 사용: {use_all_stocks}")
            logger.info(f"선택된 테마: {target_themes}")
            logger.info(f"선택된 종목: {target_stocks}")
            logger.info(f"매수 조건: {buy_conditions}")
            logger.info(f"리밸런싱 주기: {rebalance_frequency}")

            # 세션 상태 업데이트 (RUNNING)
            from app.models.simulation import SimulationSession
            from sqlalchemy import update

            stmt = (
                update(SimulationSession)
                .where(SimulationSession.session_id == session_id)
                .values(
                    status="RUNNING",
                    progress=0,
                    started_at=datetime.now()
                )
            )
            await db.execute(stmt)
            await db.commit()

            # BacktestEngine 생성
            engine = BacktestEngine(db)

            import re

            def _extract_factor(expr: str) -> Optional[str]:
                if not expr:
                    return None
                match = re.search(r'\{([^}]+)\}', expr)
                if not match:
                    return None
                return match.group(1).strip().upper()

            parsed_conditions = []
            if buy_conditions:
                for cond in buy_conditions:
                    factor_code = _extract_factor(cond.get('exp_left_side'))
                    if not factor_code:
                        continue
                    parsed_conditions.append({
                        "id": cond.get('name') or factor_code,
                        "factor": factor_code,
                        "operator": cond.get('inequality', '>'),
                        "value": cond.get('exp_right_side'),
                        "description": cond.get('exp_left_side')
                    })

            # 논리식이 없으면 기본적으로 모든 조건을 AND 로 연결
            expression_text = buy_logic.strip() if buy_logic else ""
            if not expression_text and parsed_conditions:
                expression_text = " and ".join([c["id"] for c in parsed_conditions])

            # 우선순위 팩터 정규화
            normalized_priority_factor = _extract_factor(priority_factor)

            buy_condition_payload: Optional[dict] = None
            if parsed_conditions:
                buy_condition_payload = {
                    "expression": expression_text or parsed_conditions[0]["id"],
                    "conditions": parsed_conditions,
                    "priority_factor": normalized_priority_factor,
                    "priority_order": priority_order or "desc"
                }

            # 기능상 SELL condition 리스트는 STOP/TAKE/HOLD 로직에 의해 관리하므로
            # condition_sell 의 factor 조건만 전달 (없으면 빈 리스트)
            parsed_sell_conditions = []
            if condition_sell:
                for sell_cond in condition_sell.get('sell_conditions', []):
                    factor_code = _extract_factor(sell_cond.get('exp_left_side', ''))
                    if not factor_code:
                        continue
                    parsed_sell_conditions.append({
                        "factor": factor_code,
                        "operator": sell_cond.get('inequality', '>'),
                        "value": sell_cond.get('exp_right_side', 0),
                        "description": sell_cond.get('exp_left_side')
                    })

            max_buy_value_won: Optional[Decimal] = None
            if max_buy_value is not None:
                max_buy_value_won = Decimal(str(max_buy_value)) * Decimal("10000")

            # 백테스트 실행
            result = await engine.run_backtest(
                backtest_id=UUID(session_id),
                buy_conditions=buy_condition_payload or parsed_conditions,
                sell_conditions=parsed_sell_conditions,
                start_date=start_date,
                end_date=end_date,
                condition_sell=condition_sell,
                target_and_loss=target_and_loss,
                hold_days=hold_days,
                initial_capital=initial_capital,
                rebalance_frequency=rebalance_frequency.upper(),
                max_positions=max_holdings,
                position_sizing="EQUAL_WEIGHT",
                benchmark=benchmark,
                commission_rate=Decimal(str(commission_rate / 100)),  # % -> decimal
                slippage=Decimal(str(slippage / 100)),  # % -> decimal
                target_themes=target_themes if not use_all_stocks else [],
                target_stocks=target_stocks if not use_all_stocks else [],
                per_stock_ratio=per_stock_ratio,
                max_buy_value=max_buy_value_won,
                max_daily_stock=max_daily_stock
            )

            logger.info(f"백테스트 완료 - Session: {session_id}")

            # 세션 상태 업데이트 (COMPLETED)
            stmt = (
                update(SimulationSession)
                .where(SimulationSession.session_id == session_id)
                .values(
                    status="COMPLETED",
                    progress=100,
                    completed_at=datetime.now()
                )
            )
            await db.execute(stmt)
            await db.commit()

            return result

        except Exception as e:
            logger.error(f"백테스트 실행 중 오류: {e}", exc_info=True)

            # 세션 상태를 'FAILED'로 업데이트
            from app.models.simulation import SimulationSession
            from sqlalchemy import update

            stmt = (
                update(SimulationSession)
                .where(SimulationSession.session_id == session_id)
                .values(
                    status="FAILED",
                    error_message=str(e),
                    completed_at=datetime.now()
                )
            )
            await db.execute(stmt)
            await db.commit()

            raise
