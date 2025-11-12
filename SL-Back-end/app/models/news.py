"""
뉴스 관련 데이터베이스 모델
- 뉴스 기사 저장
- 테마별 감성 분석 결과
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class NewsArticle(Base):
    """
    뉴스 기사 테이블
    - 크롤링된 뉴스 저장
    - 감성 분석 결과 포함
    """
    __tablename__ = "news"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True, comment="뉴스 기사 ID")

    # Foreign Keys
    stock_code = Column(
        String(6),
        ForeignKey("companies.stock_code", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="종목 코드"
    )

    # News Content
    title = Column(String(500), nullable=False, index=True, comment="뉴스 제목")
    content = Column(Text, nullable=True, comment="뉴스 본문")
    source = Column(String(100), nullable=True, comment="뉴스 출처 (네이버, 다음 등)")
    link = Column(String(500), unique=True, nullable=False, comment="뉴스 원문 링크")

    # Dates
    news_date = Column(DateTime, nullable=True, index=True, comment="기사 발행일시")
    crawled_at = Column(DateTime, server_default=func.now(), nullable=False, comment="크롤링 일시")

    # Company Info (저장 당시)
    company_name = Column(String(200), nullable=True, comment="회사명 (저장 당시)")

    # Sentiment Analysis
    sentiment_label = Column(
        String(20),
        nullable=True,
        comment="감성 분석 결과 (positive/negative/neutral)"
    )
    sentiment_score = Column(
        Float,
        nullable=True,
        comment="감성 점수 (-1.0 ~ 1.0)"
    )

    # Theme (Optional)
    theme = Column(String(100), nullable=True, index=True, comment="뉴스 관련 테마")

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    company = relationship("Company", lazy="selectin")

    # Indexes
    __table_args__ = (
        Index('idx_news_stock_code', 'stock_code'),
        Index('idx_news_date', 'news_date'),
        Index('idx_news_theme', 'theme'),
        Index('idx_news_title_content', 'title'),  # 검색 최적화
        Index('idx_news_sentiment', 'sentiment_label'),
        {"comment": "뉴스 기사 저장소"}
    )

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title[:30]}..., stock_code={self.stock_code})>"


class ThemeSentiment(Base):
    """
    테마별 감성 분석 요약
    - 백그라운드 워커에서 주기적으로 업데이트
    - 빠른 조회를 위한 캐시 성격
    """
    __tablename__ = "theme_sentiments"

    # Primary Key
    theme_name = Column(String(100), primary_key=True, comment="테마명")

    # Sentiment Data
    sentiment_score = Column(Float, nullable=False, comment="평균 감성 점수 (-1.0 ~ 1.0)")
    related_stocks = Column(String, nullable=True, comment="관련 종목 (쉼표로 구분)")
    summary = Column(Text, nullable=True, comment="테마 요약")

    # Counts
    positive_news_count = Column(Float, default=0, comment="긍정 뉴스 수")
    negative_news_count = Column(Float, default=0, comment="부정 뉴스 수")

    # Timestamps
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 업데이트 일시"
    )

    def __repr__(self):
        return f"<ThemeSentiment(theme={self.theme_name}, score={self.sentiment_score:.2f})>"
