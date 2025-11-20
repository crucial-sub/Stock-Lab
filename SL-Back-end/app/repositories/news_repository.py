"""
뉴스 Repository - DB 조회 전용

"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.news import NewsArticle, ThemeSentiment
from loguru import logger
import html
from datetime import datetime
from pytz import UTC, timezone

# Theme mapping: English (DB) <-> Korean (Frontend)
THEME_MAPPING = {
    "other": "기타",
    "chemical": "화학",
    "other_finance": "기타금융",
    "electronics": "전기·전자",
    "distribution": "유통",
    "transport_equipment": "운송장비·부품",
    "metal": "금속",
    "pharma": "제약",
    "food": "음식료·담배",
    "construction": "건설",
    "service": "일반서비스",
    "machinery": "기계·장비",
    "textile": "섬유·의류",
    "securities": "증권",
    "transport": "운송·창고",
    "it_service": "IT 서비스",
    "real_estate": "부동산",
    "non_metal": "비금속",
    "paper": "종이·목재",
    "insurance": "보험",
    "entertainment": "오락·문화",
    "utility": "전기·가스·수도",
    "other_manufacturing": "기타제조",
    "medical": "의료·정밀기기",
    "telecom": "통신",
    "bank": "은행",
    "agriculture": "농업, 임업 및 어업",
    "finance": "금융",
    "publishing": "출판·매체복제",
}

#프론트에서 받은 한글 테마명을 영어로 변환
THEME_MAPPING_REVERSE = {v: k for k, v in THEME_MAPPING.items()}


STOCK_CODE_MAPPING = {
    "005930": "삼성전자",
    "051910": "LG화학",
    "035720": "카카오",
    "007670": "SK텔레콤",
    "068270": "셀트리온",
    "207940": "삼성바이오로직스",
    "012330": "현대모비스",
    "028260": "삼성물산",
    "055550": "신한지주",
    "316140": "우리금융지주",
    "005380": "현대차",
    "000270": "기아",
    "247540": "에코프로",
    "247950": "인코스페이스",
    "066570": "LG전자",
    "010140": "삼성중공업",
    "034730": "SK",
    "032830": "삼성생명",
    "030200": "KT",
    "011200": "HMM",
    "015760": "한국전력",
    "018260": "삼성SDS",
    "036570": "엔씨소프트",
    "044820": "쿠팡",
    "032640": "LG우",
}


class NewsRepository:
    """뉴스 DB 조회 레포지토리"""

    @staticmethod
    async def get_latest_news_by_stock(
        db: AsyncSession,
        stock_code: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        특정 종목의 최신 뉴스 조회

        Args:
            db: 데이터베이스 세션
            stock_code: 종목코드
            limit: 조회 제한 수

        Returns:
            뉴스 리스트
        """
        try:
            query = select(NewsArticle).where(
                NewsArticle.stock_code == stock_code
            ).order_by(
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article) for article in articles]
        except Exception as e:
            logger.error(f"Failed to get news for {stock_code}: {e}")
            return []

    @staticmethod
    async def search_news_in_db(
        db: AsyncSession,
        keyword: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        키워드로 뉴스 검색 (제목, 내용, 회사명, 종목코드)

        Args:
            db: 데이터베이스 세션
            keyword: 검색 키워드 (회사명, 종목코드, 제목, 내용)
            limit: 조회 제한 수

        Returns:
            뉴스 리스트
        """
        try:
            query = select(NewsArticle).where(
                or_(
                    NewsArticle.title.contains(keyword),
                    NewsArticle.content.contains(keyword),
                    NewsArticle.company_name.contains(keyword),  # 회사명으로 검색
                    NewsArticle.stock_code.contains(keyword)  # 종목코드로 검색
                )
            ).order_by(
                NewsArticle.analyzed_at.desc()  # 분석 완료 시간 기준 정렬
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article) for article in articles]
        except Exception as e:
            logger.error(f"Failed to search news for '{keyword}': {e}")
            return []

    @staticmethod
    async def search_news_by_theme(
        db: AsyncSession,
        theme: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        테마별 뉴스 조회

        Args:
            db: 데이터베이스 세션
            theme: 테마명 (한글 또는 영어)
            limit: 조회 제한 수

        Returns:
            뉴스 리스트
        """
        try:
            # 프론트에서 받은 값이 테마인지 회사명인지 판단
            # 테마일 경우 영어 코드로 변환, 회사명일 경우 그대로 사용
            search_theme = THEME_MAPPING_REVERSE.get(theme, theme)

            # 회사명(종목명)으로도 검색 가능하도록 OR 조건 추가
            query = select(NewsArticle).where(
                or_(
                    NewsArticle.theme == search_theme,
                    NewsArticle.company_name == theme
                )
            ).order_by(
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article) for article in articles]
        except Exception as e:
            logger.error(f"Failed to search news by theme '{theme}': {e}")
            return []

    @staticmethod
    async def get_available_themes(db: AsyncSession) -> List[str]:
        """
        DB에 실제로 존재하는 회사명(종목명) 목록 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            회사명 목록
        """
        try:
            query = (
                select(NewsArticle.company_name)
                .distinct()
                .where(
                    NewsArticle.company_name.isnot(None),
                    NewsArticle.company_name != ""
                )
                .order_by(NewsArticle.company_name.asc())
            )

            result = await db.execute(query)
            companies = result.scalars().all()

            # company_name이 비어있을 경우를 대비해 테마명으로 대체
            if companies:
                return list(companies)

            theme_query = select(NewsArticle.theme).distinct().where(
                NewsArticle.theme.isnot(None)
            )
            theme_result = await db.execute(theme_query)
            themes = theme_result.scalars().all()
            return list(themes) if themes else []
        except Exception as e:
            logger.error(f"Failed to get available themes: {e}")
            return []

    @staticmethod
    async def get_latest_news(db: AsyncSession, limit: int = 5) -> List[Dict]:
        """최신 뉴스 (id 기준 내림차순)"""
        try:
          query = select(NewsArticle).order_by(NewsArticle.id.desc()).limit(limit)
          result = await db.execute(query)
          articles = result.scalars().all()
          return [_serialize_news(article) for article in articles]
        except Exception as e:
          logger.error(f"Failed to fetch latest news: {e}")
          return []


def _serialize_news(article: NewsArticle) -> Dict:
    """뉴스 기사를 직렬화 - 프론트 스키마에 맞게"""
    # 날짜 선택 (우선순위: analyzed_at(분석 완료 시간) > crawled_at > news_date)
    published_at = ""

    date_obj = article.news_date or article.crawled_at or article.analyzed_at

    if date_obj:
        try:
            # datetime인 경우 UTC -> KST 변환
            if isinstance(date_obj, datetime):
                # UTC 타임존 추가 (naive datetime인 경우)
                if date_obj.tzinfo is None:
                    date_obj = UTC.localize(date_obj)
                # KST로 변환
                kst = timezone('Asia/Seoul')
                date_obj = date_obj.astimezone(kst)
                published_at = date_obj.strftime('%Y.%m.%d')
            else:
                # Date 타입인 경우 직접 문자열로 변환
                published_at = date_obj.strftime('%Y.%m.%d') if hasattr(date_obj, 'strftime') else str(date_obj)
        except Exception as e:
            logger.debug(f"Failed to convert date for article {article.id}: {e}")
            # 실패 시 빈 문자열 유지
            pass

    # sentiment_label을 sentiment로 매핑
    sentiment_map = {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "POSITIVE": "positive",
        "NEGATIVE": "negative",
        "NEUTRAL": "neutral",
        None: "neutral"
    }
    sentiment = sentiment_map.get(article.sentiment_label, "neutral")

    # 카테고리는 기본적으로 회사명(종목명)으로 표기, 없으면 테마명 매핑
    theme_name = article.company_name or None
    if not theme_name and article.theme:
        theme_name = THEME_MAPPING.get(article.theme.lower(), article.theme)

    # 종목명 결정: company_name > stock_code 매핑 > 빈 문자열
    ticker_label = article.company_name or ""
    if not ticker_label and article.stock_code:
        ticker_label = STOCK_CODE_MAPPING.get(article.stock_code, "")

    return {
        "id": str(article.id) if article.id else None,
        "title": html.unescape(article.title) if article.title else "",
        "subtitle": None,
        "summary": html.unescape(article.content[:200]) if article.content else "",  # 처음 200자를 summary로
        "content": html.unescape(article.content) if article.content else "",
        "tickerLabel": ticker_label,  # 종목명
        "stockCode": article.stock_code or None,  # 종목코드
        "themeName": theme_name,  # 테마명 (한글)
        "themeNameKor": theme_name,  # 테마명 (한글) - 프론트 요청
        "sentiment": sentiment,
        "publishedAt": published_at,  # 분석 완료 시간 (analyzed_at)
        "source": article.source or "",
        "link": article.link or "",
        "pressName": None
    }
