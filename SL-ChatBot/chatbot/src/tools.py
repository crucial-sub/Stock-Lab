"""Tool definitions for LangChain Agent.

Defines available tools that the agent can use to perform tasks.
"""
from typing import List, Dict, Any, Optional, Union
from langchain_core.tools import tool
import aiohttp
from langchain_core.tools import BaseTool # Import BaseTool for type hinting
from db.sentiment_insights import SentimentInsightService


def get_tools(news_retriever=None, factor_sync=None) -> List:
    """Return a list of structured tools for the LangChain agent."""

    sentiment_service: Optional[SentimentInsightService] = None
    if news_retriever:
        sentiment_service = SentimentInsightService(
            backend_url=news_retriever.backend_url,
            news_retriever=news_retriever
        )
    elif factor_sync:
        sentiment_service = SentimentInsightService(
            backend_url=factor_sync.backend_url,
            news_retriever=None
        )

    # --- Tool Implementations ---
    @tool
    async def search_stock_news(keyword: str, max_results: int = 5) -> Dict:
        """지정한 키워드(종목/테마)로 최신 뉴스를 검색합니다. DB에 저장된 실제 뉴스만 반환합니다."""
        if not news_retriever:
            return {
                "success": False,
                "error": "뉴스 검색 서비스 이용 불가",
                "keyword": keyword
            }

        try:
            news_list = await news_retriever.search_news_by_keyword(
                keyword=keyword,
                max_results=max_results
            )

            if news_list and len(news_list) > 0:
                # 뉴스 데이터를 구조화된 형식으로 반환
                formatted_news = [
                    {
                        "title": news.get("title", ""),
                        "summary": news.get("summary", "")[:200],  # 첫 200자
                        "sentiment": news.get("sentiment", "neutral"),
                        "publishedAt": news.get("publishedAt", ""),
                        "source": news.get("source", "")
                    }
                    for news in news_list[:max_results]
                ]
                return {
                    "success": True,
                    "news_count": len(news_list),
                    "news_data": formatted_news,
                    "keyword": keyword,
                    "message": f"'{keyword}'에 대한 뉴스 {len(news_list)}건 조회됨"
                }
            else:
                return {
                    "success": False,
                    "news_count": 0,
                    "keyword": keyword,
                    "message": f"'{keyword}'에 대한 최신 뉴스 데이터가 없습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "keyword": keyword,
                "message": "뉴스 검색 중 오류 발생"
            }

    @tool
    async def get_factor_info(factor_name: str) -> Dict:
        """특정 투자 팩터(PER, PBR, ROE 등)의 정의/해석/활용 정보를 조회합니다."""
        if not factor_sync:
            return {"error": "Factor sync not available", "success": False}
        try:
            factor_info = await factor_sync.get_factor_info(factor_name)
            if factor_info:
                return {"success": True, "factor": factor_name, "info": factor_info}
            else:
                return {"success": False, "message": f"팩터 '{factor_name}' 정보를 찾을 수 없습니다."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def get_available_factors() -> Dict:
        """백엔드 API에서 사용 가능한 모든 투자 팩터 목록을 조회합니다."""
        if not factor_sync:
            return {"error": "Factor sync not available", "success": False}
        try:
            factors = await factor_sync.get_all_factors()
            return {"success": True, "factors": factors, "count": len(factors) if factors else 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def get_theme_sentiment_summary(limit: int = 5) -> Dict:
        """미리 분석된 시장의 주요 테마별 뉴스 감성 분석 결과를 조회합니다. 긍정적, 부정적 테마와 관련 종목 정보를 얻을 수 있습니다."""
        if news_retriever:
            backend_url = news_retriever.backend_url
        elif factor_sync:
            backend_url = factor_sync.backend_url
        else:
            return {"error": "Backend URL not configured", "success": False}

        url = f"{backend_url}/news/themes/sentiment-summary"
        params = {"limit": limit}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as resp:
                    if resp.status == 200:
                        return {"success": True, "summary": await resp.json()}
                    else:
                        return {"success": False, "error": f"Backend API error: HTTP {resp.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def interpret_theme_sentiments(limit: int = 5) -> Dict:
        """테마별 감성 점수를 심층적으로 해석하여 요약합니다."""
        if not sentiment_service:
            return {"success": False, "error": "Sentiment service unavailable"}
        try:
            insights = await sentiment_service.get_theme_sentiment_insights(limit=limit)
            return {"success": True, "insights": insights}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def get_available_themes() -> Dict:
        """백엔드 API에서 분석 가능한 모든 테마 목록을 조회합니다."""
        if news_retriever:
            backend_url = news_retriever.backend_url
        elif factor_sync:
            backend_url = factor_sync.backend_url
        else:
            return {"error": "Backend URL not configured", "success": False}
        
        url = f"{backend_url}/news/themes"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"success": True, "themes": data.get("themes", []), "count": data.get("count", 0)}
                    else:
                        return {"success": False, "error": f"Backend API error: HTTP {resp.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    def recommend_strategy(risk_tolerance: str, investment_horizon: str, preferred_style: Optional[str] = None) -> Dict:
        """사용자의 투자 성향(low, medium, high), 투자 기간(short, medium, long), 선호 스타일(value, growth, quality, momentum, dividend)에 맞는 전략 유형을 추천합니다."""
        strategy_matrix = {
            ("low", "long"): "dividend", ("low", "medium"): "value", ("low", "short"): "quality",
            ("medium", "long"): "quality", ("medium", "medium"): "multi_factor", ("medium", "short"): "value",
            ("high", "long"): "growth", ("high", "medium"): "multi_factor", ("high", "short"): "momentum"
        }
        recommended = strategy_matrix.get((risk_tolerance, investment_horizon), "multi_factor")
        if preferred_style:
            recommended = preferred_style

        strategy_details = {
            "value": {"name": "가치주(Value) 전략", "description": "저평가된 우량주 발굴", "key_factors": ["PER < 15", "PBR < 1.5"]},
            "growth": {"name": "성장주(Growth) 전략", "description": "높은 성장률을 보이는 기업 투자", "key_factors": ["매출성장률 > 20%"]},
            "quality": {"name": "우량주(Quality) 전략", "description": "재무 건전성이 뛰어난 기업", "key_factors": ["ROE > 15%"]},
            "momentum": {"name": "모멘텀(Momentum) 전략", "description": "상승 추세가 강한 종목", "key_factors": ["6개월 수익률 상위 20%"]},
            "dividend": {"name": "배당주(Dividend) 전략", "description": "안정적인 배당 수익", "key_factors": ["배당수익률 > 3%"]},
            "multi_factor": {"name": "다중팩터(Multi-Factor) 전략", "description": "여러 팩터를 조합한 균형 전략", "key_factors": ["PER < 20", "ROE > 12%"]}
        }
        return {
            "success": True,
            "recommended_strategy": recommended,
            "details": strategy_details.get(recommended, {}),
        }

    @tool
    def build_backtest_conditions(buy_conditions: List[Dict], sell_conditions: Optional[List[Dict]] = None, start_date: str = "2020-01-01", end_date: str = "2024-12-31") -> Dict:
        """백테스트용 매수/매도 조건을 정형화된 구조로 생성합니다. 조건은 'factor', 'operator', 'value'를 포함해야 합니다."""
        valid_operators = ["<", ">", "<=", ">=", "=="]
        all_conditions = buy_conditions + (sell_conditions or [])
        for condition in all_conditions:
            if condition.get("operator") not in valid_operators:
                return {"success": False, "error": f"Invalid operator: {condition.get('operator')}"}
            if not all(k in condition for k in ["factor", "operator", "value"]):
                return {"success": False, "error": f"Invalid condition structure: {condition}"}
        
        return {
            "success": True,
            "backtest_config": {
                "buy_conditions": buy_conditions,
                "sell_conditions": sell_conditions or [],
                "start_date": start_date,
                "end_date": end_date,
            }
        }

    @tool
    async def analyze_stock_sentiment(stock_code: str, stock_name: Optional[str] = None, max_results: int = 400) -> Dict:
        """종목별 7일/30일 감성 추세와 급변 감성 변화를 분석합니다."""
        if not sentiment_service or not sentiment_service.news_retriever:
            return {"success": False, "error": "News retriever not available for stock sentiment analysis"}
        try:
            analysis = await sentiment_service.analyze_stock_sentiment(
                stock_code=stock_code,
                stock_name=stock_name,
                max_results=max_results
            )
            return {"success": True, "analysis": analysis}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Return a list of all defined tools
    return [ # type: ignore
        search_stock_news,
        get_factor_info,
        get_available_factors,
        get_theme_sentiment_summary,
        interpret_theme_sentiments,
        get_available_themes,
        recommend_strategy,
        build_backtest_conditions,
        analyze_stock_sentiment,
    ]
