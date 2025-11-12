"""
뉴스 크롤링 서비스
네이버 뉴스 API + 인포스탁 웹 스크래핑 통합
"""
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


class NewsAPIClient:
    """네이버 뉴스 검색 API 클라이언트"""

    def __init__(self, client_id: str, client_secret: str):
        """
        Args:
            client_id: 네이버 API Client ID
            client_secret: 네이버 API Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"

    async def search_news_async(
        self,
        query: str,
        display: int = 100,
        start: int = 1,
        sort: str = "date"
    ) -> Optional[Dict]:
        """
        비동기 뉴스 검색

        Args:
            query: 검색 키워드
            display: 검색 결과 출력 건수 (최대 100)
            start: 검색 시작 위치 (최대 1000)
            sort: 정렬 옵션 (sim: 정확도순, date: 날짜순)

        Returns:
            dict: 검색 결과
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Naver API request failed: {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"Naver API timeout: Request took longer than 10 seconds")
            return None
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Naver API connection error (check DNS/network): {e}")
            return None
        except Exception as e:
            logger.error(f"Naver API error: {e}")
            return None

    async def search_stock_news(
        self,
        stock_name: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        종목 뉴스 검색

        Args:
            stock_name: 종목명
            max_results: 최대 결과 수

        Returns:
            list: 뉴스 리스트
        """
        display = min(100, max_results)

        result = await self.search_news_async(
            stock_name,
            display=display,
            start=1,
            sort="date"
        )

        if not result:
            return []

        items = result.get('items', [])
        return items[:max_results]

    def parse_news_item(
        self,
        item: Dict,
        stock_code: str,
        stock_name: str
    ) -> Dict:
        """
        네이버 API 응답을 표준 포맷으로 변환

        Args:
            item: 네이버 API 응답 item
            stock_code: 종목코드
            stock_name: 종목명

        Returns:
            dict: 표준 포맷 뉴스
        """
        # HTML 태그 제거
        title = item.get('title', '').replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
        description = item.get('description', '').replace('<b>', '').replace('</b>', '').replace('&quot;', '"')

        # 날짜 파싱
        pub_date = item.get('pubDate', '')

        try:
            # RFC 1123 형식 파싱: "Mon, 04 Nov 2024 15:30:00 +0900"
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            iso_date = dt.isoformat()
            display_date = dt.strftime('%Y.%m.%d %H:%M')
        except:
            # 파싱 실패 시 현재 시간 사용
            dt = datetime.now()
            iso_date = dt.isoformat()
            display_date = dt.strftime('%Y.%m.%d %H:%M')

        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "title": title,
            "content": description,
            "source": "네이버",
            "date": {
                "iso": iso_date,
                "display": display_date
            },
            "link": item.get('link', ''),
            "original_link": item.get('originallink', '')
        }


class InfostockScraper:
    """인포스탁 웹 스크래핑 클라이언트"""

    def __init__(self):
        self.base_url = "https://www.infostock.co.kr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def crawl_stock_news(
        self,
        stock_code: str,
        stock_name: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        인포스탁 종목 뉴스 스크래핑

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            max_results: 최대 결과 수

        Returns:
            list: 뉴스 리스트 (표준 포맷)
        """
        news_list = []

        try:
            # 인포스탁 뉴스 검색 URL
            search_url = f"{self.base_url}/news/search"
            params = {'keyword': stock_name, 'page': 1}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    search_url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Infostock request failed: {response.status}")
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 뉴스 아이템 파싱
                    news_items = soup.select('.news-item, .article-item, .news-list-item')[:max_results]

                    for item in news_items:
                        try:
                            title_elem = item.select_one('.title, .news-title, h3, h4')
                            title = title_elem.get_text(strip=True) if title_elem else ""

                            link_elem = item.select_one('a')
                            link = link_elem.get('href', '') if link_elem else ""
                            if link and not link.startswith('http'):
                                link = f"{self.base_url}{link}"

                            content_elem = item.select_one('.summary, .content, .desc, p')
                            content = content_elem.get_text(strip=True) if content_elem else ""

                            date_elem = item.select_one('.date, .time, time')
                            date_str = date_elem.get_text(strip=True) if date_elem else ""
                            published_at = self._parse_date(date_str)

                            if title and link:
                                news_list.append({
                                    "stock_code": stock_code,
                                    "stock_name": stock_name,
                                    "title": title,
                                    "content": content,
                                    "source": "인포스탁",
                                    "date": {
                                        "iso": published_at.isoformat() if published_at else "",
                                        "display": published_at.strftime('%Y.%m.%d %H:%M') if published_at else date_str
                                    },
                                    "link": link,
                                    "original_link": link
                                })
                        except Exception as e:
                            logger.debug(f"Failed to parse Infostock news item: {e}")
                            continue

        except asyncio.TimeoutError:
            logger.error(f"Infostock timeout for {stock_name}: Request took longer than 15 seconds")
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Infostock connection error for {stock_name} (check DNS/network): {e}")
        except Exception as e:
            logger.error(f"Infostock crawling error for {stock_name}: {e}")

        return news_list

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        formats = [
            "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M",
            "%Y.%m.%d", "%Y-%m-%d",
            "%m.%d %H:%M", "%m-%d %H:%M",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.year == 1900:
                    dt = dt.replace(year=datetime.now().year)
                return dt
            except:
                continue

        return datetime.now()


class NewsCrawler:
    """통합 뉴스 크롤러 - 네이버 API + 인포스탁 스크래핑"""

    def __init__(
        self,
        naver_client_id: str = None,
        naver_client_secret: str = None,
        enable_naver: bool = True,
        enable_infostock: bool = True
    ):
        """
        Args:
            naver_client_id: 네이버 API Client ID
            naver_client_secret: 네이버 API Client Secret
            enable_naver: 네이버 크롤링 활성화
            enable_infostock: 인포스탁 크롤링 활성화
        """
        self.enable_naver = enable_naver and naver_client_id and naver_client_secret
        self.enable_infostock = enable_infostock

        self.naver_client = None
        self.infostock_client = None

        if self.enable_naver:
            self.naver_client = NewsAPIClient(naver_client_id, naver_client_secret)
            logger.info("Naver API crawler enabled")

        if self.enable_infostock:
            self.infostock_client = InfostockScraper()
            logger.info("Infostock scraper enabled")

    async def crawl_stock_news(
        self,
        stock_code: str,
        stock_name: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        특정 종목 뉴스 크롤링 (네이버 + 인포스탁 통합)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            max_results: 총 최대 결과 수

        Returns:
            list: 통합 뉴스 리스트
        """
        logger.info(f"Crawling unified news for {stock_name} ({stock_code})")

        tasks = []
        max_per_source = max_results // 2 if (self.enable_naver and self.enable_infostock) else max_results

        # 네이버 크롤링
        if self.enable_naver and self.naver_client:
            async def crawl_naver():
                raw_items = await self.naver_client.search_stock_news(stock_name, max_per_source)
                return [self.naver_client.parse_news_item(item, stock_code, stock_name) for item in raw_items]
            tasks.append(crawl_naver())

        # 인포스탁 크롤링
        if self.enable_infostock and self.infostock_client:
            tasks.append(self.infostock_client.crawl_stock_news(stock_code, stock_name, max_per_source))

        # 동시 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 통합
        all_news = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Crawler error: {result}")
            elif isinstance(result, list):
                all_news.extend(result)

        # 날짜순 정렬 (최신순)
        all_news.sort(key=lambda x: x.get("date", {}).get("iso", ""), reverse=True)

        logger.info(f"Found {len(all_news)} unified news for {stock_name}")
        return all_news[:max_results]

    async def crawl_multiple_stocks(
        self,
        stocks: List[Dict[str, str]],
        max_results_per_stock: int = 20
    ) -> Dict[str, List[Dict]]:
        """
        여러 종목 뉴스 동시 크롤링

        Args:
            stocks: 종목 리스트 [{"code": "005930", "name": "삼성전자"}, ...]
            max_results_per_stock: 종목당 최대 뉴스 수

        Returns:
            dict: {stock_code: [news_list]}
        """
        logger.info(f"Crawling unified news for {len(stocks)} stocks")

        tasks = [
            self.crawl_stock_news(stock["code"], stock["name"], max_results_per_stock)
            for stock in stocks
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        news_by_stock = {}
        for stock, news_list in zip(stocks, results):
            if isinstance(news_list, Exception):
                logger.error(f"Failed to crawl {stock['name']}: {news_list}")
                news_by_stock[stock["code"]] = []
            else:
                news_by_stock[stock["code"]] = news_list

        total_news = sum(len(news) for news in news_by_stock.values())
        logger.info(f"Crawled {total_news} total unified news for {len(stocks)} stocks")

        return news_by_stock
