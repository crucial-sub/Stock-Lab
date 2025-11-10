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


@router.get("/list", response_model=List[IndustryInfo])
async def get_industries(db: AsyncSession = Depends(get_db)):
    """
    모든 산업 목록 조회 (DB에 실제 존재하는 산업만)

    Returns:
        산업 목록 (각 산업에 속한 종목 수 포함)
    """
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
    # 최신 주가 정보와 함께 종목 조회
    stmt = (
        select(Company)
        .where(Company.stock_code.isnot(None))
        .where(Company.industry == industry_name)
        .order_by(Company.stock_name)
    )

    result = await db.execute(stmt)
    companies = result.scalars().all()

    # 응답 생성
    stocks = [
        StockInfo(
            stock_code=c.stock_code,
            stock_name=c.stock_name or c.company_name,
            company_name=c.company_name,
            industry=c.industry or "기타",
            market_type=c.market_type,
        )
        for c in companies
    ]

    return IndustryStocksResponse(
        industry=industry_name,
        stocks=stocks,
        total_count=len(stocks),
    )


@router.post("/stocks-by-industries", response_model=List[StockInfo])
async def get_stocks_by_multiple_industries(
    industries: List[str],
    db: AsyncSession = Depends(get_db),
):
    """
    여러 산업의 종목을 한번에 조회

    Args:
        industries: 산업명 리스트

    Returns:
        선택된 산업들의 모든 종목
    """
    stmt = (
        select(Company)
        .where(Company.stock_code.isnot(None))
        .where(Company.industry.in_(industries))
        .order_by(Company.industry, Company.stock_name)
    )

    result = await db.execute(stmt)
    companies = result.scalars().all()

    stocks = [
        StockInfo(
            stock_code=c.stock_code,
            stock_name=c.stock_name or c.company_name,
            company_name=c.company_name,
            industry=c.industry or "기타",
            market_type=c.market_type,
        )
        for c in companies
    ]

    return stocks
