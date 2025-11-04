"""
배당 정보 테이블 모델
배당수익률 팩터 계산을 위한 추가 테이블
"""
from sqlalchemy import Column, Integer, String, DECIMAL, Date, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DividendInfo(Base):
    """
    배당 정보 테이블
    - 배당 공시 정보
    - 배당수익률 계산용
    """
    __tablename__ = "dividend_info"

    # Primary Key
    dividend_id = Column(Integer, primary_key=True, autoincrement=True, comment="배당 고유 ID")

    # Foreign Key
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기업 참조 ID"
    )

    # 배당 정보
    fiscal_year = Column(String(4), nullable=False, comment="회계연도")
    dividend_type = Column(String(50), nullable=True, comment="배당 구분 (현금배당/주식배당/중간배당)")

    # 배당금액
    cash_dividend_per_share = Column(DECIMAL(15, 2), nullable=True, comment="주당 현금배당금 (원)")
    stock_dividend_ratio = Column(DECIMAL(10, 4), nullable=True, comment="주식배당 비율 (%)")
    total_dividend_amount = Column(DECIMAL(20, 2), nullable=True, comment="배당금 총액 (원)")

    # 배당 기준일
    record_date = Column(Date, nullable=True, comment="배당 기준일")
    payment_date = Column(Date, nullable=True, comment="배당 지급일")
    announcement_date = Column(Date, nullable=True, comment="배당 공시일")

    # 배당성향
    dividend_payout_ratio = Column(DECIMAL(10, 4), nullable=True, comment="배당성향 (%)")

    # 공시 연동
    rcept_no = Column(String(20), nullable=True, comment="DART 접수번호")

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    company = relationship("Company", backref="dividends")

    # Indexes
    __table_args__ = (
        Index('idx_dividend_company_year', 'company_id', 'fiscal_year'),
        Index('idx_dividend_record_date', 'record_date'),
        {"comment": "배당 정보 테이블 - 배당수익률 계산용"}
    )

    def __repr__(self):
        return f"<DividendInfo(company_id={self.company_id}, year={self.fiscal_year}, dividend={self.cash_dividend_per_share})>"