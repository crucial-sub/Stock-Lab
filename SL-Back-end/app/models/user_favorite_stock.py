"""
사용자 관심종목 모델
- 사용자가 즐겨찾기한 종목 관리
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserFavoriteStock(Base):
    """사용자 관심종목 테이블"""
    __tablename__ = "user_favorite_stocks"

    # Primary Key
    favorite_id = Column(Integer, primary_key=True, autoincrement=True, comment="관심종목 고유 ID")

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

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="등록일시")

    # Relationships
    # user = relationship("User", back_populates="favorite_stocks")
    # company = relationship("Company", back_populates="favorited_by_users")

    # Indexes & Constraints
    __table_args__ = (
        # 유니크 제약: 같은 사용자가 같은 종목을 중복 등록 불가
        UniqueConstraint('user_id', 'company_id', name='uq_user_favorite_stock'),

        # 복합 인덱스: 사용자별 관심종목 조회 최적화
        Index('idx_user_favorite_stocks_user_created', 'user_id', 'created_at'),

        {"comment": "사용자 관심종목 테이블"}
    )

    def __repr__(self):
        return f"<UserFavoriteStock(user_id={self.user_id}, stock_code={self.stock_code})>"
