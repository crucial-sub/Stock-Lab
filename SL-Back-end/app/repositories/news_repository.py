"""
뉴스 Repository - DB 조회 전용

"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.news import NewsArticle, ThemeSentiment
from app.repositories.theme_repository import ThemeRepository
from loguru import logger
import html
from datetime import datetime
from pytz import UTC, timezone

# 테마 매핑 캐시 (DB에서 동적으로 로드)
_THEME_MAPPING_CACHE: Optional[Dict[str, str]] = None
_THEME_MAPPING_REVERSE_CACHE: Optional[Dict[str, str]] = None


async def _load_theme_mappings(db: AsyncSession) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    DB에서 테마 매핑 로드 (영문 ↔ 한글)

    Returns:
        (영문→한글 매핑, 한글→영문 매핑)
    """
    global _THEME_MAPPING_CACHE, _THEME_MAPPING_REVERSE_CACHE

    if _THEME_MAPPING_CACHE is not None and _THEME_MAPPING_REVERSE_CACHE is not None:
        return _THEME_MAPPING_CACHE, _THEME_MAPPING_REVERSE_CACHE

    theme_repo = ThemeRepository(db)
    _THEME_MAPPING_CACHE = await theme_repo.get_theme_mapping()
    _THEME_MAPPING_REVERSE_CACHE = {v: k for k, v in _THEME_MAPPING_CACHE.items()}

    logger.info(f"Loaded {len(_THEME_MAPPING_CACHE)} themes from database")
    return _THEME_MAPPING_CACHE, _THEME_MAPPING_REVERSE_CACHE

# 언론사 코드/도메인 -> 명칭 매핑
MEDIA_DOMAIN_MAPPING = {
    "001": "연합뉴스",
    "002": "프레시안",
    "003": "뉴시스",
    "005": "국민일보",
    "006": "미디어오늘",
    "007": "일다",
    "008": "머니투데이",
    "009": "매일경제",
    "011": "서울경제",
    "014": "파이낸셜뉴스",
    "015": "한국경제",
    "016": "헤럴드경제",
    "018": "이데일리",
    "020": "동아일보",
    "021": "문화일보",
    "022": "세계일보",
    "023": "조선일보",
    "024": "매경이코노미",
    "025": "중앙일보",
    "028": "한겨레",
    "029": "디지털타임스",
    "030": "전자신문",
    "031": "아이뉴스24",
    "032": "경향신문",
    "044": "코리아헤럴드",
    "047": "오마이뉴스",
    "050": "한경비즈니스",
    "052": "YTN",
    "053": "주간조선",
    "055": "SBS",
    "056": "KBS",
    "057": "MBN",
    "079": "노컷뉴스",
    "081": "서울신문",
    "082": "부산일보",
    "087": "강원일보",
    "088": "매일신문",
    "092": "지디넷코리아",
    "094": "월간 산",
    "119": "데일리안",
    "123": "조세일보",
    "127": "기자협회보",
    "138": "디지털데일리",
    "145": "레이디경향",
    "214": "MBC",
    "215": "한국경제TV",
    "243": "이코노미스트",
    "262": "신동아",
    "277": "아시아경제",
    "293": "블로터",
    "296": "코메디닷컴",
    "308": "시사IN",
    "310": "여성신문",
    "346": "헬스조선",
    "366": "조선비즈",
    "374": "SBS Biz",
    "417": "머니S",
    "421": "뉴스1",
    "422": "연합뉴스TV",
    "437": "JTBC",
    "448": "TV조선",
    "449": "채널A",
    "469": "한국일보",
    "584": "동아사이언스",
    "586": "시사저널",
    "607": "뉴스타파",
    "629": "더팩트",
    "648": "비즈워치",
    "654": "강원도민일보",
    "655": "CJB청주방송",
    "656": "대전일보",
    "657": "대구MBC",
    "659": "전주MBC",
    "660": "kbc광주방송",
    "661": "JIBS",
    "662": "농민신문",
    "665": "더스쿠프",
    "666": "경기일보",
}

# 역방향 매핑(코드가 문자열이 아닌 도메인 형태로 들어올 때 대비)
MEDIA_DOMAIN_MAPPING.update({v: v for v in MEDIA_DOMAIN_MAPPING.values()})


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
            # DB에서 테마 매핑 로드
            theme_mapping, _ = await _load_theme_mappings(db)

            query = select(NewsArticle).where(
                NewsArticle.stock_code == stock_code
            ).order_by(
                NewsArticle.news_date.desc(),
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article, theme_mapping) for article in articles]
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
            # DB에서 테마 매핑 로드
            theme_mapping, _ = await _load_theme_mappings(db)

            query = select(NewsArticle).where(
                or_(
                    NewsArticle.title.contains(keyword),
                    NewsArticle.content.contains(keyword),
                    NewsArticle.company_name.contains(keyword),  # 회사명으로 검색
                    NewsArticle.stock_code.contains(keyword)  # 종목코드로 검색
                )
            ).order_by(
                NewsArticle.news_date.desc(),
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article, theme_mapping) for article in articles]
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
            # DB에서 테마 매핑 로드
            theme_mapping, theme_mapping_reverse = await _load_theme_mappings(db)

            # 프론트에서 받은 값이 테마인지 회사명인지 판단
            # 테마일 경우 영어 코드로 변환, 회사명일 경우 그대로 사용
            search_theme = theme_mapping_reverse.get(theme, theme)

            # 회사명(종목명)으로도 검색 가능하도록 OR 조건 추가
            query = select(NewsArticle).where(
                or_(
                    NewsArticle.theme == search_theme,
                    NewsArticle.company_name == theme
                )
            ).order_by(
                NewsArticle.news_date.desc(),
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article, theme_mapping) for article in articles]
        except Exception as e:
            logger.error(f"Failed to search news by theme '{theme}': {e}")
            return []

    @staticmethod
    async def search_news_by_themes(
        db: AsyncSession,
        themes: List[str],
        limit: int = 1000
    ) -> List[Dict]:
        """
        여러 테마 또는 회사명을 동시에 조회

        Args:
            db: 데이터베이스 세션
            themes: 테마명 또는 회사명 리스트
            limit: 조회 제한 수

        Returns:
            뉴스 리스트
        """
        try:
            theme_mapping, theme_mapping_reverse = await _load_theme_mappings(db)

            normalized_themes = []
            for theme in themes:
                normalized_themes.append(theme_mapping_reverse.get(theme, theme))

            conditions = []
            for normalized in normalized_themes:
                conditions.append(NewsArticle.theme == normalized)
                conditions.append(NewsArticle.company_name == normalized)

            if not conditions:
                return []

            query = select(NewsArticle).where(
                or_(*conditions)
            ).order_by(
                NewsArticle.news_date.desc(),
                NewsArticle.analyzed_at.desc()
            ).limit(limit)

            result = await db.execute(query)
            articles = result.scalars().all()

            return [_serialize_news(article, theme_mapping) for article in articles]
        except Exception as e:
            logger.error(f"Failed to search news by themes '{themes}': {e}")
            return []

    @staticmethod
    async def get_news_by_id(
        db: AsyncSession,
        news_id: int
    ) -> Optional[Dict]:
        """
        ID로 뉴스 기사 단건 조회
        """
        try:
            theme_mapping, _ = await _load_theme_mappings(db)

            query = select(NewsArticle).where(NewsArticle.id == news_id)
            result = await db.execute(query)
            article = result.scalar_one_or_none()
            if not article:
                return None

            return _serialize_news(article, theme_mapping)
        except Exception as e:
            logger.error(f"Failed to fetch news by id '{news_id}': {e}")
            return None

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
          # DB에서 테마 매핑 로드
          theme_mapping, _ = await _load_theme_mappings(db)

          query = select(NewsArticle).order_by(
              NewsArticle.news_date.desc(),
              NewsArticle.analyzed_at.desc(),
              NewsArticle.id.desc()
          ).limit(limit)
          result = await db.execute(query)
          articles = result.scalars().all()
          return [_serialize_news(article, theme_mapping) for article in articles]
        except Exception as e:
          logger.error(f"Failed to fetch latest news: {e}")
          return []


def _serialize_news(article: NewsArticle, theme_mapping: Optional[Dict[str, str]] = None) -> Dict:
    """뉴스 기사를 직렬화 - 프론트 스키마에 맞게"""
    # 날짜 선택 (우선순위: analyzed_at(분석 완료 시간) > crawled_at > news_date)
    published_at = ""

    date_obj = article.news_date 

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

    # 테마명 매핑 (theme만 사용, company_name은 tickerLabel로 처리)
    theme_name = None
    if article.theme:
        if theme_mapping:
            theme_name = theme_mapping.get(article.theme.lower(), article.theme)
        else:
            theme_name = article.theme

    # 종목명 결정: company_name > stock_code 매핑 > 빈 문자열
    ticker_label = article.company_name or ""
    if not ticker_label and article.stock_code:
        ticker_label = STOCK_CODE_MAPPING.get(article.stock_code, "")

    display_source = article.source or ""
    press_name = None
    if hasattr(article, "media_domain") and article.media_domain:
        press_name = MEDIA_DOMAIN_MAPPING.get(article.media_domain, display_source)
    elif article.source:
        press_name = MEDIA_DOMAIN_MAPPING.get(article.source, display_source)

    return {
        "id": str(article.id) if article.id else None,
        "title": html.unescape(article.title) if article.title else "",
        "subtitle": None,
        "summary": html.unescape(article.content[:200]) if article.content else "",  # 처음 200자를 summary로
        "llm_summary": html.unescape(article.llm_summary) if getattr(article, "llm_summary", None) else "",
        "content": html.unescape(article.content) if article.content else "",
        "tickerLabel": ticker_label,  # 종목명
        "stockCode": article.stock_code or None,  # 종목코드
        "themeName": theme_name,  # 테마명 (한글)
        "themeNameKor": theme_name,  # 테마명 (한글) - 프론트 요청
        "sentiment": sentiment,
        "publishedAt": published_at,  # 분석 완료 시간 (analyzed_at)
        "source": display_source,
        "link": article.link or "",
        "pressName": press_name
    }
