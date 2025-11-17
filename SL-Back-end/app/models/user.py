"""
User 모델
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    nickname = Column(String(8), unique=True, index=True, nullable=True, comment="사용자 닉네임 (2~8자)")
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # 키움증권 API 연동 정보
    kiwoom_app_key = Column(String(255), nullable=True)
    kiwoom_app_secret = Column(String(255), nullable=True)
    kiwoom_access_token = Column(String(512), nullable=True)
    kiwoom_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    simulation_sessions = relationship("SimulationSession", back_populates="user", lazy="selectin")
    community_posts = relationship("CommunityPost", back_populates="user")
    community_comments = relationship("CommunityComment", back_populates="user")
    community_likes = relationship("CommunityLike", back_populates="user")
    auto_trading_strategies = relationship("AutoTradingStrategy", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, name={self.name}, email={self.email}, phone={self.phone_number})>"
