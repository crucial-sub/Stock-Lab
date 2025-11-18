"""
Chat Session 모델
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ChatSession(Base):
    """채팅 세션 모델 - 사용자별 대화 세션 관리"""
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)  # 첫 질문으로 자동 생성
    mode = Column(String(50), default="chat", nullable=False)  # initial, chat, questionnaire

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<ChatSession(session_id={self.session_id}, user_id={self.user_id}, title={self.title})>"


class ChatMessage(Base):
    """채팅 메시지 모델 - 각 세션의 개별 메시지"""
    __tablename__ = "chat_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)

    # 추가 메타데이터 (선택사항)
    intent = Column(String(100), nullable=True)  # explain, recommend, backtest, etc.
    backtest_conditions = Column(JSONB, nullable=True)  # DSL 조건이 있을 경우
    ui_language = Column(JSONB, nullable=True)  # UI Language 정보

    message_order = Column(Integer, nullable=False)  # 메시지 순서
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages", lazy="selectin")

    def __repr__(self):
        return f"<ChatMessage(message_id={self.message_id}, session_id={self.session_id}, role={self.role})>"
