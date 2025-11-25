#!/usr/bin/env python3
"""
빠른 성능 테스트 - 2개월 기간
"""

import asyncio
import time
import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, '/Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end')

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine


async def run_quick_test():
    """2개월 백테스트 성능 테스트"""

    # 2개월 기간 (2024-09-01 ~ 2024-10-31)
    start_date = datetime.strptime("20240901", "%Y%m%d").date()
    end_date = datetime.strptime("20241031", "%Y%m%d").date()

    logger.info("="*60)
    logger.info("🚀 백테스트 성능 테스트 시작")
    logger.info(f"   기간: {start_date} ~ {end_date} (2개월)")
    logger.info("="*60)

    total_start = time.time()

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)

        result = await engine.run_backtest(
            backtest_id=uuid4(),
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
    logger.info(f"⚡ 총 실행 시간: {total_elapsed:.2f}초")
    logger.info("="*60)

    if result:
        logger.info(f"📊 총 수익률: {result.total_return:.2f}%")
        logger.info(f"📊 총 거래 수: {result.total_trades}")

    # 20초 목표 달성 여부
    if total_elapsed <= 20:
        logger.info("✅ 목표 달성: 20초 이내 완료!")
    else:
        logger.warning(f"⚠️ 목표 미달: {total_elapsed:.2f}초 > 20초")

    return total_elapsed


if __name__ == "__main__":
    asyncio.run(run_quick_test())
