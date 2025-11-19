"""
Redis 캐시 사전 로딩 스크립트 - 최소 필드만 조회
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal
from app.core.cache import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def warm_up_company_info(db):
    """전체 종목 정보 캐시"""
    logger.info("=== 종목 정보 캐시 시작 ===")

    result = await db.execute(text("""
        SELECT company_id, stock_code, company_name, market_type, industry
        FROM companies
        WHERE stock_code IS NOT NULL
    """))
    companies = result.fetchall()

    for company in companies:
        cache_key = f"quant:company:{company[1]}"
        await cache.set(cache_key, {
            "company_id": company[0],
            "stock_code": company[1],
            "company_name": company[2],
            "market": company[3],
            "industry": company[4],
        }, ttl=0)

    logger.info(f"✅ {len(companies)}개 종목 정보 캐시 완료")
    return len(companies)


async def warm_up_stock_prices(db, days: int = 1095):
    """전체 종목 시세 데이터 캐시"""
    logger.info(f"=== 최근 {days}일 시세 데이터 캐시 시작 ===")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(text("""
        SELECT company_id, stock_code
        FROM companies
        WHERE stock_code IS NOT NULL
    """))
    companies = result.fetchall()

    total = len(companies)
    cached_count = 0

    for i, company in enumerate(companies, 1):
        company_id, stock_code = company[0], company[1]

        result = await db.execute(text("""
            SELECT trade_date, open_price, high_price, low_price, close_price, volume, market_cap
            FROM stock_prices
            WHERE company_id = :company_id
            AND trade_date >= :start_date
            AND trade_date <= :end_date
            ORDER BY trade_date DESC
        """), {"company_id": company_id, "start_date": start_date, "end_date": end_date})
        prices = result.fetchall()

        if prices:
            cache_key = f"quant:stock_price:{stock_code}:{start_date}:{end_date}"
            data_list = [
                {
                    "date": str(p[0]),
                    "open": p[1],
                    "high": p[2],
                    "low": p[3],
                    "close": p[4],
                    "volume": p[5],
                    "market_cap": p[6],
                }
                for p in prices
            ]
            await cache.set(cache_key, data_list, ttl=0)
            cached_count += 1

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%) - 캐시됨: {cached_count}")

    logger.info(f"✅ {total}개 종목 중 {cached_count}개 시세 캐시 완료")
    return cached_count


async def warm_up_financial_statements(db):
    """전체 종목 재무제표 캐시"""
    logger.info("=== 재무제표 데이터 캐시 시작 ===")

    result = await db.execute(text("""
        SELECT company_id, stock_code
        FROM companies
        WHERE stock_code IS NOT NULL
    """))
    companies = result.fetchall()

    total = len(companies)
    cached_count = 0

    for i, company in enumerate(companies, 1):
        company_id, stock_code = company[0], company[1]

        # 재무제표 메타 조회
        result = await db.execute(text("""
            SELECT stmt_id, bsns_year, reprt_code, fs_div
            FROM financial_statements
            WHERE company_id = :company_id
            ORDER BY bsns_year DESC, reprt_code DESC
            LIMIT 8
        """), {"company_id": company_id})
        statements = result.fetchall()

        if statements:
            cache_key = f"quant:financial_statements:{stock_code}"
            data_list = []

            for stmt in statements:
                stmt_id = stmt[0]
                stmt_data = {
                    "stmt_id": stmt_id,
                    "bsns_year": stmt[1],
                    "reprt_code": stmt[2],
                    "fs_div": stmt[3],
                }

                # 재무상태표
                bs_result = await db.execute(text("""
                    SELECT account_nm, thstrm_amount, frmtrm_amount
                    FROM balance_sheets
                    WHERE stmt_id = :stmt_id
                    ORDER BY ord
                """), {"stmt_id": stmt_id})
                stmt_data["balance_sheets"] = [
                    {"account_nm": r[0], "thstrm_amount": r[1], "frmtrm_amount": r[2]}
                    for r in bs_result.fetchall()
                ]

                # 손익계산서
                is_result = await db.execute(text("""
                    SELECT account_nm, thstrm_amount, frmtrm_amount
                    FROM income_statements
                    WHERE stmt_id = :stmt_id
                    ORDER BY ord
                """), {"stmt_id": stmt_id})
                stmt_data["income_statements"] = [
                    {"account_nm": r[0], "thstrm_amount": r[1], "frmtrm_amount": r[2]}
                    for r in is_result.fetchall()
                ]

                # 현금흐름표
                cf_result = await db.execute(text("""
                    SELECT account_nm, thstrm_amount, frmtrm_amount
                    FROM cashflow_statements
                    WHERE stmt_id = :stmt_id
                    ORDER BY ord
                """), {"stmt_id": stmt_id})
                stmt_data["cashflow_statements"] = [
                    {"account_nm": r[0], "thstrm_amount": r[1], "frmtrm_amount": r[2]}
                    for r in cf_result.fetchall()
                ]

                data_list.append(stmt_data)

            await cache.set(cache_key, data_list, ttl=0)
            cached_count += 1

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%) - 캐시됨: {cached_count}")

    logger.info(f"✅ {total}개 종목 중 {cached_count}개 재무제표 캐시 완료")
    return cached_count


async def main():
    """전체 캐시 워밍업 실행"""
    logger.info("========================================")
    logger.info("Redis 캐시 사전 로딩 시작")
    logger.info("========================================")

    await cache.initialize()

    async with AsyncSessionLocal() as db:
        try:
            # 1. 종목 정보
            company_count = await warm_up_company_info(db)

            # 2. 시세 데이터 (최근 3년)
            price_count = await warm_up_stock_prices(db, days=1095)

            # 3. 재무제표
            financial_count = await warm_up_financial_statements(db)

            # 캐시 통계 출력
            stats = await cache.get_cache_stats()
            logger.info("========================================")
            logger.info("캐시 완료:")
            logger.info(f"  종목 정보: {company_count}개")
            logger.info(f"  시세 데이터: {price_count}개")
            logger.info(f"  재무제표: {financial_count}개")
            logger.info("Redis 통계:")
            logger.info(f"  사용 메모리: {stats.get('used_memory_human', 'N/A')}")
            logger.info(f"  최대 메모리: {stats.get('used_memory_peak_human', 'N/A')}")
            logger.info(f"  히트율: {stats.get('hit_ratio', 0)*100:.2f}%")
            logger.info("========================================")

        except Exception as e:
            logger.error(f"캐시 로딩 실패: {e}", exc_info=True)
        finally:
            await cache.close()


if __name__ == "__main__":
    asyncio.run(main())
