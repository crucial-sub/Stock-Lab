"""
Background theme sentiment analysis worker.
"""
import asyncio
import os
from typing import List, Dict
from loguru import logger
from sqlalchemy import select
import json
from sqlalchemy.dialects.postgresql import insert

from app.services.news_crawler import NewsCrawler
from app.core.database import AsyncSessionLocal
from app.core.config import get_settings
from app.api.routes.news import ThemeSentiment
from app.services.shared_data import AVAILABLE_THEMES


def simple_sentiment_analyzer(text: str) -> float:
    """
    간단한 키워드 기반 감성 분석기
    """
    positive_keywords = ['상승', '호황', '성장', '증가', '확대', '개선', '긍정', '수혜', '최고', '급등', '호재']
    negative_keywords = ['하락', '감소', '축소', '악화', '부정', '위기', '급락', '악재', '부진', '최악', '하락세']

    text_lower = text.lower()

    pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
    neg_count = sum(1 for kw in negative_keywords if kw in text_lower)

    if pos_count > neg_count:
        return 1.0
    elif neg_count > pos_count:
        return -1.0
    else:
        return 0.0

async def llm_sentiment_analyzer(news_titles: List[str]) -> List[float]:
    """
    LLM을 사용한 뉴스 제목 감성 분석 (Bedrock Claude 사용)
    """
    try:
        import boto3
        settings = get_settings()
        aws_region = getattr(settings, 'AWS_REGION', os.getenv('AWS_REGION', 'us-west-2'))
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region,
        )
    except ImportError:
        logger.warning("boto3가 설치되지 않아 LLM 감성 분석을 건너뜁니다.")
        return [0.0] * len(news_titles)

    scores = []
    for title in news_titles:
        prompt = f"""Human: 다음 뉴스 제목의 감성을 '긍정', '부정', '중립' 중 하나로만 분류해줘. 다른 설명은 절대 추가하지 마.
뉴스 제목: "{title}"
Assistant:"""

        body = json.dumps({
            "prompt": prompt,
            "max_tokens_to_sample": 10,
            "temperature": 0.1,
        })
        
        try:
            response = bedrock.invoke_model(body=body, modelId="anthropic.claude-instant-v1")
            result = json.loads(response.get('body').read()).get('completion', '중립').strip()
            
            if "긍정" in result: scores.append(1.0)
            elif "부정" in result: scores.append(-1.0)
            else: scores.append(0.0)
        except Exception as e:
            logger.error(f"LLM 감성 분석 API 호출 오류: {e}")
            scores.append(0.0)
    return scores


async def analyze_and_save_theme_sentiment():
    """주요 테마의 뉴스 감성을 분석하고 DB에 저장합니다."""
    logger.info("테마 감성 분석 작업 시작...")

    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.warning("Theme analyzer: NAVER 자격증명이 없어 작업을 건너뜁니다.")
        return

    crawler = NewsCrawler(client_id, client_secret)
    major_themes = [theme for theme in AVAILABLE_THEMES if theme['id'] in ['semiconductor', 'ai', 'secondary_battery', 'bio_pharma', 'robot', 'construction', 'finance']]

    async with AsyncSessionLocal() as db:
        for theme in major_themes:
            theme_name = theme['name']
            logger.info(f"'{theme_name}' 테마 뉴스 분석 중...")
            news_list = await crawler.crawl_stock_news("unknown", theme_name, max_results=50)

            if not news_list:
                logger.info(f"'{theme_name}' 테마 분석 종료: 뉴스 0건")
                continue

            news_titles = [news['title'] for news in news_list]
            # Use simple keyword-based sentiment analysis for now (faster and cheaper)
            sentiments = [simple_sentiment_analyzer(title) for title in news_titles]

            total_score = 0
            positive_count = 0
            negative_count = 0
            for sentiment in sentiments:
                total_score += sentiment
                if sentiment > 0: positive_count += 1
                if sentiment < 0: negative_count += 1

            avg_score = total_score / len(sentiments) if sentiments else 0

            # Upsert (Insert or Update) a a ThemeSentiment
            stmt = insert(ThemeSentiment).values(
                theme_name=theme_name, # type: ignore
                sentiment_score=avg_score,
                summary=f"최근 50개 뉴스 중 긍정 {positive_count}개, 부정 {negative_count}개",
                positive_news_count=positive_count,
                negative_news_count=negative_count
            ).on_conflict_do_update(
                index_elements=['theme_name'],
                set_={
                    "sentiment_score": avg_score,
                    "summary": f"최근 50개 뉴스 중 긍정 {positive_count}개, 부정 {negative_count}개",
                    "positive_news_count": positive_count,
                    "negative_news_count": negative_count,
                }
            )
            await db.execute(stmt)
            logger.info(
                f"'{theme_name}' 테마 분석 종료: 뉴스 {len(news_list)}건, 긍정 {positive_count}건, 부정 {negative_count}건, 평균 {avg_score:.2f}"
            )
        
        await db.commit()
        logger.info("테마 감성 분석 작업 완료.")

async def theme_analyzer_loop(stop_event: asyncio.Event):
    """주기적인 테마 분석 루프"""
    interval = int(os.getenv("THEME_ANALYSIS_INTERVAL_SECONDS", 3600)) # 기본 1시간
    while not stop_event.is_set():
        await analyze_and_save_theme_sentiment()
        await asyncio.sleep(interval)
