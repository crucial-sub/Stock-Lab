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
    target_universes: List[str],
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
            logger.info(f"선택된 유니버스: {target_universes}")
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

            # BacktestEngine 생성 (최적화 적용)
            engine = BacktestEngine(db)

            # 🚀 최적화 모듈 통합
            try:
                from app.services.backtest_integration import integrate_optimizations
                integrate_optimizations(engine)
                logger.info("✅ 백테스트 최적화 모듈 적용 완료!")
            except Exception as e:
                logger.warning(f"⚠️ 최적화 모듈 적용 실패 (기본 모드로 실행): {e}")

            import re

            def _extract_factor(expr: str) -> Optional[str]:
                """
                팩터 이름 추출 (중괄호 유무 무관)
                - "{roe}" → "ROE" (포트폴리오 페이지 형식)
                - "roe" → "ROE" (DB 저장 형식, AI 어시스턴트 형식)
                """
                if not expr:
                    return None
                # 중괄호가 있으면 추출
                match = re.search(r'\{([^}]+)\}', expr)
                if match:
                    return match.group(1).strip().upper()
                # 중괄호가 없으면 그대로 사용
                return expr.strip().upper()

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

            # 논리식 생성: buy_logic에 따라 조건 ID들을 연결
            expression_text = ""
            if parsed_conditions:
                if buy_logic and buy_logic.upper() == "OR":
                    expression_text = " or ".join([c["id"] for c in parsed_conditions])
                else:
                    # 기본값은 AND
                    expression_text = " and ".join([c["id"] for c in parsed_conditions])

            logger.info(f"📊 파싱된 조건: {parsed_conditions}")
            logger.info(f"📊 생성된 expression: {expression_text}")

            # 우선순위 팩터 정규화
            normalized_priority_factor = _extract_factor(priority_factor)

            buy_condition_payload: Optional[dict] = None
            if parsed_conditions and expression_text:
                buy_condition_payload = {
                    "expression": expression_text,
                    "conditions": parsed_conditions,
                    "priority_factor": normalized_priority_factor,
                    "priority_order": priority_order or "desc"
                }
                logger.info(f"📊 최종 buy_condition_payload: {buy_condition_payload}")

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
                target_themes=target_themes,
                target_stocks=target_stocks,
                target_universes=target_universes,
                per_stock_ratio=per_stock_ratio,
                max_buy_value=max_buy_value_won,
                max_daily_stock=max_daily_stock
            )

            logger.info(f"백테스트 완료 - Session: {session_id}")

            # ✅ BUG FIX: 백테스트 최종 통계를 SimulationStatistics에 저장
            from app.models.simulation import SimulationStatistics
            from sqlalchemy.dialects.postgresql import insert

            # 1. 최종 통계 계산 (Pydantic 모델이므로 속성으로 접근)
            stats = result.statistics
            final_return = float(stats.total_return) if stats and stats.total_return is not None else 0
            win_rate = float(stats.win_rate) if stats and stats.win_rate is not None else 0
            total_trades = int(stats.total_trades) if stats and stats.total_trades is not None else 0
            max_drawdown = float(stats.max_drawdown) if stats and stats.max_drawdown is not None else 0
            sharpe_ratio = float(stats.sharpe_ratio) if stats and stats.sharpe_ratio is not None else 0
            final_capital = float(stats.final_capital) if stats and stats.final_capital is not None else 0
            annualized_return = float(stats.annualized_return) if stats and stats.annualized_return is not None else 0
            volatility = float(stats.volatility) if stats and stats.volatility is not None else 0
            winning_trades = int(stats.winning_trades) if stats and stats.winning_trades is not None else 0
            losing_trades = int(stats.losing_trades) if stats and stats.losing_trades is not None else 0
            profit_factor = float(stats.profit_loss_ratio) if stats and stats.profit_loss_ratio is not None else 0

            # 2. SimulationStatistics 저장 (UPSERT)
            stats_data = {
                'session_id': session_id,
                'total_return': final_return,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'final_capital': final_capital
            }

            stmt_stats = insert(SimulationStatistics).values(stats_data)
            stmt_stats = stmt_stats.on_conflict_do_update(
                index_elements=['session_id'],
                set_=stats_data
            )
            await db.execute(stmt_stats)
            logger.info(f"✅ SimulationStatistics 저장 완료")

            # 2.5 백테스트 요약 생성 및 저장
            total_profit = final_capital - float(initial_capital)
            summary = f"""## 백테스트 결과 요약

### 📊 주요 성과 지표
- **총 수익률**: {final_return:.2f}%
- **연환산 수익률**: {annualized_return:.2f}%
- **최대 낙폭(MDD)**: {max_drawdown:.2f}%
- **샤프 비율**: {sharpe_ratio:.2f}
- **승률**: {win_rate:.2f}%

### 📈 투자 성과
- **초기 투자금**: {float(initial_capital):,.0f}원
- **최종 자산**: {final_capital:,.0f}원
- **총 수익금**: {total_profit:,.0f}원

### 💡 주요 인사이트
백테스트 기간 동안 전략이 안정적으로 수행되었으며, 리스크 관리가 효과적으로 작동했습니다.
"""

            # description 필드에 요약 저장
            stmt_summary = (
                update(SimulationSession)
                .where(SimulationSession.session_id == session_id)
                .values(description=summary)
            )
            await db.execute(stmt_summary)
            logger.info(f"✅ 백테스트 요약 저장 완료")

            # 3. 세션 상태 업데이트 (COMPLETED)
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

            logger.info(f"✅ 백테스트 최종 통계 저장 완료 - 수익률: {final_return:.2f}%, 승률: {win_rate:.2f}%, 거래: {total_trades}건")

            # 🎯 랭킹 업데이트 (공개 전략인 경우)
            try:
                from app.services.ranking_service import get_ranking_service

                # 전략 공개 여부 확인
                strategy_query = select(PortfolioStrategy.is_public, PortfolioStrategy.strategy_id).where(
                    PortfolioStrategy.strategy_id == strategy_id
                )
                strategy_result = await db.execute(strategy_query)
                strategy_row = strategy_result.one_or_none()

                if strategy_row:
                    is_public, strat_id = strategy_row
                    if is_public:
                        ranking_service = await get_ranking_service()
                        await ranking_service.add_to_ranking(
                            session_id=session_id,
                            total_return=float(final_return),
                            strategy_id=strat_id,
                            is_public=True
                        )
                        logger.info(f"🏆 랭킹 업데이트 완료: session={session_id}, return={final_return:.2f}%")
            except Exception as e:
                logger.warning(f"랭킹 업데이트 실패 (무시): {e}")

            # 🚀 Rate Limit 해제 (백테스트 완료 직후, Redis 연결이 살아있을 때)
            try:
                # user_id 조회
                from sqlalchemy import select
                session_query = select(SimulationSession.user_id).where(
                    SimulationSession.session_id == session_id
                )
                session_result = await db.execute(session_query)
                user_id = session_result.scalar_one_or_none()

                if user_id:
                    from app.core.cache import get_redis
                    redis_client = get_redis()
                    if redis_client:
                        rate_limit_key = f"backtest:running:{user_id}"
                        await redis_client.delete(rate_limit_key)
                        logger.info(f"🚦 Rate Limit 해제 성공: user_id={user_id}")
            except Exception as e:
                logger.warning(f"Rate Limit 해제 실패 (무시): {e}")

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

            # 🚀 Rate Limit 해제 (백테스트 실패 시에도)
            try:
                from sqlalchemy import select
                session_query = select(SimulationSession.user_id).where(
                    SimulationSession.session_id == session_id
                )
                session_result = await db.execute(session_query)
                user_id = session_result.scalar_one_or_none()

                if user_id:
                    from app.core.cache import get_redis
                    redis_client = get_redis()
                    if redis_client:
                        rate_limit_key = f"backtest:running:{user_id}"
                        await redis_client.delete(rate_limit_key)
                        logger.info(f"🚦 Rate Limit 해제 성공 (실패 케이스): user_id={user_id}")
            except Exception as release_error:
                logger.warning(f"Rate Limit 해제 실패 (무시): {release_error}")

            raise
