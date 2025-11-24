"""
자동매매 스케줄러
- 매일 오전 7시: 매수/매도 종목 선정 (리밸런싱 프리뷰)
- 매일 오전 9시: 실제 매수/매도 주문 실행
"""
import logging
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.auto_trading import AutoTradingStrategy
from app.models.user import User
from app.services.auto_trading_service import AutoTradingService
from app.services.auto_trading_executor import AutoTradingExecutor
from app.services.kiwoom_service import KiwoomService

logger = logging.getLogger(__name__)

# 글로벌 스케줄러 인스턴스
scheduler: AsyncIOScheduler | None = None


async def update_all_position_hold_days():
    """
    모든 보유 포지션의 hold_days 업데이트 (영업일 기준)
    """
    from app.models.auto_trading import LivePosition
    from app.utils.date_utils import count_business_days
    from datetime import date

    logger.info("🔄 보유 포지션 hold_days 업데이트 중...")

    async with AsyncSessionLocal() as db:
        try:
            # 모든 보유 포지션 조회
            positions_query = select(LivePosition)
            positions_result = await db.execute(positions_query)
            positions = positions_result.scalars().all()

            if not positions:
                logger.info("   보유 포지션 없음")
                return

            today = date.today()
            updated_count = 0

            for position in positions:
                # 영업일 기준으로 hold_days 계산
                business_days = count_business_days(position.buy_date, today)
                old_days = position.hold_days
                position.hold_days = business_days

                if old_days != business_days:
                    updated_count += 1
                    logger.debug(
                        f"   {position.stock_code}: {old_days}일 -> {business_days}일 (매수일: {position.buy_date})"
                    )

            await db.commit()
            logger.info(f"✅ hold_days 업데이트 완료: {updated_count}/{len(positions)}개 변경됨")

        except Exception as e:
            logger.error(f"❌ hold_days 업데이트 실패: {e}", exc_info=True)
            await db.rollback()


async def select_stocks_for_active_strategies():
    """
    모든 활성화된 자동매매 전략에 대해 종목 선정 (오전 7시 실행)
    """
    logger.info("=" * 80)
    logger.info("🔍 [오전 7시] 자동매매 종목 선정 시작")
    logger.info("=" * 80)

    # 1. 먼저 모든 포지션의 hold_days 업데이트
    await update_all_position_hold_days()

    async with AsyncSessionLocal() as db:
        try:
            # 활성화된 모든 전략 조회
            query = select(AutoTradingStrategy).where(
                AutoTradingStrategy.is_active == True
            )
            result = await db.execute(query)
            active_strategies = result.scalars().all()

            if not active_strategies:
                logger.info("⚠️  활성화된 자동매매 전략이 없습니다.")
                return

            logger.info(f"✅ {len(active_strategies)}개의 활성화된 전략 발견")

            # 각 전략에 대해 종목 선정
            for strategy in active_strategies:
                try:
                    logger.info(f"\n📊 전략 ID: {strategy.strategy_id} - 종목 선정 중...")

                    # 리밸런싱 프리뷰 생성 (종목 선정 + 로그 저장)
                    stocks = await AutoTradingService.generate_rebalance_preview(
                        db=db,
                        strategy_id=strategy.strategy_id,
                        user_id=strategy.user_id
                    )

                    logger.info(
                        f"✅ 전략 {strategy.strategy_id}: {len(stocks)}개 종목 선정 완료"
                    )

                    # 선정된 종목 상위 5개 로그 출력
                    for i, stock in enumerate(stocks[:5], 1):
                        logger.info(
                            f"   {i}. {stock.get('stock_code')} {stock.get('company_name')} - "
                            f"목표 수량: {stock.get('quantity')}주"
                        )

                except Exception as e:
                    logger.error(
                        f"❌ 전략 {strategy.strategy_id} 종목 선정 실패: {e}",
                        exc_info=True
                    )

            logger.info("\n" + "=" * 80)
            logger.info("✅ 오전 7시 종목 선정 완료")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 종목 선정 작업 실패: {e}", exc_info=True)


async def execute_trades_for_active_strategies():
    """
    모든 활성화된 자동매매 전략에 대해 매수/매도 실행 (오전 9시 실행)
    """
    logger.info("=" * 80)
    logger.info("💰 [오전 9시] 자동매매 주문 실행 시작")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        try:
            # 활성화된 모든 전략 조회
            query = select(AutoTradingStrategy).where(
                AutoTradingStrategy.is_active == True
            )
            result = await db.execute(query)
            active_strategies = result.scalars().all()

            if not active_strategies:
                logger.info("⚠️  활성화된 자동매매 전략이 없습니다.")
                return

            logger.info(f"✅ {len(active_strategies)}개의 활성화된 전략 발견")

            # 각 전략에 대해 매수/매도 실행
            for strategy in active_strategies:
                try:
                    logger.info(f"\n📊 전략 ID: {strategy.strategy_id} - 매매 실행 중...")

                    # 0. 유저 조회 및 키움 토큰 자동 갱신
                    user_query = select(User).where(User.user_id == strategy.user_id)
                    user_result = await db.execute(user_query)
                    user = user_result.scalar_one_or_none()

                    if user and user.kiwoom_access_token:
                        try:
                            # 토큰 유효성 자동 검증 및 갱신
                            await KiwoomService.ensure_valid_token(db, user)
                            logger.info(f"✅ 키움 토큰 검증 완료 (전략: {strategy.strategy_id})")
                        except Exception as token_error:
                            logger.error(f"❌ 키움 토큰 갱신 실패: {token_error}")
                            # 토큰 갱신 실패 시 해당 전략은 건너뜀
                            continue

                    # 1. 매도: 조건에 맞는 포지션 매도 (손절, 익절, 최대보유일)
                    await AutoTradingService.check_and_execute_sell_signals(
                        db=db,
                        strategy=strategy
                    )

                    # 2. 매수: 오전 7시에 선정한 종목 매수
                    # 최근 리밸런싱 프리뷰에서 종목 리스트 가져오기
                    log_entry = await AutoTradingService.get_latest_rebalance_preview(
                        db=db,
                        strategy_id=strategy.strategy_id,
                        user_id=strategy.user_id
                    )

                    if log_entry and log_entry.details:
                        selected_stocks = log_entry.details.get("stocks", [])

                        if selected_stocks:
                            bought_count = await AutoTradingExecutor.execute_buy_orders(
                                db=db,
                                strategy=strategy,
                                selected_stocks=selected_stocks
                            )

                            logger.info(
                                f"✅ 전략 {strategy.strategy_id}: "
                                f"{bought_count}개 종목 매수 완료"
                            )
                        else:
                            logger.info(
                                f"⚠️  전략 {strategy.strategy_id}: 매수할 종목이 없습니다."
                            )
                    else:
                        logger.warning(
                            f"⚠️  전략 {strategy.strategy_id}: "
                            f"리밸런싱 프리뷰를 찾을 수 없습니다. (오전 7시 작업 실패 가능성)"
                        )

                    # 전략 최종 실행 시간 업데이트
                    strategy.last_executed_at = datetime.now()
                    await db.commit()

                except Exception as e:
                    logger.error(
                        f"❌ 전략 {strategy.strategy_id} 매매 실행 실패: {e}",
                        exc_info=True
                    )
                    await db.rollback()

            logger.info("\n" + "=" * 80)
            logger.info("✅ 오전 9시 매매 실행 완료")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 매매 실행 작업 실패: {e}", exc_info=True)


def start_scheduler():
    """
    자동매매 스케줄러 시작
    """
    global scheduler

    if scheduler is not None:
        logger.warning("⚠️  스케줄러가 이미 실행 중입니다.")
        return

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 오전 7시: 종목 선정 (월~금)
    scheduler.add_job(
        select_stocks_for_active_strategies,
        trigger=CronTrigger(
            day_of_week="mon-fri",  # 월~금
            hour=7,
            minute=0,
            timezone="Asia/Seoul"
        ),
        id="select_stocks_7am",
        name="오전 7시 종목 선정",
        replace_existing=True
    )

    # 오전 9시: 매수/매도 실행 (월~금)
    scheduler.add_job(
        execute_trades_for_active_strategies,
        trigger=CronTrigger(
            day_of_week="mon-fri",  # 월~금
            hour=9,
            minute=0,
            timezone="Asia/Seoul"
        ),
        id="execute_trades_9am",
        name="오전 9시 매매 실행",
        replace_existing=True
    )

    if settings.ENABLE_CACHE_WARMING:
        # 새벽 3시: 캐시 워밍 (매일)
        scheduler.add_job(
            run_cache_warming_job,
            trigger=CronTrigger(
                hour=3,
                minute=0,
                timezone="Asia/Seoul"
            ),
            id="cache_warming_3am",
            name="새벽 3시 캐시 워밍",
            replace_existing=True
        )

    scheduler.start()

    logger.info("=" * 80)
    logger.info("🚀 자동매매 스케줄러 시작")
    logger.info("   - 오전 7시: 종목 선정 (월~금)")
    logger.info("   - 오전 9시: 매수/매도 실행 (월~금)")
    if settings.ENABLE_CACHE_WARMING:
        logger.info("   - 새벽 3시: 캐시 워밍 (매일)")
    logger.info("=" * 80)


def stop_scheduler():
    """
    자동매매 스케줄러 종료
    """
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("⏹️  자동매매 스케줄러 종료")


def get_scheduler_status():
    """
    스케줄러 상태 조회
    """
    if scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time.isoformat() if job.next_run_time else None
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": next_run,
        })

    return {
        "running": scheduler.running,
        "jobs": jobs
    }


# ==================== 캐시 워밍 스케줄러 추가 ====================

async def run_cache_warming_job():
    """
    캐시 워밍 작업 (매일 새벽 3시 실행)
    """
    if not settings.ENABLE_CACHE_WARMING:
        logger.info("⏸️  Cache warming job skipped (disabled)")
        return
    from app.services.cache_warmer import run_cache_warming
    await run_cache_warming()
