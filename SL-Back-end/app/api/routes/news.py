"""
뉴스 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import select
import os

from app.services.news_crawler import NewsCrawler
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
    stock_code: str
    stock_name: str
    title: str
    content: str
    source: str
    date: Dict[str, str]
    link: str
    original_link: Optional[str] = None


class NewsListResponse(BaseModel):
    """뉴스 목록 응답"""
    total: int = Field(..., description="Total number of news")
    news: List[NewsArticleSchema] = Field(..., description="News list")


class CrawlRequest(BaseModel):
    """뉴스 크롤링 요청"""
    stocks: List[Dict[str, str]] = Field(
        ...,
        description="List of stocks to crawl",
        example=[{"code": "005930", "name": "삼성전자"}]
    )
    max_results_per_stock: int = Field(20, ge=1, le=100, description="Max news per stock")


class CrawlResponse(BaseModel):
    """크롤링 응답"""
    total_stocks: int
    total_news: int
    news_by_stock: Dict[str, List[NewsArticleSchema]]


# === Helper Functions ===

def get_news_crawler() -> NewsCrawler:
    """뉴스 크롤러 인스턴스 생성"""
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Naver API credentials not configured"
        )

    return NewsCrawler(client_id, client_secret)


# === API Endpoints ===

@router.get(
    "/stock/{stock_code}",
    response_model=NewsListResponse,
    summary="종목별 뉴스 조회"
)
async def get_stock_news(
    stock_code: str,
    stock_name: str = Query(..., description="Stock name"),
    max_results: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 종목의 최신 뉴스를 조회합니다.

    - **stock_code**: 종목코드 (예: 005930)
    - **stock_name**: 종목명 (예: 삼성전자)
    - **max_results**: 최대 결과 수 (1-100, 기본값: 20)

    **Returns:**
    - 뉴스 목록 (최신순)
    """
    try:
        crawler = get_news_crawler()
        news_list = await crawler.crawl_stock_news(
            stock_code,
            stock_name,
            max_results
        )

        # Persist to DB (best-effort)
        try:
            await NewsRepository.save_news_list_for_stock(
                db,
                stock_code=stock_code,
                stock_name=stock_name,
                news_list=news_list,
            )
        except Exception as pe:
            logger.warning(f"Persist news failed for {stock_code}: {pe}")

        return NewsListResponse(
            total=len(news_list),
            news=news_list
        )

    except Exception as e:
        logger.error(f"Failed to get news for {stock_code}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch news: {str(e)}"
        )


@router.post(
    "/crawl",
    response_model=CrawlResponse,
    summary="여러 종목 뉴스 크롤링"
)
async def crawl_multiple_stocks(
    request: CrawlRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    여러 종목의 뉴스를 동시에 크롤링합니다.

    **Parameters:**
    - **stocks**: 종목 리스트 (code, name 포함)
    - **max_results_per_stock**: 종목당 최대 뉴스 수

    **Returns:**
    - 종목별 뉴스 딕셔너리

    **Note:**
    - 인증 필요 (JWT 토큰)
    - 대량 크롤링 시 네이버 API 호출 제한 주의
    """
    try:
        crawler = get_news_crawler()
        news_by_stock = await crawler.crawl_multiple_stocks(
            request.stocks,
            request.max_results_per_stock
        )

        total_news = sum(len(news) for news in news_by_stock.values())

        # Persist all (best-effort)
        try:
            for stock in request.stocks:
                code = stock.get("code")
                name = stock.get("name")
                items = news_by_stock.get(code, [])
                if items:
                    await NewsRepository.save_news_list_for_stock(
                        db, stock_code=code, stock_name=name, news_list=items
                    )
        except Exception as pe:
            logger.warning(f"Persist batch news failed: {pe}")

        return CrawlResponse(
            total_stocks=len(request.stocks),
            total_news=total_news,
            news_by_stock=news_by_stock
        )

    except Exception as e:
        logger.error(f"Failed to crawl news: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to crawl news: {str(e)}"
        )


@router.get(
    "/search",
    response_model=NewsListResponse,
    summary="키워드로 뉴스 검색"
)
async def search_news(
    keyword: str = Query(..., description="Search keyword"),
    max_results: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db)
):
    """
    키워드로 뉴스를 검색합니다.

    **Parameters:**
    - **keyword**: 검색 키워드
    - **max_results**: 최대 결과 수

    **Returns:**
    - 뉴스 목록 (최신순)
    """
    try:
        crawler = get_news_crawler()

        # 키워드 검색 (종목코드는 unknown으로 설정)
        news_list = await crawler.crawl_stock_news(
            "unknown",
            keyword,
            max_results
        )

        # Persist without symbol mapping
        try:
            await NewsRepository.save_news_list_for_stock(
                db,
                stock_code=None,
                stock_name=None,
                news_list=news_list,
            )
        except Exception as pe:
            logger.warning(f"Persist search news failed for '{keyword}': {pe}")

        return NewsListResponse(
            total=len(news_list),
            news=news_list
        )

    except Exception as e:
        logger.error(f"Failed to search news for '{keyword}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search news: {str(e)}"
        )


@router.get(
    "/health",
    summary="뉴스 서비스 헬스체크"
)
async def news_health_check():
    """
    뉴스 서비스 상태를 확인합니다.

    **Returns:**
    - 서비스 상태 정보
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    return {
        "status": "ok",
        "service": "news_api",
        "naver_api_configured": bool(client_id and client_secret),
        "timestamp": datetime.now().isoformat()
    }


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
    [IMPROVEMENT]
    백그라운드에서 주기적으로 분석/저장된 테마별 뉴스 감성 분석 결과를 반환합니다.
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

        # Serialize ORM rows to JSON-safe dicts so clients (and the chatbot tool)
        # receive plain JSON rather than SQLAlchemy model objects.
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


# === DB-backed Endpoints (no crawling) ===

@router.get(
    "/db/stock/{stock_code}",
    response_model=NewsListResponse,
    summary="DB에서 종목 뉴스 조회"
)
async def get_stock_news_from_db(
    stock_code: str,
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 특정 종목 뉴스 조회."""
    try:
        items = await NewsRepository.get_latest_news_by_stock(db, stock_code, limit)
        return NewsListResponse(total=len(items), news=items)
    except Exception as e:
        logger.error(f"DB news fetch failed for {stock_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news from DB")


@router.get(
    "/db/search",
    response_model=NewsListResponse,
    summary="DB에서 키워드 뉴스 검색"
)
async def search_news_from_db(
    keyword: str = Query(..., description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 키워드 검색."""
    try:
        items = await NewsRepository.search_news_in_db(db, keyword, limit)
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
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """DB 저장본에서 테마별 뉴스 조회."""
    try:
        items = await NewsRepository.search_news_by_theme(db, theme, limit)
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
