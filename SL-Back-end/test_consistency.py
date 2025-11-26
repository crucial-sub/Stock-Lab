#!/usr/bin/env python3
"""
동일성 검증 테스트 - 동일 조건 백테스트 2회 실행 후 결과 비교
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


async def run_backtest_once(run_number: int):
    """백테스트 1회 실행"""

    # 2개월 기간 (2024-09-01 ~ 2024-10-31)
    start_date = datetime.strptime("20240901", "%Y%m%d").date()
    end_date = datetime.strptime("20241031", "%Y%m%d").date()

    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 백테스트 실행 #{run_number}")
    logger.info(f"   기간: {start_date} ~ {end_date}")
    logger.info(f"{'='*60}")

    start_time = time.time()
    backtest_id = uuid4()

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)
        # DB 저장 비활성화 (테스트용)
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

    elapsed = time.time() - start_time

    # statistics에서 성과 지표 추출
    stats = result.statistics if result else None
    return {
        "run_number": run_number,
        "elapsed": elapsed,
        "total_return": float(stats.get('total_return', 0)) if stats else None,
        "annual_return": float(stats.get('annualized_return', 0)) if stats else None,
        "max_drawdown": float(stats.get('max_drawdown', 0)) if stats else None,
        "sharpe_ratio": float(stats.get('sharpe_ratio', 0)) if stats else None,
        "win_rate": float(stats.get('win_rate', 0)) if stats else None,
        "total_trades": int(stats.get('total_trades', 0)) if stats else None,
        "final_value": float(stats.get('final_capital', 0)) if stats else None,
    }


async def run_consistency_test():
    """동일성 검증 테스트"""

    logger.info("\n" + "="*80)
    logger.info("🎯 동일성 검증 테스트 시작")
    logger.info("   동일 조건으로 백테스트를 2회 실행하여 결과 일치 여부 확인")
    logger.info("="*80 + "\n")

    # 1회차 실행
    result1 = await run_backtest_once(1)
    logger.info(f"✅ 1회차 완료: {result1['elapsed']:.2f}초")

    # 2회차 실행
    result2 = await run_backtest_once(2)
    logger.info(f"✅ 2회차 완료: {result2['elapsed']:.2f}초")

    # 결과 비교
    logger.info("\n" + "="*80)
    logger.info("📊 결과 비교")
    logger.info("="*80)

    metrics = ["total_return", "annual_return", "max_drawdown", "sharpe_ratio", "win_rate", "total_trades", "final_value"]

    all_match = True
    for metric in metrics:
        v1 = result1[metric]
        v2 = result2[metric]

        # 소수점 정밀도 차이 허용 (1e-6 이하)
        if v1 is None or v2 is None:
            match = v1 == v2
        elif isinstance(v1, float):
            match = abs(v1 - v2) < 1e-6
        else:
            match = v1 == v2

        status = "✅" if match else "❌"
        if not match:
            all_match = False

        logger.info(f"   {status} {metric}: {v1} vs {v2}")

    logger.info("\n" + "="*80)
    if all_match:
        logger.info("🎉 동일성 검증 성공! 모든 지표가 일치합니다.")
    else:
        logger.error("⚠️ 동일성 검증 실패! 일부 지표가 다릅니다.")
    logger.info("="*80)

    return all_match


if __name__ == "__main__":
    asyncio.run(run_consistency_test())
