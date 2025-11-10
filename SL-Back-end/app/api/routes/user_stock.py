"""
사용자 관심종목/최근 본 주식 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.core.database import get_db
from app.services.user_stock import UserStockService
from app.schemas.user_stock import (
    FavoriteStockAdd,
    FavoriteStockListResponse,
    FavoriteStockItem,
    RecentStockListResponse,
    RecentStockItem
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 관심종목 ====================

@router.post("/users/{user_id}/favorites")
async def add_favorite_stock(
    user_id: UUID,
    request: FavoriteStockAdd,
    db: AsyncSession = Depends(get_db)
):
    """
    관심종목 추가

    Args:
        user_id: 사용자 ID
        request: 종목 코드

    Returns:
        추가 결과 메시지
    """
    try:
        service = UserStockService(db)
        result = await service.add_favorite(user_id, request.stock_code)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"관심종목 추가 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 추가 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/users/{user_id}/favorites/{stock_code}")
async def remove_favorite_stock(
    user_id: UUID,
    stock_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    관심종목 삭제

    Args:
        user_id: 사용자 ID
        stock_code: 종목 코드

    Returns:
        삭제 결과 메시지
    """
    try:
        service = UserStockService(db)
        result = await service.remove_favorite(user_id, stock_code)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"관심종목 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/users/{user_id}/favorites", response_model=FavoriteStockListResponse)
async def get_favorite_stocks(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    관심종목 리스트 조회

    Args:
        user_id: 사용자 ID

    Returns:
        관심종목 리스트
    """
    try:
        service = UserStockService(db)
        data = await service.get_favorites(user_id)

        return FavoriteStockListResponse(
            items=[FavoriteStockItem(**item) for item in data["items"]],
            total=data["total"]
        )

    except Exception as e:
        logger.error(f"관심종목 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/users/{user_id}/favorites/{stock_code}/check")
async def check_favorite_stock(
    user_id: UUID,
    stock_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 종목이 관심종목인지 확인

    Args:
        user_id: 사용자 ID
        stock_code: 종목 코드

    Returns:
        관심종목 여부
    """
    try:
        service = UserStockService(db)
        is_favorite = await service.check_favorite(user_id, stock_code)

        return {"is_favorite": is_favorite}

    except Exception as e:
        logger.error(f"관심종목 확인 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"관심종목 확인 중 오류가 발생했습니다: {str(e)}"
        )


# ==================== 최근 본 주식 ====================

@router.get("/users/{user_id}/recent-stocks", response_model=RecentStockListResponse)
async def get_recent_stocks(
    user_id: UUID,
    limit: int = Query(10, ge=1, le=50, description="최대 개수"),
    db: AsyncSession = Depends(get_db)
):
    """
    최근 본 주식 리스트 조회

    Args:
        user_id: 사용자 ID
        limit: 최대 개수 (기본 10개)

    Returns:
        최근 본 주식 리스트
    """
    try:
        service = UserStockService(db)
        data = await service.get_recent_views(user_id, limit)

        return RecentStockListResponse(
            items=[RecentStockItem(**item) for item in data["items"]],
            total=data["total"]
        )

    except Exception as e:
        logger.error(f"최근 본 주식 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"최근 본 주식 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/users/{user_id}/recent-stocks/{stock_code}")
async def add_recent_stock(
    user_id: UUID,
    stock_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    최근 본 주식 기록

    Args:
        user_id: 사용자 ID
        stock_code: 종목 코드

    Returns:
        성공 메시지
    """
    try:
        service = UserStockService(db)
        await service.add_recent_view(user_id, stock_code)

        return {"message": "최근 본 주식에 기록되었습니다"}

    except Exception as e:
        logger.error(f"최근 본 주식 기록 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"최근 본 주식 기록 중 오류가 발생했습니다: {str(e)}"
        )
