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
from app.models.balance_sheet import BalanceSheet
from app.models.income_statement import IncomeStatement
from app.models.cashflow_statement import CashflowStatement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def warm_up_company_info(db):
    """전체 종목 정보 캐시"""
    logger.info("=== 종목 정보 캐시 시작 ===")

    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

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


async def warm_up_stock_prices(db, days: int = 365):
    """전체 종목 시세 데이터 캐시"""
    logger.info(f"=== 최근 {days}일 시세 데이터 캐시 시작 ===")

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

    total = len(companies)
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

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%)")

    logger.info(f"✅ {total}개 종목 시세 캐시 완료")
    return total


async def warm_up_balance_sheets(db):
    """전체 종목 재무상태표 캐시"""
    logger.info("=== 재무상태표 데이터 캐시 시작 ===")

    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

    total = len(companies)
    for i, company in enumerate(companies, 1):
        result = await db.execute(
            select(BalanceSheet)
            .where(BalanceSheet.company_id == company.company_id)
            .order_by(BalanceSheet.created_at.desc())
            .limit(8)  # 최근 8분기
        )
        balance_sheets = result.scalars().all()

        if balance_sheets:
            cache_key = f"quant:balance_sheet:{company.stock_code}"
            data_list = [
                {
                    "account_nm": bs.account_nm,
                    "thstrm_amount": bs.thstrm_amount,
                    "frmtrm_amount": bs.frmtrm_amount,
                }
                for bs in balance_sheets
            ]
            await cache.set(cache_key, data_list, ttl=0)

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%)")

    logger.info(f"✅ {total}개 종목 재무상태표 캐시 완료")
    return total


async def warm_up_income_statements(db):
    """전체 종목 손익계산서 캐시"""
    logger.info("=== 손익계산서 데이터 캐시 시작 ===")

    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

    total = len(companies)
    for i, company in enumerate(companies, 1):
        result = await db.execute(
            select(IncomeStatement)
            .where(IncomeStatement.company_id == company.company_id)
            .order_by(IncomeStatement.created_at.desc())
            .limit(8)
        )
        income_statements = result.scalars().all()

        if income_statements:
            cache_key = f"quant:income_statement:{company.stock_code}"
            data_list = [
                {
                    "account_nm": ins.account_nm,
                    "thstrm_amount": ins.thstrm_amount,
                    "frmtrm_amount": ins.frmtrm_amount,
                }
                for ins in income_statements
            ]
            await cache.set(cache_key, data_list, ttl=0)

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%)")

    logger.info(f"✅ {total}개 종목 손익계산서 캐시 완료")
    return total


async def warm_up_cashflow_statements(db):
    """전체 종목 현금흐름표 캐시"""
    logger.info("=== 현금흐름표 데이터 캐시 시작 ===")

    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

    total = len(companies)
    for i, company in enumerate(companies, 1):
        result = await db.execute(
            select(CashflowStatement)
            .where(CashflowStatement.company_id == company.company_id)
            .order_by(CashflowStatement.created_at.desc())
            .limit(8)
        )
        cashflow_statements = result.scalars().all()

        if cashflow_statements:
            cache_key = f"quant:cashflow_statement:{company.stock_code}"
            data_list = [
                {
                    "account_nm": cf.account_nm,
                    "thstrm_amount": cf.thstrm_amount,
                    "frmtrm_amount": cf.frmtrm_amount,
                }
                for cf in cashflow_statements
            ]
            await cache.set(cache_key, data_list, ttl=0)

        if i % 100 == 0:
            logger.info(f"진행: {i}/{total} ({i/total*100:.1f}%)")

    logger.info(f"✅ {total}개 종목 현금흐름표 캐시 완료")
    return total


async def main():
    """전체 캐시 워밍업 실행"""
    logger.info("========================================")
    logger.info("Redis 캐시 사전 로딩 시작")
    logger.info("========================================")

    await cache.initialize()

    async with AsyncSessionLocal() as db:
        try:
            # 1. 종목 정보
            await warm_up_company_info(db)

            # 2. 시세 데이터 (최근 3년)
            await warm_up_stock_prices(db, days=1095)

            # 3. 재무상태표
            await warm_up_balance_sheets(db)

            # 4. 손익계산서
            await warm_up_income_statements(db)

            # 5. 현금흐름표
            await warm_up_cashflow_statements(db)

            # 캐시 통계 출력
            stats = await cache.get_cache_stats()
            logger.info("========================================")
            logger.info("캐시 통계:")
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
