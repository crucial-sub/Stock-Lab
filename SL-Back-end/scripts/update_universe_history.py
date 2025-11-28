#!/usr/bin/env python3
"""
일일 배치: stock_universe_history 테이블 업데이트
- 매일 밤 실행하여 최신 거래일의 유니버스 분류 업데이트
- cron: 0 22 * * * (매일 밤 10시)
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_universe_history(session: AsyncSession) -> dict:
    """
    최신 거래일의 유니버스 분류 업데이트

    Returns:
        결과 통계
    """
    try:
        # 최신 거래일 조회
        result = await session.execute(
            text("SELECT MAX(trade_date) FROM stock_prices WHERE market_cap IS NOT NULL")
        )
        latest_date = result.scalar_one_or_none()

        if not latest_date:
            logger.warning("시가총액 데이터가 있는 거래일이 없습니다.")
            return {"status": "skipped", "reason": "no data"}

        logger.info(f"최신 거래일: {latest_date}")

        # 유니버스 히스토리 삽입/업데이트
        insert_sql = text("""
            INSERT INTO stock_universe_history (stock_code, trade_date, universe_id, market_cap, market_type)
            SELECT
                c.stock_code,
                sp.trade_date,
                CASE
                    -- KOSPI 분류 (stock_code < 400000)
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer < 400000 AND sp.market_cap >= 10000000000000 THEN 'KOSPI_MEGA'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer < 400000 AND sp.market_cap >= 2000000000000 THEN 'KOSPI_LARGE'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer < 400000 AND sp.market_cap >= 500000000000 THEN 'KOSPI_MID'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer < 400000 AND sp.market_cap > 0 THEN 'KOSPI_SMALL'

                    -- KOSDAQ 분류 (stock_code >= 400000)
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer >= 400000 AND sp.market_cap >= 2000000000000 THEN 'KOSDAQ_MEGA'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer >= 400000 AND sp.market_cap >= 500000000000 THEN 'KOSDAQ_LARGE'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer >= 400000 AND sp.market_cap >= 200000000000 THEN 'KOSDAQ_MID'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer >= 400000 AND sp.market_cap > 0 THEN 'KOSDAQ_SMALL'

                    ELSE NULL
                END as universe_id,
                sp.market_cap,
                CASE
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer < 400000 THEN 'KOSPI'
                    WHEN c.stock_code ~ '^[0-9]{6}$' AND c.stock_code::integer >= 400000 THEN 'KOSDAQ'
                    ELSE NULL
                END as market_type
            FROM companies c
            INNER JOIN stock_prices sp ON c.company_id = sp.company_id
            WHERE sp.trade_date = :trade_date
              AND sp.market_cap IS NOT NULL
              AND sp.market_cap > 0
              AND c.stock_code ~ '^[0-9]{6}$'
            ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                universe_id = EXCLUDED.universe_id,
                market_cap = EXCLUDED.market_cap,
                market_type = EXCLUDED.market_type
        """)

        result = await session.execute(insert_sql, {"trade_date": latest_date})
        await session.commit()

        rows_affected = result.rowcount
        logger.info(f"✅ {rows_affected}개 레코드 삽입/업데이트 완료")

        # 결과 통계 조회
        stats_sql = text("""
            SELECT
                universe_id,
                COUNT(*) as stock_count
            FROM stock_universe_history
            WHERE trade_date = :trade_date
            GROUP BY universe_id
            ORDER BY universe_id
        """)

        result = await session.execute(stats_sql, {"trade_date": latest_date})
        stats = result.all()

        stats_dict = {row.universe_id: row.stock_count for row in stats}
        logger.info(f"📊 유니버스별 종목 수: {stats_dict}")

        return {
            "status": "success",
            "trade_date": latest_date.strftime("%Y-%m-%d"),
            "rows_affected": rows_affected,
            "stats": stats_dict
        }

    except Exception as e:
        logger.error(f"❌ 업데이트 실패: {e}", exc_info=True)
        await session.rollback()
        return {"status": "error", "error": str(e)}


async def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("stock_universe_history 일일 배치 시작")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as session:
        result = await update_universe_history(session)

    logger.info("=" * 60)
    logger.info(f"배치 결과: {result['status']}")
    if result['status'] == 'success':
        logger.info(f"거래일: {result['trade_date']}")
        logger.info(f"처리 건수: {result['rows_affected']}")
    logger.info("=" * 60)

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result['status'] == 'success' else 1)
