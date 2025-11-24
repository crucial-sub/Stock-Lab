#!/usr/bin/env python3
"""
stock_prices의 최근 날짜별 데이터 확인
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


async def check_stock_prices_dates():
    """stock_prices 최근 날짜별 데이터 확인"""
    async with AsyncSessionLocal() as session:
        try:
            # 2025-11-13 이후의 거래일별 종목 수
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN market_cap IS NOT NULL AND market_cap > 0 THEN 1 END) as with_market_cap,
                    COUNT(DISTINCT company_id) as unique_companies
                FROM stock_prices
                WHERE trade_date >= '2025-11-13'
                GROUP BY trade_date
                ORDER BY trade_date DESC
            """))
            rows = result.all()

            logger.info("=" * 100)
            logger.info("stock_prices 테이블 - 2025-11-13 이후 거래일별 데이터")
            logger.info("=" * 100)
            logger.info(f"{'날짜':<15} {'전체 레코드':<15} {'시총 데이터 있음':<20} {'유니크 종목 수':<20}")
            logger.info("-" * 100)
            for row in rows:
                logger.info(f"{str(row.trade_date):<15} {row.total_records:<15} {row.with_market_cap:<20} {row.unique_companies:<20}")
            logger.info("=" * 100)

        except Exception as e:
            logger.error(f"❌ 확인 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(check_stock_prices_dates())
