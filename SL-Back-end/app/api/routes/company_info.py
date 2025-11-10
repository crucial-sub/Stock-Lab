"""
종목 재무 정보 API 라우터
- 라우팅 및 HTTP 요청/응답 처리
- 비즈니스 로직은 서비스 레이어에서 처리
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.services.company_info import CompanyInfoService
from app.services.user_stock import UserStockService
from app.schemas.company_info import (
    CompanyInfoResponse,
    CompanyBasicInfo,
    InvestmentIndicators,
    ProfitabilityIndicators,
    FinancialRatios,
    QuarterlyPerformance,
    IncomeStatementData,
    BalanceSheetData,
    PriceHistoryPoint
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/company/{stock_code}/info", response_model=CompanyInfoResponse)
async def get_company_info(
    stock_code: str,
    user_id: Optional[UUID] = Query(None, description="사용자 ID (관심종목 판단 및 최근 본 주식 기록용)"),
    db: AsyncSession = Depends(get_db)
):
    """
    종목의 모든 재무 정보를 반환

    Args:
        stock_code: 종목 코드 (6자리, 예: 005930)
        user_id: 사용자 ID (선택, 관심종목 판단 및 최근 본 주식 기록용)
        db: 데이터베이스 세션

    Returns:
        CompanyInfoResponse: 종목의 모든 재무 정보
    """
    try:
        service = CompanyInfoService(db)
        data = await service.get_company_info(stock_code, user_id)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"종목 코드 {stock_code}를 찾을 수 없습니다"
            )

        # 사용자 ID가 있으면 최근 본 주식에 기록
        if user_id:
            user_stock_service = UserStockService(db)
            await user_stock_service.add_recent_view(user_id, stock_code)

        # 응답 모델로 변환
        return CompanyInfoResponse(
            basic_info=CompanyBasicInfo(**data["basic_info"]),
            investment_indicators=InvestmentIndicators(**data["investment_indicators"]),
            profitability_indicators=ProfitabilityIndicators(**data["profitability_indicators"]),
            financial_ratios=FinancialRatios(**data["financial_ratios"]),
            quarterly_performance=[
                QuarterlyPerformance(**perf) for perf in data["quarterly_performance"]
            ],
            income_statements=[
                IncomeStatementData(**stmt) for stmt in data["income_statements"]
            ],
            balance_sheets=[
                BalanceSheetData(**sheet) for sheet in data["balance_sheets"]
            ],
            price_history=[
                PriceHistoryPoint(**point) for point in data["price_history"]
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 정보 조회 실패 ({stock_code}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"종목 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/company/search")
async def search_companies(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    종목 검색 (종목명 또는 종목 코드로 검색)

    Args:
        query: 검색어 (종목명 또는 종목 코드)
        limit: 최대 결과 수
        db: 데이터베이스 세션

    Returns:
        검색된 종목 목록
    """
    try:
        service = CompanyInfoService(db)
        return await service.search_companies(query, limit)

    except Exception as e:
        logger.error(f"종목 검색 실패 ({query}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"종목 검색 중 오류가 발생했습니다: {str(e)}"
        )
