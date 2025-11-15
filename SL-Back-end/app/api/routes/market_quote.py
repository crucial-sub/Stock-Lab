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
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.market_quote import MarketQuoteService
from app.services.user_stock import UserStockService
from app.schemas.market_quote import (
    MarketQuoteListResponse,
    MarketQuoteItem,
    SortBy,
    SortOrder
)
from app.schemas.user_stock import (
    FavoriteStockAdd,
    FavoriteStockListResponse,
    RecentStockListResponse
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


# ==================== 관심 종목 ====================

@router.get("/market/favorites", response_model=FavoriteStockListResponse)
async def get_favorite_stocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    관심 종목 목록 조회 (최근 등록 순)
    - favorite_id 역순 정렬
    """
    try:
        service = UserStockService(db)
        result = await service.get_favorites(current_user.user_id)
        return FavoriteStockListResponse(**result)
    except Exception as e:
        logger.error(f"관심 종목 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/favorites")
async def add_favorite_stock(
    request: FavoriteStockAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    관심 종목 추가
    - 이미 존재하면 409 에러 반환
    """
    try:
        service = UserStockService(db)
        await service.add_favorite(current_user.user_id, request.stock_code)
        return {"message": "관심 종목이 추가되었습니다", "stock_code": request.stock_code}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"관심 종목 추가 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/market/favorites/{stock_code}")
async def remove_favorite_stock(
    stock_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    관심 종목 삭제
    - 존재하지 않으면 404 에러 반환
    """
    try:
        service = UserStockService(db)
        await service.remove_favorite(current_user.user_id, stock_code)
        return {"message": "관심 종목이 삭제되었습니다", "stock_code": stock_code}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"관심 종목 삭제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 최근 본 종목 ====================

@router.get("/market/recent-viewed", response_model=RecentStockListResponse)
async def get_recent_viewed_stocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 본 종목 목록 조회 (최신 순, 최대 10개)
    - viewed_at 역순 정렬
    """
    try:
        service = UserStockService(db)
        result = await service.get_recent_views(current_user.user_id)
        return RecentStockListResponse(**result)
    except Exception as e:
        logger.error(f"최근 본 종목 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/recent-viewed/{stock_code}")
async def add_recent_viewed_stock(
    stock_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 본 종목 추가
    - 이미 존재하면 viewed_at 업데이트
    - 10개 초과 시 가장 오래된 항목 자동 삭제
    """
    try:
        service = UserStockService(db)
        await service.add_recent_view(current_user.user_id, stock_code)
        return {"message": "최근 본 종목에 추가되었습니다", "stock_code": stock_code}
    except Exception as e:
        logger.error(f"최근 본 종목 추가 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/market/recent-viewed/{stock_code}")
async def remove_recent_viewed_stock(
    stock_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 본 종목 수동 삭제
    - 존재하지 않으면 404 에러 반환
    """
    try:
        service = UserStockService(db)
        await service.remove_recent_view(current_user.user_id, stock_code)
        return {"message": "최근 본 종목이 삭제되었습니다", "stock_code": stock_code}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"최근 본 종목 삭제 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
