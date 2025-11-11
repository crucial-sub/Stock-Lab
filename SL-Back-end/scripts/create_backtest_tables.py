#!/usr/bin/env python3
"""
백테스트 테이블 생성 스크립트
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models.backtest import (
    BacktestSession, BacktestCondition, BacktestStatistics,
    BacktestDailySnapshot, BacktestTrade, BacktestHolding
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """백테스트 관련 테이블 생성"""
    try:
        # 모든 모델을 임포트하여 Base.metadata에 등록
        logger.info("Creating backtest tables...")

        async with engine.begin() as conn:
            # 테이블 생성
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Successfully created all backtest tables!")
        logger.info("Created tables:")
        logger.info("  - backtest_sessions")
        logger.info("  - backtest_conditions")
        logger.info("  - backtest_statistics")
        logger.info("  - backtest_daily_snapshots")
        logger.info("  - backtest_trades")
        logger.info("  - backtest_holdings")

    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())