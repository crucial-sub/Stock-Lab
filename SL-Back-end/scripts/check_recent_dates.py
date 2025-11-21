#!/usr/bin/env python3
"""
최근 날짜별 종목 수 확인 스크립트
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


async def check_recent_dates():
    """최근 날짜별 종목 수 확인"""
    async with AsyncSessionLocal() as session:
        try:
            # 최근 10개 거래일의 종목 수
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    COUNT(*) as stock_count,
                    COUNT(DISTINCT universe_id) as universe_count
                FROM stock_universe_history
                GROUP BY trade_date
                ORDER BY trade_date DESC
                LIMIT 10
            """))
            rows = result.all()

            logger.info("=" * 80)
            logger.info("최근 10개 거래일의 종목 수")
            logger.info("=" * 80)
            logger.info(f"{'날짜':<15} {'종목 수':<15} {'유니버스 수':<15}")
            logger.info("-" * 80)
            for row in rows:
                logger.info(f"{str(row.trade_date):<15} {row.stock_count:<15} {row.universe_count:<15}")
            logger.info("=" * 80)

            # 최신 날짜의 유니버스별 상세 현황
            if rows:
                latest_date = rows[0].trade_date
                detail_result = await session.execute(text("""
                    SELECT
                        universe_id,
                        COUNT(*) as stock_count,
                        MIN(market_cap) as min_cap,
                        MAX(market_cap) as max_cap
                    FROM stock_universe_history
                    WHERE trade_date = :trade_date
                    GROUP BY universe_id
                    ORDER BY universe_id
                """), {"trade_date": latest_date})
                detail_rows = detail_result.all()

                logger.info(f"\n최신 거래일 ({latest_date}) 유니버스별 상세")
                logger.info("=" * 80)
                logger.info(f"{'유니버스':<20} {'종목 수':<15} {'최소 시총':<20} {'최대 시총':<20}")
                logger.info("-" * 80)
                for row in detail_rows:
                    min_cap = f"{row.min_cap:,}" if row.min_cap else "N/A"
                    max_cap = f"{row.max_cap:,}" if row.max_cap else "N/A"
                    logger.info(f"{row.universe_id:<20} {row.stock_count:<15} {min_cap:<20} {max_cap:<20}")
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 확인 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(check_recent_dates())
