"""
뉴스 관련 데이터베이스 모델 (DB 조회 전용)
- 뉴스 기사 저장/조회
- 테마별 감성 분석 결과 (읽기 전용)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class NewsArticle(Base):
    """
    뉴스 기사 테이블 (읽기 전용)
    - 뉴스 기사 조회
    - 감성 분석 결과 포함
    """
    __tablename__ = "news"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True, comment="뉴스 기사 ID")

    # News Content
    stock_code = Column(String(20), nullable=True, comment="종목 코드")
    title = Column(Text, nullable=True, comment="뉴스 제목")
    content = Column(Text, nullable=True, comment="뉴스 본문")
    llm_summary = Column(Text, nullable=True, comment="LLM 생성 요약")
    
    source = Column(String(100), nullable=True, comment="뉴스 출처")
    link = Column(Text, nullable=True, comment="뉴스 원문 링크")
    media_domain = Column(String(50), nullable=True, comment="언론사 도메인/코드")

    # Dates
    news_date = Column(Date, nullable=True, comment="기사 발행일")

    # Sentiment Analysis
    sentiment_label = Column(String(20), nullable=True, comment="감성 분석 결과")
    sentiment_score = Column(Integer, nullable=True, comment="감성 점수")
    sentiment_confidence = Column(Integer, nullable=True, comment="감성 신뢰도")
    risk_tags = Column(JSON, nullable=True, comment="위험 태그")

    # Timestamps
    analyzed_at = Column(DateTime, nullable=True, comment="분석 일시")
    crawled_at = Column(DateTime, nullable=True, comment="크롤링 일시")

    # Company Info (저장 당시)
    company_name = Column(String(255), nullable=True, comment="회사명 (저장 당시)")

    # Theme
    theme = Column(String(100), nullable=True, comment="뉴스 관련 테마")
    theme_code = Column(String(50), nullable=True, comment="테마 코드")

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title[:30] if self.title else ''}..., stock_code={self.stock_code})>"


class ThemeSentiment(Base):
    """
    테마별 감성 분석 요약 (읽기 전용)
    - 사전 분석된 감성 데이터
    - 빠른 조회를 위한 캐시
    """
    __tablename__ = "theme_sentiments"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")

    # Theme Data
    theme = Column(String(100), nullable=True, comment="테마명")
    theme_code = Column(String(50), nullable=True, comment="테마 코드")

    # Sentiment Data
    avg_sentiment_score = Column(Integer, nullable=True, comment="평균 감성 점수")
    sentiment_label = Column(String(20), nullable=True, comment="감성 분류")

    # Counts
    total_count = Column(Integer, nullable=True, comment="총 뉴스 수")
    positive_count = Column(Integer, nullable=True, comment="긍정 뉴스 수")
    negative_count = Column(Integer, nullable=True, comment="부정 뉴스 수")
    neutral_count = Column(Integer, nullable=True, comment="중립 뉴스 수")

    # Risk Tags
    top_risk_tags = Column(JSON, nullable=True, comment="상위 위험 태그")

    # Window
    window_start = Column(DateTime, nullable=True, comment="분석 윈도우 시작")
    window_end = Column(DateTime, nullable=True, comment="분석 윈도우 종료")
    calculated_at = Column(DateTime, server_default=func.now(), nullable=True, comment="계산 일시")

    def __repr__(self):
        return f"<ThemeSentiment(theme={self.theme}, score={self.avg_sentiment_score})>"
