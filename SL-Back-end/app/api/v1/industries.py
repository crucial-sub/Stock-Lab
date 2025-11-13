"""
산업(Industry) 및 종목 조회 API
매매 대상 설정에서 사용
"""
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.models.company import Company

router = APIRouter(prefix="/industries", tags=["Industries"])


class StockInfo(BaseModel):
    """종목 정보"""
    stock_code: str
    stock_name: str
    company_name: str
    industry: Optional[str]
    market_type: Optional[str]
    current_price: Optional[int] = None
    change_rate: Optional[float] = None

    class Config:
        from_attributes = True


class IndustryInfo(BaseModel):
    """산업 정보"""
    industry_name: str
    stock_count: int


class IndustryStocksResponse(BaseModel):
    """산업별 종목 응답"""
    industry: str
    stocks: List[StockInfo]
    total_count: int


class IndustryListRequest(BaseModel):
    """여러 산업 조회 요청"""
    industries: List[str]


@router.get("/list", response_model=List[IndustryInfo])
async def get_industries(db: AsyncSession = Depends(get_db)):
    """
    모든 산업 목록 조회 (DB에 실제 존재하는 산업만)

    Returns:
        산업 목록 (각 산업에 속한 종목 수 포함)
    """
    try:
        stmt = (
            select(
                Company.industry,
                func.count(Company.company_id).label("stock_count")
            )
            .where(Company.stock_code.isnot(None))
            .where(Company.industry.isnot(None))
            .group_by(Company.industry)
            .order_by(func.count(Company.company_id).desc())
        )

        result = await db.execute(stmt)
        industries_data = result.all()

        industries = [
            IndustryInfo(
                industry_name=industry_name,
                stock_count=stock_count
            )
            for industry_name, stock_count in industries_data
        ]

        return industries

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"산업 목록 DB 조회 실패 (폴백 데이터 사용): {str(e)}")

        # 폴백 데이터: 주요 산업 목록
        return [
            IndustryInfo(industry_name="반도체", stock_count=120),
            IndustryInfo(industry_name="자동차", stock_count=85),
            IndustryInfo(industry_name="은행", stock_count=15),
            IndustryInfo(industry_name="증권", stock_count=32),
            IndustryInfo(industry_name="화학", stock_count=95),
            IndustryInfo(industry_name="철강", stock_count=45),
            IndustryInfo(industry_name="건설", stock_count=78),
            IndustryInfo(industry_name="유통", stock_count=62),
            IndustryInfo(industry_name="IT 서비스", stock_count=105),
            IndustryInfo(industry_name="통신", stock_count=18),
            IndustryInfo(industry_name="제약", stock_count=142),
            IndustryInfo(industry_name="바이오", stock_count=88),
            IndustryInfo(industry_name="식품", stock_count=54),
            IndustryInfo(industry_name="의료", stock_count=41),
            IndustryInfo(industry_name="게임", stock_count=67),
            IndustryInfo(industry_name="엔터테인먼트", stock_count=35),
        ]


@router.get("/{industry_name}/stocks", response_model=IndustryStocksResponse)
async def get_stocks_by_industry(
    industry_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    산업별 종목 조회

    Args:
        industry_name: 산업명 (예: "반도체", "IT 서비스")

    Returns:
        해당 산업의 모든 종목
    """
    # 필요한 컬럼만 선택하여 종목 조회
    stmt = (
        select(
            Company.stock_code,
            Company.stock_name,
            Company.company_name,
            Company.industry,
            Company.market_type
        )
        .where(Company.stock_code.isnot(None))
        .where(Company.industry == industry_name)
        .order_by(Company.stock_name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # 응답 생성
    stocks = [
        StockInfo(
            stock_code=row.stock_code,
            stock_name=row.stock_name or row.company_name,
            company_name=row.company_name,
            industry=row.industry or "기타",
            market_type=row.market_type,
        )
        for row in rows
    ]

    return IndustryStocksResponse(
        industry=industry_name,
        stocks=stocks,
        total_count=len(stocks),
    )


@router.post("/stocks-by-industries", response_model=List[StockInfo])
async def get_stocks_by_multiple_industries(
    request: IndustryListRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    여러 산업의 종목을 한번에 조회

    Args:
        request: 산업명 리스트를 포함한 요청

    Returns:
        선택된 산업들의 모든 종목
    """
    stmt = (
        select(
            Company.stock_code,
            Company.stock_name,
            Company.company_name,
            Company.industry,
            Company.market_type
        )
        .where(Company.stock_code.isnot(None))
        .where(Company.industry.in_(request.industries))
        .order_by(Company.industry, Company.stock_name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    stocks = [
        StockInfo(
            stock_code=row.stock_code,
            stock_name=row.stock_name or row.company_name,
            company_name=row.company_name,
            industry=row.industry or "기타",
            market_type=row.market_type,
        )
        for row in rows
    ]

    return stocks


@router.get("/search", response_model=List[StockInfo])
async def search_stocks(
    query: str,
    db: AsyncSession = Depends(get_db),
):
    """
    종목명 또는 종목코드로 검색

    검색 우선순위:
    1. 완전 일치 (종목명 == 검색어)
    2. 시작 일치 (종목명이 검색어로 시작)
    3. 부분 일치 (종목명에 검색어 포함)

    Args:
        query: 검색어 (종목명 또는 종목코드)

    Returns:
        검색 결과에 해당하는 종목 목록 (우선순위순)
    """
    try:
        # CASE 문으로 우선순위 지정
        # 1순위: 완전 일치
        # 2순위: 시작 일치
        # 3순위: 부분 일치
        from sqlalchemy import case

        priority = case(
            # 완전 일치 (종목명 또는 종목코드)
            (
                (Company.stock_name == query) |
                (Company.company_name == query) |
                (Company.stock_code == query),
                1
            ),
            # 시작 일치
            (
                (Company.stock_name.ilike(f"{query}%")) |
                (Company.company_name.ilike(f"{query}%")) |
                (Company.stock_code.ilike(f"{query}%")),
                2
            ),
            # 부분 일치
            else_=3
        )

        stmt = (
            select(
                Company.stock_code,
                Company.stock_name,
                Company.company_name,
                Company.industry,
                Company.market_type
            )
            .where(Company.stock_code.isnot(None))
            .where(
                (Company.stock_name.ilike(f"%{query}%")) |
                (Company.company_name.ilike(f"%{query}%")) |
                (Company.stock_code.ilike(f"%{query}%"))
            )
            .order_by(priority, Company.stock_name)  # 우선순위 → 종목명순
            .limit(100)  # 최대 100개까지만 반환
        )

        result = await db.execute(stmt)
        rows = result.all()

        stocks = [
            StockInfo(
                stock_code=row.stock_code,
                stock_name=row.stock_name or row.company_name,
                company_name=row.company_name,
                industry=row.industry or "기타",
                market_type=row.market_type,
            )
            for row in rows
        ]

        return stocks

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"종목 검색 DB 조회 실패 (폴백 데이터 사용): {str(e)}")

        # 폴백 데이터: 주요 종목 목록
        fallback_stocks = [
            StockInfo(stock_code="005930", stock_name="삼성전자", company_name="삼성전자", industry="반도체", market_type="KOSPI"),
            StockInfo(stock_code="000660", stock_name="SK하이닉스", company_name="SK하이닉스", industry="반도체", market_type="KOSPI"),
            StockInfo(stock_code="035720", stock_name="카카오", company_name="카카오", industry="IT 서비스", market_type="KOSPI"),
            StockInfo(stock_code="035420", stock_name="NAVER", company_name="NAVER", industry="IT 서비스", market_type="KOSPI"),
            StockInfo(stock_code="207940", stock_name="삼성바이오로직스", company_name="삼성바이오로직스", industry="바이오", market_type="KOSPI"),
        ]

        # 검색어와 매치되는 종목만 반환
        if query:
            query_lower = query.lower()
            return [
                stock for stock in fallback_stocks
                if query_lower in stock.stock_name.lower()
                or query_lower in stock.company_name.lower()
                or query_lower in stock.stock_code.lower()
            ]

        return fallback_stocks
