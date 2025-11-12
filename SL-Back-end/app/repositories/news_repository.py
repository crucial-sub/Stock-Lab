"""
News repository for database queries.

Handles search and filtering of news articles.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, or_, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle, ThemeSentiment
from app.models.company import Company


class NewsRepository:
    @staticmethod
    def _format_kst(dt: Optional[datetime]) -> Dict[str, str]:
        """Return ISO and display strings in KST for a given UTC or naive-UTC datetime."""
        if not dt:
            return {"iso": "", "display": ""}
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        kst_dt = dt.astimezone(ZoneInfo("Asia/Seoul"))
        return {"iso": kst_dt.isoformat(), "display": kst_dt.strftime("%Y.%m.%d %H:%M")}

    @staticmethod
    async def search_news_in_db(
        db: AsyncSession,
        keyword: str,
        limit: int = 20,
    ) -> List[Dict]:
        """검색 키워드로 뉴스 조회 (제목/내용/종목코드/회사명 포함)."""
        a = NewsArticle
        c = Company
        q = (
            select(a.id, a.title, a.content, a.link, a.news_date, a.source, a.stock_code, c.stock_name)
            .outerjoin(c, a.stock_code == c.stock_code)
            .where(or_(
                a.title.ilike(f"%{keyword}%"),
                a.content.ilike(f"%{keyword}%"),
                a.stock_code.ilike(f"%{keyword}%"),
                a.company_name.ilike(f"%{keyword}%")
            ))
            .order_by(desc(a.news_date), desc(a.id))
            .limit(limit)
        )
        res = await db.execute(q)
        rows = res.all()
        items: List[Dict] = []
        for r in rows:
            items.append(
                {
                    "id": str(r.id),
                    "stock_code": r.stock_code or "unknown",
                    "stock_name": r.stock_name or "종목",
                    "title": r.title or "",
                    "content": r.content or "",
                    "source": r.source or "뉴스DB",
                    "date": NewsRepository._format_kst(r.news_date),
                    "link": r.link or "",
                    "themeName": None,
                }
            )
        return items

    @staticmethod
    async def search_news_by_theme(
        db: AsyncSession,
        theme: str,
        limit: int = 20,
    ) -> List[Dict]:
        """테마별 뉴스 조회."""
        a = NewsArticle
        c = Company
        q = (
            select(a.id, a.title, a.content, a.link, a.news_date, a.source, a.stock_code, a.theme, c.stock_name)
            .outerjoin(c, a.stock_code == c.stock_code)
            .where(a.theme == theme)
            .order_by(desc(a.news_date), desc(a.id))
            .limit(limit)
        )
        res = await db.execute(q)
        rows = res.all()
        items: List[Dict] = []
        for r in rows:
            items.append(
                {
                    "id": str(r.id),
                    "stock_code": r.stock_code or "unknown",
                    "stock_name": r.stock_name or "종목",
                    "title": r.title or "",
                    "content": r.content or "",
                    "source": r.source or "뉴스DB",
                    "date": NewsRepository._format_kst(r.news_date),
                    "link": r.link or "",
                    "themeName": r.theme,
                }
            )
        return items

    @staticmethod
    async def get_news_by_id(
        db: AsyncSession,
        news_id: int,
    ) -> Optional[Dict]:
        """ID로 뉴스 단건 조회."""
        a = NewsArticle
        q = select(a).where(a.id == news_id)
        res = await db.execute(q)
        article = res.scalar_one_or_none()

        if not article:
            return None

        return {
            "id": str(article.id),
            "stock_code": article.stock_code or "unknown",
            "stock_name": article.stock_code or "종목",
            "title": article.title or "",
            "content": article.content or "",
            "source": article.source or "뉴스DB",
            "date": NewsRepository._format_kst(article.news_date),
            "link": article.link or "",
            "themeName": article.theme,
        }

    @staticmethod
    async def get_latest_news_by_stock(
        db: AsyncSession,
        stock_code: str,
        limit: int = 20,
    ) -> List[Dict]:
        """종목별 최신 뉴스 조회."""
        a = NewsArticle
        c = Company
        q = (
            select(a.id, a.title, a.content, a.link, a.news_date, a.source, a.stock_code, c.stock_name)
            .outerjoin(c, a.stock_code == c.stock_code)
            .where(a.stock_code == stock_code)
            .order_by(desc(a.news_date), desc(a.id))
            .limit(limit)
        )
        res = await db.execute(q)
        rows = res.all()
        items: List[Dict] = []
        for r in rows:
            items.append(
                {
                    "id": str(r.id),
                    "stock_code": r.stock_code or "unknown",
                    "stock_name": r.stock_name or "종목",
                    "title": r.title or "",
                    "content": r.content or "",
                    "source": r.source or "뉴스DB",
                    "date": NewsRepository._format_kst(r.news_date),
                    "link": r.link or "",
                    "themeName": None,
                }
            )
        return items

    @staticmethod
    async def save_news_list_for_stock(
        db: AsyncSession,
        stock_code: Optional[str],
        stock_name: Optional[str],
        news_list: List[Dict],
    ) -> None:
        """뉴스 목록을 데이터베이스에 저장합니다."""
        if not news_list:
            return

        # 1. 모든 뉴스의 링크를 한 번에 조회하여 이미 존재하는 링크를 확인 (N+1 문제 해결)
        links_to_check = [news.get("link") for news in news_list if news.get("link")]
        if not links_to_check:
            return

        existing_links_query = select(NewsArticle.link).where(NewsArticle.link.in_(links_to_check))
        existing_links_result = await db.execute(existing_links_query)
        existing_links = {link for link, in existing_links_result}

        articles_to_add = []
        for news in news_list:
            link = news.get("link")
            if not link or link in existing_links:
                continue

            articles_to_add.append(NewsArticle(
                stock_code=stock_code,
                company_name=stock_name,
                title=news.get("title", ""),
                content=news.get("content", ""),
                source=news.get("source"),
                link=link,
                original_link=news.get("original_link"),
                news_date=news.get("news_date"),
                theme=news.get("theme"),
            ))

        if articles_to_add:
            db.add_all(articles_to_add)
        await db.commit()

    @staticmethod
    async def get_available_themes(
        db: AsyncSession,
    ) -> List[str]:
        """DB에 실제로 존재하는 테마 목록 조회 (뉴스가 있는 테마만)."""
        q = (
            select(distinct(NewsArticle.theme))
            .where(NewsArticle.theme.isnot(None))
            .where(NewsArticle.theme != "")
            .order_by(NewsArticle.theme)
        )
        res = await db.execute(q)
        rows = res.scalars().all()
        return [r for r in rows if r]  # Filter out None values
