"""Background news crawling worker (every N seconds).

Runs a periodic task to crawl configured stocks and persist into DB.
"""
from __future__ import annotations

import asyncio
import os
from typing import List, Dict

from loguru import logger

from app.services.news_crawler import NewsCrawler
from app.repositories.news_repository import NewsRepository
from app.core.database import AsyncSessionLocal
from app.models.company import Company
from sqlalchemy import select


async def _get_stocks_from_db() -> List[Dict[str, str]]:
    """Get active stocks from database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Company).where(Company.is_active == 1, Company.stock_code.isnot(None))
        )
        companies = result.scalars().all()

        stocks = [
            {"code": company.stock_code, "name": company.stock_name or company.company_name}
            for company in companies
        ]
        logger.info(f"Loaded {len(stocks)} stocks from database")
        return stocks


def _parse_stocks(spec: str) -> List[Dict[str, str]]:
    """Parse "code:name;code2:name2" format into list of dicts."""
    out: List[Dict[str, str]] = []
    if not spec:
        return out
    parts = [p.strip() for p in spec.split(";") if p.strip()]
    for p in parts:
        if ":" in p:
            code, name = p.split(":", 1)
            out.append({"code": code.strip(), "name": name.strip()})
    return out


async def news_crawl_loop(stop_event: asyncio.Event):
    """Periodic crawl loop."""
    interval = int(os.getenv("NEWS_CRAWL_INTERVAL_SECONDS", "300"))
    max_per_stock = int(os.getenv("NEWS_CRAWL_MAX_PER_STOCK", "20"))
    use_db = os.getenv("NEWS_CRAWL_USE_DB", "true").lower() in {"1", "true", "yes", "on"}

    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.warning("News worker: NAVER credentials not configured; worker will sleep")

    while not stop_event.is_set():
        try:
            if not (client_id and client_secret):
                await asyncio.sleep(interval)
                continue

            # Get stocks from DB or env variable
            if use_db:
                stocks = await _get_stocks_from_db()
            else:
                stocks_spec = os.getenv("NEWS_CRAWL_STOCKS", "005930:삼성전자")
                stocks = _parse_stocks(stocks_spec)

            if not stocks:
                logger.warning("News worker: No stocks found; check DB or NEWS_CRAWL_STOCKS")
                await asyncio.sleep(interval)
                continue

            crawler = NewsCrawler(client_id, client_secret)

            # Crawl concurrently via service API
            news_by_stock = await crawler.crawl_multiple_stocks(stocks, max_per_stock)

            # Persist
            async with AsyncSessionLocal() as db:
                total_saved = 0
                for stock in stocks:
                    items = news_by_stock.get(stock["code"], [])
                    if items:
                        saved, linked = await NewsRepository.save_news_list_for_stock(
                            db,
                            stock_code=stock["code"],
                            stock_name=stock["name"],
                            news_list=items,
                        )
                        total_saved += saved
                # concise end-of-cycle summary
                logger.info(
                    f"뉴스 크롤링 완료: 종목 {len(stocks)}개, 저장 {total_saved}건 (주기 {interval}s)"
                )
        except Exception as e:
            logger.error(f"News worker error: {e}")
        finally:
            await asyncio.sleep(interval)


def spawn_news_worker() -> asyncio.Task | None:
    """Spawn the background task if enabled by env."""
    enabled = os.getenv("NEWS_CRAWL_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        logger.info("News worker disabled (NEWS_CRAWL_ENABLED is false)")
        return None

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    task = loop.create_task(news_crawl_loop(stop_event))
    task._sl_stop_event = stop_event  # attach for shutdown
    logger.info("News worker started")
    return task
