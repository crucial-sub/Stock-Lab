"""
유니버스 분류 히스토리 테이블 모델
"""
from sqlalchemy import Column, Integer, String, Date, Index
from app.core.database import Base


class StockUniverseHistory(Base):
    """
    종목별 유니버스 분류 히스토리
    - 매 거래일마다 각 종목이 어느 유니버스에 속하는지 기록
    """
    __tablename__ = "stock_universe_history"

    # Primary Key (복합키)
    id = Column(Integer, primary_key=True, autoincrement=True, comment="고유 ID")

    # 분류 정보
    stock_code = Column(String(6), nullable=False, index=True, comment="종목코드")
    universe_id = Column(String(50), nullable=False, index=True, comment="유니버스 ID (예: KOSPI_MEGA)")
    trade_date = Column(Date, nullable=False, index=True, comment="거래일")

    # 시가총액 정보 (참고용)
    market_cap = Column(Integer, nullable=True, comment="시가총액 (원)")

    # 복합 인덱스
    __table_args__ = (
        Index('idx_universe_date', 'universe_id', 'trade_date'),
        Index('idx_stock_date', 'stock_code', 'trade_date'),
    )
