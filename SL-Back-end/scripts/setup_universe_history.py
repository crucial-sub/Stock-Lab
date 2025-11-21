#!/usr/bin/env python3
"""
stock_universe_history 테이블 초기 설정 스크립트
AWS RDS에 테이블 생성 및 데이터 채우기
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


async def setup_universe_history():
    """테이블 생성 및 초기 데이터 채우기"""

    async with AsyncSessionLocal() as session:
        try:
            # 1단계: 테이블 생성
            logger.info("=" * 60)
            logger.info("1단계: stock_universe_history 테이블 생성")
            logger.info("=" * 60)

            # 테이블 생성
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_universe_history (
                    stock_code VARCHAR(20) NOT NULL,
                    trade_date DATE NOT NULL,
                    universe_id VARCHAR(20) NOT NULL,
                    market_cap BIGINT,
                    market_type VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (stock_code, trade_date)
                )
            """))

            # 인덱스 생성 (각각 개별 실행)
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_suh_trade_date ON stock_universe_history(trade_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_suh_universe_date ON stock_universe_history(universe_id, trade_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_suh_market_type ON stock_universe_history(market_type, trade_date)"))

            await session.commit()
            logger.info("✅ 테이블 및 인덱스 생성 완료")

            # 2단계: 초기 데이터 채우기
            logger.info("=" * 60)
            logger.info("2단계: 초기 데이터 채우기 (시간이 걸릴 수 있습니다...)")
            logger.info("=" * 60)

            populate_sql = text("""
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
                WHERE sp.market_cap IS NOT NULL
                  AND sp.market_cap > 0
                  AND c.stock_code ~ '^[0-9]{6}$'
                ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                    universe_id = EXCLUDED.universe_id,
                    market_cap = EXCLUDED.market_cap,
                    market_type = EXCLUDED.market_type
            """)

            result = await session.execute(populate_sql)
            await session.commit()
            rows_inserted = result.rowcount
            logger.info(f"✅ {rows_inserted}개 레코드 삽입 완료")

            # 3단계: 결과 검증
            logger.info("=" * 60)
            logger.info("3단계: 데이터 검증")
            logger.info("=" * 60)

            # 총 레코드 수
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM stock_universe_history")
            )
            total_count = count_result.scalar()
            logger.info(f"총 레코드 수: {total_count:,}")

            # 최신 날짜 확인
            date_result = await session.execute(
                text("SELECT MAX(trade_date) FROM stock_universe_history")
            )
            latest_date = date_result.scalar()
            logger.info(f"최신 거래일: {latest_date}")

            # 유니버스별 종목 수 (최신 날짜 기준)
            stats_result = await session.execute(
                text("""
                    SELECT universe_id, COUNT(*) as stock_count
                    FROM stock_universe_history
                    WHERE trade_date = :trade_date
                    GROUP BY universe_id
                    ORDER BY universe_id
                """),
                {"trade_date": latest_date}
            )
            stats = stats_result.all()

            logger.info("유니버스별 종목 수 (최신 날짜):")
            for row in stats:
                logger.info(f"  - {row.universe_id}: {row.stock_count}개")

            logger.info("=" * 60)
            logger.info("🎉 설치 완료!")
            logger.info("=" * 60)

            return {
                "status": "success",
                "total_records": total_count,
                "latest_date": str(latest_date),
                "stats": {row.universe_id: row.stock_count for row in stats}
            }

        except Exception as e:
            logger.error(f"❌ 설치 실패: {e}", exc_info=True)
            await session.rollback()
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    result = asyncio.run(setup_universe_history())
    exit(0 if result["status"] == "success" else 1)
