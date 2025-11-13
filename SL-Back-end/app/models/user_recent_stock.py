"""
사용자 최근 본 주식 모델
- 사용자가 최근에 조회한 종목 기록
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserRecentStock(Base):
    """사용자 최근 본 주식 테이블"""
    __tablename__ = "user_recent_stocks"

    # Primary Key
    recent_id = Column(Integer, primary_key=True, autoincrement=True, comment="최근 본 종목 고유 ID")

    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="회사 ID"
    )

    # 종목 정보 (빠른 조회를 위해 중복 저장)
    stock_code = Column(String(10), nullable=False, comment="종목 코드")
    stock_name = Column(String(100), nullable=False, comment="종목명")

    # Timestamps
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="조회일시 (업데이트됨)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="최초 생성일시")

    # Relationships
    # user = relationship("User", back_populates="recent_stocks")
    # company = relationship("Company", back_populates="viewed_by_users")

    # Indexes & Constraints
    __table_args__ = (
        # 유니크 제약: 같은 사용자가 같은 종목을 중복 기록 불가
        UniqueConstraint('user_id', 'company_id', name='uq_user_recent_stock'),

        # 복합 인덱스: 사용자별 최근 본 종목 조회 최적화 (최신순)
        Index('idx_user_recent_stocks_user_viewed', 'user_id', 'viewed_at'),

        {"comment": "사용자 최근 본 주식 테이블"}
    )

    def __repr__(self):
        return f"<UserRecentStock(user_id={self.user_id}, stock_code={self.stock_code}, viewed_at={self.viewed_at})>"
