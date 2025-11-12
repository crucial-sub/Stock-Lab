"""
주식 시세 테이블 모델
대용량 데이터 (틱데이터 포함 시 수억 건)
"""
from sqlalchemy import Column, Integer, BigInteger, Float, Date, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class StockPrice(Base):
    """
    주식 시세 테이블
    - 일별 OHLCV 데이터
    - 대용량 데이터: 2,500종목 × 5년 × 250일 = 3,125,000건
    - 틱데이터 추가 시: 수억 건 이상
    """
    __tablename__ = "stock_prices"

    # Primary Key
    price_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="시세 고유 ID")

    # Foreign Key
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기업 참조 ID"
    )

    # 거래 정보
    trade_date = Column(Date, nullable=False, index=True, comment="거래일자")
    open_price = Column(Integer, nullable=True, comment="시가 (원)")
    high_price = Column(Integer, nullable=True, comment="고가 (원)")
    low_price = Column(Integer, nullable=True, comment="저가 (원)")
    close_price = Column(Integer, nullable=True, index=True, comment="종가 (원)")
    volume = Column(BigInteger, nullable=True, comment="거래량 (주)")
    trading_value = Column(BigInteger, nullable=True, comment="거래대금 (원)")

    # 변동 정보
    change_vs_1d = Column(Integer, nullable=True, comment="1일 전일대비 (원)")
    fluctuation_rate = Column(Float, nullable=True, comment="등락률 (%)")

    # 시가총액 정보
    market_cap = Column(BigInteger, nullable=True, comment="시가총액 (원)")
    listed_shares = Column(BigInteger, nullable=True, comment="상장주식수 (주)")

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")

    # Relationships
    company = relationship("Company", back_populates="stock_prices")

    # Indexes (성능 최적화)
    __table_args__ = (
        # 유니크 제약: 같은 종목의 같은 날짜는 1개만
        UniqueConstraint('company_id', 'trade_date', name='uq_stock_prices_company_date'),

        # 복합 인덱스: 날짜 범위 조회 최적화 (백테스팅용)
        Index('idx_stock_prices_date_company', 'trade_date', 'company_id'),

        # 복합 인덱스: 종목별 시계열 조회 최적화
        Index('idx_stock_prices_company_date_close', 'company_id', 'trade_date', 'close_price'),

        # 시가총액 정렬 조회용
        Index('idx_stock_prices_date_marketcap', 'trade_date', 'market_cap'),

        # 거래량 상위 종목 조회용
        Index('idx_stock_prices_date_volume', 'trade_date', 'volume'),

        # 등락률 정렬 조회용
        Index('idx_stock_prices_date_fluctuation', 'trade_date', 'fluctuation_rate'),

        # 거래대금 정렬 조회용
        Index('idx_stock_prices_date_trading_value', 'trade_date', 'trading_value'),

        {"comment": "주식 시세 테이블 - 일별 OHLCV 데이터"}
    )

    def __repr__(self):
        return f"<StockPrice(company_id={self.company_id}, date={self.trade_date}, close={self.close_price})>"
