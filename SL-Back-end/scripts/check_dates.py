#!/usr/bin/env python3
"""
날짜 범위 확인 스크립트
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_dates():
    """날짜 범위 확인"""
    async with AsyncSessionLocal() as session:
        try:
            # 히스토리 테이블 날짜 범위
            history_result = await session.execute(text("""
                SELECT
                    MIN(trade_date) as min_date,
                    MAX(trade_date) as max_date,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT trade_date) as unique_dates
                FROM stock_universe_history
            """))
            history_row = history_result.first()

            logger.info("=" * 60)
            logger.info("📊 stock_universe_history 테이블")
            logger.info(f"  - 최소 날짜: {history_row.min_date}")
            logger.info(f"  - 최대 날짜: {history_row.max_date}")
            logger.info(f"  - 총 레코드 수: {history_row.total_records:,}")
            logger.info(f"  - 유니크 날짜 수: {history_row.unique_dates}")

            # stock_prices 날짜 범위
            prices_result = await session.execute(text("""
                SELECT
                    MIN(trade_date) as min_date,
                    MAX(trade_date) as max_date,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT trade_date) as unique_dates
                FROM stock_prices
                WHERE market_cap IS NOT NULL AND market_cap > 0
            """))
            prices_row = prices_result.first()

            logger.info("=" * 60)
            logger.info("📊 stock_prices 테이블 (시총 데이터 있는 것만)")
            logger.info(f"  - 최소 날짜: {prices_row.min_date}")
            logger.info(f"  - 최대 날짜: {prices_row.max_date}")
            logger.info(f"  - 총 레코드 수: {prices_row.total_records:,}")
            logger.info(f"  - 유니크 날짜 수: {prices_row.unique_dates}")

            # 최신 날짜 비교
            if history_row.max_date < prices_row.max_date:
                logger.warning("=" * 60)
                logger.warning("⚠️  히스토리 테이블의 최신 날짜가 stock_prices보다 오래되었습니다!")
                logger.warning(f"  - 히스토리 최신: {history_row.max_date}")
                logger.warning(f"  - stock_prices 최신: {prices_row.max_date}")
                logger.warning(f"  - 차이: {(prices_row.max_date - history_row.max_date).days}일")
                logger.warning("  - update_universe_history.py를 실행하여 업데이트하세요.")
            else:
                logger.info("=" * 60)
                logger.info("✅ 히스토리 테이블이 최신 상태입니다.")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 확인 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(check_dates())
