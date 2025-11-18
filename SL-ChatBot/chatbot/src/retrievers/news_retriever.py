"""뉴스 검색 모듈
Backend 뉴스 API를 통해 실시간 뉴스 검색
"""
from typing import List, Dict, Optional
import aiohttp
from datetime import datetime


class NewsRetriever:
    """Backend API 기반 뉴스 검색"""

    def __init__(self, backend_url: str = "http://backend:8000/api/v1"):
        self.backend_url = backend_url

    async def search_stock_news(
        self,
        stock_code: str,
        stock_name: str,
        max_results: int = 10
    ) -> List[Dict]:
       
        url = f"{self.backend_url}/news/db/stock/{stock_code}"
        params = {"limit": max_results}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("news", [])
                    else:
                        print(f"[WARN] Failed to fetch news for {stock_name}: HTTP {resp.status}")
                        return []

        except Exception as e:
            print(f"[ERROR] News retrieval error for {stock_name}: {e}")
            return []

    async def search_news_by_keyword(
        self,
        keyword: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        키워드로 뉴스 검색

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수

        Returns:
            뉴스 리스트
        """
        url = f"{self.backend_url}/news/db/search"
        params = {"keyword": keyword, "limit": max_results}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("news", [])
                    else:
                        print(f"[WARN] Failed to search news for '{keyword}': HTTP {resp.status}")
                        return []

        except Exception as e:
            print(f"[ERROR] News search error for '{keyword}': {e}")
            return []

    def format_news_for_context(self, news_list: List[Dict], top_k: int = 5) -> str:
        """
        뉴스를 LLM 컨텍스트 형식으로 변환

        Args:
            news_list: 뉴스 리스트
            top_k: 상위 몇 개만 포함할지

        Returns:
            포맷팅된 뉴스 컨텍스트 문자열
        """
        if not news_list:
            return ""

        context_parts = ["[최신 뉴스]"]

        for i, news in enumerate(news_list[:top_k], 1):
            title = news.get("title", "제목 없음")
            content = news.get("content", "")
            date = news.get("date", {}).get("display", "날짜 미상")
            source = news.get("source", "출처 미상")

            news_text = f"{i}. {title}\n   - 날짜: {date}\n   - 출처: {source}"
            if content:
                # 내용이 너무 길면 잘라내기
                preview = content[:150] + "..." if len(content) > 150 else content
                news_text += f"\n   - 요약: {preview}"

            context_parts.append(news_text)

        return "\n\n".join(context_parts)

    # detect_and_search_news는 LangChain tool 사용 패턴으로 대체되어 제거되었습니다.
