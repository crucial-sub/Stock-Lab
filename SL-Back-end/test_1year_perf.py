#!/usr/bin/env python3
"""
1년 백테스트 성능 테스트 - 20초 이내 목표
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 불필요한 로그 레벨 조정
logging.getLogger('app.services.factor_integration').setLevel(logging.WARNING)
logging.getLogger('app.services.backtest_websocket').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, '/Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end')

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine


async def run_1year_test():
    """1년 백테스트 성능 테스트"""

    # 1년 기간 (2023-11-01 ~ 2024-10-31)
    start_date = datetime.strptime("20231101", "%Y%m%d").date()
    end_date = datetime.strptime("20241031", "%Y%m%d").date()

    logger.info("="*60)
    logger.info("🚀 1년 백테스트 성능 테스트")
    logger.info(f"   기간: {start_date} ~ {end_date}")
    logger.info("   목표: 20초 이내")
    logger.info("="*60)

    total_start = time.time()
    backtest_id = uuid4()

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)
        # 🚀 테스트 모드: DB 저장 및 WebSocket 전송 스킵
        engine.skip_db_save = True

        result = await engine.run_backtest(
            backtest_id=backtest_id,
            buy_conditions=[
                {"name": "A", "exp_left_side": "기본값({PER})", "inequality": "<", "exp_right_side": 10},
                {"name": "B", "exp_left_side": "기본값({ROE})", "inequality": ">", "exp_right_side": 10}
            ],
            sell_conditions=[],
            start_date=start_date,
            end_date=end_date,
            target_and_loss={"target_gain": 20, "stop_loss": 10},
            hold_days={"min_hold_days": 5, "max_hold_days": 60, "sell_price_basis": "시가", "sell_price_offset": 0},
            initial_capital=Decimal("10000000"),
            rebalance_frequency="DAILY",
            max_positions=10,
            position_sizing="EQUAL_WEIGHT",
            benchmark="KOSPI",
            commission_rate=0.00015,
            slippage=0.001,
            per_stock_ratio=0.1,
            max_daily_stock=3
        )

    total_elapsed = time.time() - total_start

    logger.info("="*60)
    logger.info(f"⏱️ 총 실행 시간: {total_elapsed:.2f}초")
    logger.info("="*60)

    if result and result.statistics:
        stats = result.statistics
        logger.info(f"📊 총 수익률: {stats.total_return:.2f}%")
        logger.info(f"📊 총 거래 수: {stats.total_trades}")

    # 20초 목표 달성 여부
    if total_elapsed <= 20:
        logger.info("🎉 목표 달성: 20초 이내 완료!")
    else:
        logger.warning(f"⚠️ 목표 미달: {total_elapsed:.2f}초 > 20초")
        logger.warning(f"   초과 시간: {total_elapsed - 20:.2f}초")

    return total_elapsed


if __name__ == "__main__":
    asyncio.run(run_1year_test())
