"""
커뮤니티 게시판 관련 테이블 모델
- 게시글, 댓글, 좋아요 기능

스냅샷 데이터 구조 예시:

strategy_snapshot = {
    "strategy_name": "모멘텀 전략",
    "strategy_type": "MOMENTUM",
    "description": "...",
    "buy_conditions": [...],
    "sell_conditions": {...},
    "trade_targets": {...},
    "created_at": "2024-01-15T10:30:00"
}

session_snapshot = {
    "session_name": "2024년 1월 백테스트",
    "period": {"start": "2024-01-01", "end": "2024-06-30"},
    "initial_capital": 50000000,
    "statistics": {
        "total_return": 15.5,
        "sharpe_ratio": 1.2,
        "max_drawdown": -8.3,
        ...
    },
    "created_at": "2024-01-15T10:35:00"
}
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, ForeignKey, Index, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


def generate_uuid():
    """UUID 생성 함수"""
    return str(uuid.uuid4())


class CommunityPost(Base):
    """커뮤니티 게시글 테이블"""
    __tablename__ = "community_posts"

    post_id = Column(String(36), primary_key=True, default=generate_uuid, comment="게시글 ID (UUID)")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
        comment="작성자 ID"
    )

    # 게시글 기본 정보
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    tags = Column(JSON, nullable=True, comment="태그 목록 (예: ['질문', '초보'])")
    post_type = Column(
        String(50),
        nullable=False,
        default="DISCUSSION",
        comment="게시글 유형 (STRATEGY_SHARE/BACKTEST_RESULT/DISCUSSION/QUESTION)"
    )

    # 공개 설정
    is_public = Column(Boolean, default=True, nullable=False, comment="공개 여부")
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")

    # 커뮤니티 통계
    view_count = Column(Integer, default=0, nullable=False, comment="조회수")
    like_count = Column(Integer, default=0, nullable=False, comment="좋아요 수")
    comment_count = Column(Integer, default=0, nullable=False, comment="댓글 수")

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="작성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    user = relationship("User", back_populates="community_posts")
    # TODO: 커뮤니티 테이블 생성 후 활성화
    # strategy = relationship("PortfolioStrategy", backref="community_posts")
    # session = relationship("SimulationSession", backref="community_posts")
    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("CommunityLike", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_community_posts_type', 'post_type', 'is_public', 'created_at'),
        Index('idx_community_posts_user', 'user_id', 'created_at'),
        {"comment": "커뮤니티 게시글 테이블"}
    )


class CommunityComment(Base):
    """커뮤니티 댓글 테이블"""
    __tablename__ = "community_comments"

    comment_id = Column(String(36), primary_key=True, default=generate_uuid, comment="댓글 ID (UUID)")
    post_id = Column(
        String(36),
        ForeignKey("community_posts.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="게시글 ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
        comment="작성자 ID"
    )

    # 댓글 내용
    content = Column(Text, nullable=False, comment="댓글 내용")

    # 통계
    like_count = Column(Integer, default=0, nullable=False, comment="좋아요 수")

    # 대댓글 기능
    parent_comment_id = Column(
        String(36),
        ForeignKey("community_comments.comment_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="부모 댓글 ID (대댓글인 경우)"
    )

    # 익명 여부
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="작성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    post = relationship("CommunityPost", back_populates="comments")
    user = relationship("User", back_populates="community_comments")
    parent_comment = relationship("CommunityComment", remote_side=[comment_id], backref="replies")

    __table_args__ = (
        Index('idx_community_comments_post', 'post_id', 'created_at'),
        Index('idx_community_comments_user', 'user_id', 'created_at'),
        Index('idx_community_comments_parent', 'parent_comment_id'),
        {"comment": "커뮤니티 댓글 테이블"}
    )


class CommunityLike(Base):
    """커뮤니티 좋아요 테이블"""
    __tablename__ = "community_likes"

    like_id = Column(Integer, primary_key=True, autoincrement=True, comment="좋아요 ID")
    post_id = Column(
        String(36),
        ForeignKey("community_posts.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="게시글 ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="좋아요 누른 시간")

    # Relationships
    post = relationship("CommunityPost", back_populates="likes")
    user = relationship("User", back_populates="community_likes")

    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uq_post_user_like'),
        Index('idx_community_likes_post', 'post_id'),
        Index('idx_community_likes_user', 'user_id', 'created_at'),
        {"comment": "커뮤니티 좋아요 테이블"}
    )


class CommunityCommentLike(Base):
    """커뮤니티 댓글 좋아요 테이블"""
    __tablename__ = "community_comment_likes"

    like_id = Column(Integer, primary_key=True, autoincrement=True, comment="좋아요 ID")
    comment_id = Column(
        String(36),
        ForeignKey("community_comments.comment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="댓글 ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="좋아요 누른 시간")

    # Relationships
    comment = relationship("CommunityComment", backref="likes")
    user = relationship("User", backref="comment_likes")

    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_like'),
        Index('idx_community_comment_likes_comment', 'comment_id'),
        Index('idx_community_comment_likes_user', 'user_id', 'created_at'),
        {"comment": "커뮤니티 댓글 좋아요 테이블"}
    )
