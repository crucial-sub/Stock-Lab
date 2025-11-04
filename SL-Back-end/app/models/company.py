"""
기업 마스터 테이블 모델
"""
from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Company(Base):
    """
    기업 마스터 테이블
    - 모든 데이터의 중심 허브
    - corp_code (DART) ↔ stock_code (KRX) 매핑
    """
    __tablename__ = "companies"

    # Primary Key
    company_id = Column(Integer, primary_key=True, autoincrement=True, comment="기업 고유 ID")

    # Unique Keys
    corp_code = Column(
        String(8),
        unique=True,
        nullable=False,
        index=True,
        comment="DART 고유번호 (8자리)"
    )
    stock_code = Column(
        String(6),
        unique=True,
        nullable=True,
        index=True,
        comment="종목코드 (6자리) - 비상장사는 NULL"
    )

    # 기업 정보
    company_name = Column(String(200), nullable=False, index=True, comment="정식 회사명")
    company_name_eng = Column(String(200), nullable=True, comment="영문 회사명")
    stock_name = Column(String(100), nullable=True, comment="종목 약칭")
    market_type = Column(String(20), nullable=True, comment="시장 구분 (KOSPI/KOSDAQ/KONEX)")
    industry = Column(String(100), nullable=True, comment="업종")
    ceo_name = Column(String(100), nullable=True, comment="대표이사명")
    listed_date = Column(Date, nullable=True, comment="상장일")
    is_active = Column(Integer, default=1, comment="활성 상태 (1:상장중, 0:상장폐지)")

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships (lazy='selectin' for async)
    stock_prices = relationship("StockPrice", back_populates="company", lazy="selectin")
    disclosures = relationship("Disclosure", back_populates="company", lazy="selectin")
    financial_statements = relationship("FinancialStatement", back_populates="company", lazy="selectin")

    # Indexes (복합 인덱스)
    __table_args__ = (
        Index('idx_company_active_market', 'is_active', 'market_type'),
        Index('idx_company_industry', 'industry'),
        {"comment": "기업 마스터 테이블 - 모든 데이터의 중앙 허브"}
    )

    def __repr__(self):
        return f"<Company(id={self.company_id}, name={self.company_name}, code={self.stock_code})>"
