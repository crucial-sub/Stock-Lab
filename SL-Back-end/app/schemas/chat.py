"""
Chat 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class ChatMessageCreate(BaseModel):
    """채팅 메시지 생성 스키마"""
    role: str = Field(..., description="user 또는 assistant")
    content: str = Field(..., description="메시지 내용")
    intent: Optional[str] = Field(None, description="의도 (explain, recommend, backtest 등)")
    backtest_conditions: Optional[Any] = Field(None, description="백테스트 조건 (DSL)")
    ui_language: Optional[Any] = Field(None, description="UI Language 정보")


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답 스키마"""
    message_id: UUID
    session_id: UUID
    role: str
    content: str
    intent: Optional[str] = None
    backtest_conditions: Optional[Any] = None
    ui_language: Optional[Any] = None
    message_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """채팅 세션 생성 스키마"""
    title: str = Field(..., description="세션 제목 (첫 질문)")
    mode: str = Field(default="chat", description="모드 (initial, chat, questionnaire)")


class ChatSessionResponse(BaseModel):
    """채팅 세션 응답 스키마"""
    session_id: UUID
    user_id: UUID
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """채팅 세션 목록 응답 스키마 (메시지 제외)"""
    session_id: UUID
    user_id: UUID
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(0, description="메시지 개수")
    last_message: Optional[str] = Field(None, description="마지막 메시지")

    class Config:
        from_attributes = True


class SaveChatRequest(BaseModel):
    """채팅 저장 요청 스키마"""
    session_id: Optional[UUID] = Field(None, description="기존 세션 ID (없으면 새로 생성)")
    title: str = Field(..., description="세션 제목")
    mode: str = Field(default="chat", description="모드")
    messages: List[ChatMessageCreate] = Field(..., description="저장할 메시지 목록")
