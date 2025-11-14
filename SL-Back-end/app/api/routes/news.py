"""
뉴스 API 라우트 (DB 조회 전용)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import select, func
import os

from app.core.dependencies import get_current_user
from app.services.shared_data import AVAILABLE_THEMES
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.news_repository import NewsRepository
from app.models.news import ThemeSentiment
from loguru import logger

router = APIRouter(prefix="/news", tags=["news"])

# === Schemas ===

class NewsArticleSchema(BaseModel):
    """뉴스 기사 API 응답 스키마"""
    id: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    summary: str
    content: str
    tickerLabel: str  # 종목명
    stockCode: Optional[str] = None  # 종목코드
    themeName: Optional[str] = None  # 테마명
    sentiment: str  # positive, neutral, negative
    publishedAt: str  # 발행일 (YYYY.MM.DD 형식)
    source: str  # 출처
    link: str  # 링크
    pressName: Optional[str] = None  # 언론사명


class NewsListResponse(BaseModel):
    """뉴스 목록 응답"""
    total: int = Field(..., description="Total number of news")
    news: List[NewsArticleSchema] = Field(..., description="News list")


# === API Endpoints (DB-backed only, no crawling) ===

@router.get(
    "/db/stock/{stock_code}",
    response_model=NewsListResponse,
    summary="DB에서 종목 뉴스 조회"
)
async def get_stock_news(
    stock_code: str,
    max_results: int = Query(1000, ge=1, le=10000, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 특정 종목 뉴스 조회."""
    try:
        items = await NewsRepository.get_latest_news_by_stock(db, stock_code, max_results)
        return NewsListResponse(total=len(items), news=items)
    except Exception as e:
        logger.error(f"DB news fetch failed for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news from DB")


@router.get(
    "/db/search",
    response_model=NewsListResponse,
    summary="DB에서 키워드 뉴스 검색"
)
async def search_news(
    keyword: str = Query(..., description="Search keyword"),
    max_results: int = Query(1000, ge=1, le=10000, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 키워드 검색."""
    try:
        items = await NewsRepository.search_news_in_db(db, keyword, max_results)
        return NewsListResponse(total=len(items), news=items)
    except Exception as e:
        logger.error(f"DB news search failed for '{keyword}': {e}")
        raise HTTPException(status_code=500, detail="Failed to search news from DB")


@router.get(
    "/db/theme",
    response_model=NewsListResponse,
    summary="DB에서 테마별 뉴스 조회"
)
async def search_news_by_theme(
    theme: str = Query(..., description="Theme name"),
    max_results: int = Query(1000, ge=1, le=10000, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 테마별 뉴스 조회."""
    try:
        items = await NewsRepository.search_news_by_theme(db, theme, max_results)
        return NewsListResponse(total=len(items), news=items)
    except Exception as e:
        logger.error(f"DB news theme search failed for '{theme}': {e}")
        raise HTTPException(status_code=500, detail="Failed to search news by theme from DB")


@router.get(
    "/db/themes/available",
    summary="DB에서 사용 가능한 테마 목록 조회"
)
async def get_available_themes(
    db: AsyncSession = Depends(get_db),
):
    """DB에 실제로 존재하는 테마 목록을 반환합니다 (뉴스가 있는 테마만)."""
    try:
        themes = await NewsRepository.get_available_themes(db)
        return {
            "themes": themes,
            "count": len(themes),
            "retrieved_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch available themes: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available themes from DB")


@router.get(
    "/themes",
    summary="주요 테마 목록 조회"
)
async def get_major_themes():
    """
    챗봇 또는 다른 서비스에서 사용할 주요 시장 테마 목록을 반환합니다.
    이 목록은 중앙 `shared_data`에서 관리됩니다.
    """
    return {
        "themes": AVAILABLE_THEMES,
        "count": len(AVAILABLE_THEMES),
        "retrieved_at": datetime.now().isoformat()
    }


@router.get(
    "/themes/sentiment-summary",
    summary="미리 분석된 테마별 감성 요약 조회"
)
async def get_theme_sentiment_summary(
    limit: int = Query(5, ge=1, le=20, description="조회할 테마 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    [DB-backed]
    테마별 뉴스 감성 분석 결과를 반환합니다.
    - 긍정/부정 테마 목록과 관련 정보를 제공합니다.
    """
    try:
        # 긍정 테마 조회
        positive_themes_query = select(ThemeSentiment).order_by(ThemeSentiment.sentiment_score.desc()).limit(limit)
        positive_result = await db.execute(positive_themes_query)
        positive_themes = positive_result.scalars().all()

        # 부정 테마 조회
        negative_themes_query = select(ThemeSentiment).order_by(ThemeSentiment.sentiment_score.asc()).limit(limit)
        negative_result = await db.execute(negative_themes_query)
        negative_themes = negative_result.scalars().all()

        # 가장 최근 업데이트된 시간 조회
        latest_update_query = select(func.max(ThemeSentiment.updated_at))
        latest_update_result = await db.execute(latest_update_query)
        latest_update_at = latest_update_result.scalar_one_or_none()

        # Serialize ORM rows to JSON-safe dicts
        def _serialize(ts: ThemeSentiment) -> dict:
            return {
                "theme_name": ts.theme_name,
                "sentiment_score": ts.sentiment_score,
                "summary": ts.summary,
                "positive_news_count": ts.positive_news_count,
                "negative_news_count": ts.negative_news_count,
                "updated_at": (ts.updated_at.isoformat() if ts.updated_at else None),
            }

        return {
            "positive_themes": [_serialize(x) for x in positive_themes],
            "negative_themes": [_serialize(x) for x in negative_themes],
            "last_updated_at": latest_update_at.isoformat() if latest_update_at else datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"테마 감성 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="테마 감성 요약 데이터를 가져오는 데 실패했습니다."
        )


@router.get(
    "/health",
    summary="뉴스 서비스 헬스체크"
)
async def news_health_check():
    """
    뉴스 DB 조회 서비스 상태를 확인합니다.

    **Returns:**
    - 서비스 상태 정보 (DB 조회 전용, 크롤링 기능 제거됨)
    """
    return {
        "status": "ok",
        "service": "news_api",
        "mode": "db_only",
        "crawling_enabled": False,
        "timestamp": datetime.now().isoformat()
    }
