"""Sentiment insight helpers for DB-backed data."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

import aiohttp


def _sentiment_value(label: Optional[str]) -> int:
    lookup = {
        "positive": 1,
        "negative": -1,
        "neutral": 0,
        "POSITIVE": 1,
        "NEGATIVE": -1,
        "NEUTRAL": 0,
    }
    return lookup.get(label or "neutral", 0)


@dataclass
class DailySentiment:
    date: datetime
    score_sum: int
    count: int
    positive: int
    negative: int
    neutral: int

    @property
    def average(self) -> float:
        return self.score_sum / self.count if self.count else 0.0


class SentimentInsightService:
    """Utility class that enriches DB data with sentiment interpretations."""

    def __init__(self, backend_url: str, news_retriever=None):
        self.backend_url = backend_url.rstrip("/")
        self.news_retriever = news_retriever

    async def fetch_theme_summary(self, limit: int = 5) -> Dict:
        url = f"{self.backend_url}/news/themes/sentiment-summary"
        params = {"limit": limit}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Backend responded with HTTP {resp.status}")
                return await resp.json()

    async def get_theme_sentiment_insights(self, limit: int = 5) -> Dict:
        summary = await self.fetch_theme_summary(limit=limit)
        return {
            "positive_themes": [
                self._interpret_theme_entry(entry, "positive")
                for entry in summary.get("positive_themes", [])
            ],
            "negative_themes": [
                self._interpret_theme_entry(entry, "negative")
                for entry in summary.get("negative_themes", [])
            ],
            "last_updated_at": summary.get("last_updated_at"),
        }

    def _interpret_theme_entry(self, entry: Dict, polarity: str) -> Dict:
        score = entry.get("sentiment_score", 0) or 0
        # 백엔드에서는 positive_count/negative_count로 내려오므로 두 키 모두 허용
        positive = entry.get("positive_news_count", entry.get("positive_count", 0)) or 0
        negative = entry.get("negative_news_count", entry.get("negative_count", 0)) or 0
        total = entry.get("total_count") or (positive + negative + (entry.get("neutral_count") or 0))
        intensity = abs(float(score))

        if intensity >= 0.7:
            note = "강한 매수 심리" if polarity == "positive" else "강한 경계 심리"
        elif intensity >= 0.4:
            note = "우세한 흐름" if polarity == "positive" else "뚜렷한 하락 압력"
        elif intensity >= 0.2:
            note = "완만한 개선" if polarity == "positive" else "완만한 둔화"
        else:
            note = "뚜렷하지 않은 움직임"

        dominance = "긍정" if positive >= negative else "부정"
        explanation = (
            f"{entry.get('theme_name', 'N/A')} 테마는 최근 기사에서 {dominance} 기조가 "
            f"{abs(positive - negative)}건 정도 우위를 보였습니다. {note} 단계로 해석됩니다."
        )

        return {
            "theme_name": entry.get("theme_name"),
            "sentiment_score": score,
            "summary": entry.get("summary"),
            "positive_news_count": positive,
            "negative_news_count": negative,
            "total_count": total,
            "interpretation": explanation,
            "confidence": min(1.0, (positive + negative) / 50),
        }

    async def analyze_stock_sentiment(
        self,
        stock_code: str,
        stock_name: Optional[str] = None,
        max_results: int = 400,
    ) -> Dict:
        if not self.news_retriever:
            raise RuntimeError("News retriever not configured.")

        news = await self.news_retriever.search_stock_news(
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            max_results=max_results,
        )
        daily_stats = self._aggregate_daily(news)

        return {
            "stock_code": stock_code,
            "data_points": len(news),
            "window_trends": {
                "7d": self._compute_window_trend(daily_stats, 7),
                "30d": self._compute_window_trend(daily_stats, 30),
            },
            "sudden_change": self._detect_sudden_change(daily_stats),
            "latest_articles": [
                {
                    "title": item.get("title"),
                    "sentiment": item.get("sentiment"),
                    "publishedAt": item.get("publishedAt"),
                }
                for item in news[:5]
            ],
        }

    def _aggregate_daily(self, news_list: Sequence[Dict]) -> List[DailySentiment]:
        by_date: Dict[datetime, Dict[str, int]] = defaultdict(
            lambda: {"score_sum": 0, "count": 0, "positive": 0, "negative": 0, "neutral": 0}
        )
        for article in news_list:
            date_str = article.get("publishedAt")
            if not date_str:
                continue
            try:
                day = datetime.strptime(date_str, "%Y.%m.%d")
            except ValueError:
                continue
            label = article.get("sentiment")
            value = _sentiment_value(label)
            entry = by_date[day]
            entry["score_sum"] += value
            entry["count"] += 1
            if value > 0:
                entry["positive"] += 1
            elif value < 0:
                entry["negative"] += 1
            else:
                entry["neutral"] += 1

        daily = [
            DailySentiment(
                date=day,
                score_sum=data["score_sum"],
                count=data["count"],
                positive=data["positive"],
                negative=data["negative"],
                neutral=data["neutral"],
            )
            for day, data in by_date.items()
        ]
        daily.sort(key=lambda x: x.date)
        return daily

    def _compute_window_trend(self, daily: Sequence[DailySentiment], days: int) -> Dict:
        if not daily:
            return {"window_days": days, "status": "insufficient_data"}

        cutoff = datetime.utcnow() - timedelta(days=days)
        window = [item for item in daily if item.date >= cutoff]

        if not window:
            return {"window_days": days, "status": "insufficient_data"}

        total_score = sum(item.score_sum for item in window)
        total_count = sum(item.count for item in window)
        avg_score = total_score / total_count if total_count else 0.0

        midpoint = max(1, len(window) // 2)
        early = window[:midpoint]
        late = window[midpoint:]
        early_avg = (
            sum(item.score_sum for item in early) / sum(item.count for item in early)
            if sum(item.count for item in early)
            else 0.0
        )
        late_avg = (
            sum(item.score_sum for item in late) / sum(item.count for item in late)
            if sum(item.count for item in late)
            else 0.0
        )
        delta = late_avg - early_avg

        if delta > 0.25:
            direction = "상승"
        elif delta < -0.25:
            direction = "하락"
        else:
            direction = "보합"

        dominant = max(
            ("positive", sum(item.positive for item in window)),
            ("negative", sum(item.negative for item in window)),
            ("neutral", sum(item.neutral for item in window)),
            key=lambda x: x[1],
        )[0]

        explanation = (
            f"최근 {days}일 동안 평균 감성 점수는 {avg_score:.2f}로 {direction} 흐름을 보입니다. "
            f"{dominant} 기사가 상대적으로 많았습니다."
        )

        return {
            "window_days": days,
            "status": "ok",
            "avg_score": round(avg_score, 2),
            "direction": direction,
            "momentum": round(delta, 2),
            "dominant_sentiment": dominant,
            "article_count": total_count,
            "explanation": explanation,
        }

    def _detect_sudden_change(self, daily: Sequence[DailySentiment]) -> Optional[Dict]:
        if len(daily) < 4:
            return None

        recent = daily[-1]
        prior_window = daily[-4:-1]
        prior_count = sum(item.count for item in prior_window)
        if prior_count == 0:
            return None

        prior_avg = sum(item.score_sum for item in prior_window) / prior_count
        change = recent.average - prior_avg

        if abs(change) < 0.6:
            return None

        direction = "급등" if change > 0 else "급락"
        description = (
            f"{recent.date.strftime('%Y-%m-%d')} 기준 감성 점수가 {change:+.2f}만큼 {direction}했습니다. "
            "최근 기사에서 정서 변화가 크게 나타났습니다."
        )

        return {
            "date": recent.date.strftime("%Y-%m-%d"),
            "change": round(change, 2),
            "direction": direction,
            "description": description,
            "recent_avg": round(recent.average, 2),
            "previous_avg": round(prior_avg, 2),
        }
