"""
시세 페이지 API 라우터
- 전체 종목 시세 리스트 조회
- 정렬 기능 제공
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.services.market_quote import MarketQuoteService
from app.schemas.market_quote import (
    MarketQuoteListResponse,
    MarketQuoteItem,
    SortBy,
    SortOrder
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/market/quotes", response_model=MarketQuoteListResponse)
async def get_market_quotes(
    sort_by: SortBy = Query(SortBy.MARKET_CAP, description="정렬 기준"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    user_id: Optional[UUID] = Query(None, description="사용자 ID (관심종목 판단용)"),
    db: AsyncSession = Depends(get_db)
):
    """
    전체 종목 시세 조회

    Args:
        sort_by: 정렬 기준 (volume, change_rate, trading_value, market_cap, name)
        sort_order: 정렬 순서 (asc, desc)
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기 (1-100)
        user_id: 사용자 ID (선택, 관심종목 판단용)
        db: 데이터베이스 세션

    Returns:
        MarketQuoteListResponse: 시세 리스트 및 페이지네이션 정보

    Example:
        GET /api/v1/market/quotes?sort_by=volume&sort_order=desc&page=1&page_size=50&user_id=...
    """
    try:
        service = MarketQuoteService(db)
        data = await service.get_market_quotes(
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            user_id=user_id
        )

        return MarketQuoteListResponse(
            items=[MarketQuoteItem(**item) for item in data["items"]],
            total=data["total"],
            page=data["page"],
            page_size=data["page_size"],
            has_next=data["has_next"]
        )

    except Exception as e:
        logger.error(f"시세 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"시세 조회 중 오류가 발생했습니다: {str(e)}"
        )
