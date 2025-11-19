"""
Redis 캐시 사전 로딩 스크립트
전체 종목의 팩터/시세/재무 데이터를 캐시에 등록
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.cache import cache
from app.models.company import Company
from app.models.market_data import MarketData
from app.models.financial_statement import FinancialStatement
from app.services.factor_calculator_complete_v2 import FactorCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def warm_up_company_info(db: AsyncSession):
    """전체 종목 정보 캐시"""
    logger.info("=== 종목 정보 캐시 시작 ===")

    # 전체 종목 조회
    result = await db.execute(
        select(Company).where(Company.is_active == True)
    )
    companies = result.scalars().all()

    for company in companies:
        cache_key = f"quant:company:{company.stock_code}"
        await cache.set(cache_key, {
            "stock_code": company.stock_code,
            "company_name": company.company_name,
            "market": company.market,
            "sector": company.sector,
            "industry": company.industry
        }, ttl=0)  # 영구 캐싱

    logger.info(f"✅ {len(companies)}개 종목 정보 캐시 완료")


async def warm_up_market_data(db: AsyncSession, days: int = 365):
    """전체 종목 시세 데이터 캐시"""
    logger.info(f"=== 최근 {days}일 시세 데이터 캐시 시작 ===")

    # 기준일 계산
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # 활성 종목 조회
    result = await db.execute(
        select(Company.stock_code).where(Company.is_active == True)
    )
    stock_codes = [row[0] for row in result.all()]

    # 종목별 시세 데이터 캐싱
    for i, stock_code in enumerate(stock_codes, 1):
        result = await db.execute(
            select(MarketData)
            .where(
                MarketData.stock_code == stock_code,
                MarketData.date >= start_date,
                MarketData.date <= end_date
            )
            .order_by(MarketData.date.desc())
        )
        market_data = result.scalars().all()

        if market_data:
            cache_key = f"quant:market_data:{stock_code}:{start_date}:{end_date}"
            data_dict = [
                {
                    "date": str(md.date),
                    "open": float(md.open_price),
                    "high": float(md.high_price),
                    "low": float(md.low_price),
                    "close": float(md.close_price),
                    "volume": int(md.volume)
                }
                for md in market_data
            ]
            await cache.set(cache_key, data_dict, ttl=0)

        if i % 100 == 0:
            logger.info(f"진행: {i}/{len(stock_codes)} ({i/len(stock_codes)*100:.1f}%)")

    logger.info(f"✅ {len(stock_codes)}개 종목 시세 캐시 완료")


async def warm_up_financial_data(db: AsyncSession):
    """전체 종목 재무 데이터 캐시"""
    logger.info("=== 재무제표 데이터 캐시 시작 ===")

    # 활성 종목 조회
    result = await db.execute(
        select(Company.stock_code).where(Company.is_active == True)
    )
    stock_codes = [row[0] for row in result.all()]

    # 종목별 최근 8분기 재무제표 캐싱
    for i, stock_code in enumerate(stock_codes, 1):
        result = await db.execute(
            select(FinancialStatement)
            .where(FinancialStatement.stock_code == stock_code)
            .order_by(FinancialStatement.fiscal_year.desc(), FinancialStatement.fiscal_quarter.desc())
            .limit(8)
        )
        financial_data = result.scalars().all()

        if financial_data:
            cache_key = f"quant:financial:{stock_code}"
            data_dict = [
                {
                    "fiscal_year": fs.fiscal_year,
                    "fiscal_quarter": fs.fiscal_quarter,
                    "revenue": float(fs.revenue) if fs.revenue else None,
                    "operating_income": float(fs.operating_income) if fs.operating_income else None,
                    "net_income": float(fs.net_income) if fs.net_income else None,
                    "total_assets": float(fs.total_assets) if fs.total_assets else None,
                    "total_equity": float(fs.total_equity) if fs.total_equity else None,
                }
                for fs in financial_data
            ]
            await cache.set(cache_key, data_dict, ttl=0)

        if i % 100 == 0:
            logger.info(f"진행: {i}/{len(stock_codes)} ({i/len(stock_codes)*100:.1f}%)")

    logger.info(f"✅ {len(stock_codes)}개 종목 재무 캐시 완료")


async def warm_up_factors(db: AsyncSession, base_date: str = None):
    """전체 종목 팩터 데이터 캐시"""
    logger.info("=== 팩터 데이터 캐시 시작 ===")

    if base_date is None:
        base_date = datetime.now().strftime("%Y-%m-%d")

    # FactorCalculator 사용하여 전체 종목 팩터 계산 및 캐싱
    calculator = FactorCalculator()

    try:
        # 전체 종목 팩터 계산 (내부적으로 캐싱됨)
        factors_df = await calculator.calculate_all_factors(
            db=db,
            base_date=base_date,
            use_cache=True
        )

        logger.info(f"✅ {len(factors_df)}개 종목 팩터 캐시 완료")

    except Exception as e:
        logger.error(f"팩터 캐시 실패: {e}")


async def main():
    """전체 캐시 워밍업 실행"""
    logger.info("========================================")
    logger.info("Redis 캐시 사전 로딩 시작")
    logger.info("========================================")

    # Redis 초기화
    await cache.initialize()

    # DB 세션 생성
    async with AsyncSessionLocal() as db:
        try:
            # 1. 종목 정보
            await warm_up_company_info(db)

            # 2. 시세 데이터 (최근 1년)
            await warm_up_market_data(db, days=365)

            # 3. 재무 데이터
            await warm_up_financial_data(db)

            # 4. 팩터 데이터
            await warm_up_factors(db)

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
