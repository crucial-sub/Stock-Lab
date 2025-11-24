#!/usr/bin/env python3
"""
산업 정보가 없는 종목 찾기
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


async def find_missing_industry():
    """산업 정보 없는 종목 찾기"""
    async with AsyncSessionLocal() as session:
        try:
            # 유니버스에는 있지만 산업이 NULL인 종목
            result = await session.execute(text("""
                SELECT
                    c.stock_code,
                    c.stock_name,
                    c.industry,
                    suh.universe_id,
                    suh.market_cap,
                    suh.market_type
                FROM stock_universe_history suh
                JOIN companies c ON c.stock_code = suh.stock_code
                WHERE suh.trade_date = '2025-11-13'
                  AND (c.industry IS NULL OR c.industry = '')
                ORDER BY suh.market_cap DESC
                LIMIT 20
            """))
            rows = result.all()

            logger.info("=" * 100)
            logger.info("유니버스에 포함되었지만 산업 정보가 없는 종목 (상위 20개)")
            logger.info("=" * 100)
            logger.info(f"{'종목코드':<10} {'종목명':<25} {'유니버스':<15} {'시가총액 (조)':<15} {'시장':<10}")
            logger.info("-" * 100)

            for row in rows:
                market_cap_trillion = row.market_cap / 1_000_000_000_000
                logger.info(
                    f"{row.stock_code:<10} {row.stock_name:<25} {row.universe_id:<15} "
                    f"{market_cap_trillion:>13.2f}조 {row.market_type:<10}"
                )

            # 총 개수
            count_result = await session.execute(text("""
                SELECT COUNT(*) as count
                FROM stock_universe_history suh
                JOIN companies c ON c.stock_code = suh.stock_code
                WHERE suh.trade_date = '2025-11-13'
                  AND (c.industry IS NULL OR c.industry = '')
            """))
            total_missing = count_result.scalar()

            logger.info("=" * 100)
            logger.info(f"총 산업 정보 없는 종목: {total_missing}개")
            logger.info("=" * 100)

        except Exception as e:
            logger.error(f"❌ 조회 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(find_missing_industry())
