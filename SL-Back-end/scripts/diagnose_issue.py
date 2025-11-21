#!/usr/bin/env python3
"""
문제 진단 스크립트
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


async def diagnose():
    """문제 진단"""
    async with AsyncSessionLocal() as session:
        try:
            # 최근 거래일들의 종목 수
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    COUNT(*) as stock_count
                FROM stock_prices
                WHERE market_cap IS NOT NULL AND market_cap > 0
                GROUP BY trade_date
                ORDER BY trade_date DESC
                LIMIT 10
            """))
            rows = result.all()

            logger.info("=" * 80)
            logger.info("stock_prices 테이블 - 최근 거래일별 시총 데이터 있는 종목 수")
            logger.info("=" * 80)
            for row in rows:
                marker = " ⚠️ 불완전" if row.stock_count < 2000 else " ✅ 정상"
                logger.info(f"{str(row.trade_date):<15} {row.stock_count:>6}개{marker}")
            logger.info("=" * 80)

            # 추천: 2000개 이상인 가장 최근 날짜
            result = await session.execute(text("""
                SELECT trade_date, COUNT(*) as stock_count
                FROM stock_prices
                WHERE market_cap IS NOT NULL AND market_cap > 0
                GROUP BY trade_date
                HAVING COUNT(*) >= 2000
                ORDER BY trade_date DESC
                LIMIT 1
            """))
            recommended = result.first()

            if recommended:
                logger.info(f"\n💡 권장 사용 날짜: {recommended.trade_date} ({recommended.stock_count}개 종목)")
                logger.info(f"   현재 사용 중: {rows[0].trade_date} ({rows[0].stock_count}개 종목)")
                logger.info(f"   ❌ 차이: {recommended.stock_count - rows[0].stock_count}개 종목이 누락됨")

        except Exception as e:
            logger.error(f"❌ 진단 실패: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(diagnose())
