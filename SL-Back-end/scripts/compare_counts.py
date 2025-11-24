#!/usr/bin/env python3
"""
종목 수 비교 스크립트
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


async def compare_counts():
    """종목 수 비교"""
    async with AsyncSessionLocal() as session:
        try:
            # companies 테이블 종목 수
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT stock_code) as count
                FROM companies
            """))
            companies_count = result.scalar()

            # stock_universe_history 테이블 종목 수 (2025-11-13)
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT stock_code) as count
                FROM stock_universe_history
                WHERE trade_date = '2025-11-13'
            """))
            universe_count = result.scalar()

            # stock_prices 테이블 종목 수 (2025-11-13)
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT company_id) as count
                FROM stock_prices
                WHERE trade_date = '2025-11-13'
                  AND market_cap IS NOT NULL
                  AND market_cap > 0
            """))
            stock_prices_count = result.scalar()

            # 산업이 설정된 종목 수
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT stock_code) as count
                FROM companies
                WHERE industry IS NOT NULL
                  AND industry != ''
            """))
            with_industry_count = result.scalar()

            logger.info("=" * 80)
            logger.info("종목 수 비교")
            logger.info("=" * 80)
            logger.info(f"companies 테이블 (전체):                 {companies_count:>6}개")
            logger.info(f"companies 테이블 (산업 설정됨):           {with_industry_count:>6}개")
            logger.info(f"stock_prices (2025-11-13, 시총 있음):   {stock_prices_count:>6}개")
            logger.info(f"stock_universe_history (2025-11-13):    {universe_count:>6}개")
            logger.info("=" * 80)
            logger.info(f"\n💡 차이 분석:")
            logger.info(f"   - Universe vs Companies: {universe_count - companies_count:+}개")
            logger.info(f"   - Universe vs Industry:  {universe_count - with_industry_count:+}개")

            # 어느 테이블에만 있는 종목 확인
            result = await session.execute(text("""
                SELECT 'Universe에만 존재' as category, COUNT(*) as count
                FROM (
                    SELECT stock_code FROM stock_universe_history WHERE trade_date = '2025-11-13'
                    EXCEPT
                    SELECT stock_code FROM companies
                ) t
                UNION ALL
                SELECT 'Companies에만 존재' as category, COUNT(*) as count
                FROM (
                    SELECT stock_code FROM companies
                    EXCEPT
                    SELECT stock_code FROM stock_universe_history WHERE trade_date = '2025-11-13'
                ) t
            """))
            diff_rows = result.all()

            logger.info("\n종목 차이:")
            logger.info("-" * 80)
            for row in diff_rows:
                logger.info(f"  {row.category}: {row.count}개")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 비교 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(compare_counts())
