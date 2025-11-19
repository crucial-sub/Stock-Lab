"""
Redis 캐시 사전 로딩 스크립트
전체 종목의 시세/재무 데이터를 캐시에 등록
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.cache import cache
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def warm_up_company_info(db):
    """전체 종목 정보 캐시"""
    logger.info("=== 종목 정보 캐시 시작 ===")

    result = await db.execute(
        select(
            Company.company_id,
            Company.stock_code,
            Company.company_name,
            Company.market_type,
            Company.industry
        ).where(Company.stock_code.isnot(None))
    )
    companies = result.all()

    for company in companies:
        cache_key = f"quant:company:{company.stock_code}"
        await cache.set(cache_key, {
            "company_id": company.company_id,
            "stock_code": company.stock_code,
            "company_name": company.company_name,
            "market": company.market_type,
            "industry": company.industry,
        }, ttl=0)

    logger.info(f"✅ {len(companies)}개 종목 정보 캐시 완료")
    return len(companies)


async def warm_up_stock_prices(db, days: int = 1095):
    """전체 종목 시세 데이터 캐시"""
    logger.info(f"=== 최근 {days}일 시세 데이터 캐시 시작 ===")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(Company).where(Company.stock_code.isnot(None))
    )
    companies = result.scalars().all()

    total = len(companies)
    cached_count = 0

    for i, company in enumerate(companies, 1):
        result = await db.execute(
            select(StockPrice)
            .where(
                StockPrice.company_id == company.company_id,
                StockPrice.trade_date >= start_date,
                StockPrice.trade_date <= end_date
            )
            .order_by(StockPrice.trade_date.desc())
        )
        prices = result.scalars().all()

        if prices:
            cache_key = f"quant:stock_price:{company.stock_code}:{start_date}:{end_date}"
            data_list = [
                {
                    "date": str(p.trade_date),
                    "open": p.open_price,
                    "high": p.high_price,
                    "low": p.low_price,
                    "close": p.close_price,
                    "volume": p.volume,
                    "market_cap": p.market_cap,
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

    result = await db.execute(
        select(Company).where(Company.stock_code.isnot(None))
    )
    companies = result.scalars().all()

    total = len(companies)
    cached_count = 0

    for i, company in enumerate(companies, 1):
        # 해당 기업의 재무제표 조회 (최근 8개)
        result = await db.execute(
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.company_id)
            .order_by(
                FinancialStatement.bsns_year.desc(),
                FinancialStatement.reprt_code.desc()
            )
            .limit(8)
        )
        statements = result.scalars().all()

        if statements:
            cache_key = f"quant:financial_statements:{company.stock_code}"
            data_list = []

            for stmt in statements:
                stmt_data = {
                    "stmt_id": stmt.stmt_id,
                    "bsns_year": stmt.bsns_year,
                    "reprt_code": stmt.reprt_code,
                    "fs_div": stmt.fs_div,
                }

                # 재무상태표 데이터
                if stmt.balance_sheets:
                    stmt_data["balance_sheets"] = [
                        {
                            "account_nm": bs.account_nm,
                            "thstrm_amount": bs.thstrm_amount,
                            "frmtrm_amount": bs.frmtrm_amount,
                        }
                        for bs in stmt.balance_sheets
                    ]

                # 손익계산서 데이터
                if stmt.income_statements:
                    stmt_data["income_statements"] = [
                        {
                            "account_nm": ins.account_nm,
                            "thstrm_amount": ins.thstrm_amount,
                            "frmtrm_amount": ins.frmtrm_amount,
                        }
                        for ins in stmt.income_statements
                    ]

                # 현금흐름표 데이터
                if stmt.cashflow_statements:
                    stmt_data["cashflow_statements"] = [
                        {
                            "account_nm": cf.account_nm,
                            "thstrm_amount": cf.thstrm_amount,
                            "frmtrm_amount": cf.frmtrm_amount,
                        }
                        for cf in stmt.cashflow_statements
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

            # 3. 재무제표 (3개 통합)
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
