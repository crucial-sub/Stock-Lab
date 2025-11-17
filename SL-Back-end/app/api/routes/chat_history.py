"""
채팅 내역 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.chat_session import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    SaveChatRequest,
)

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_in: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    새 채팅 세션 생성

    Args:
        session_in: 세션 생성 정보
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션

    Returns:
        ChatSessionResponse: 생성된 세션 정보
    """
    new_session = ChatSession(
        user_id=current_user.user_id,
        title=session_in.title,
        mode=session_in.mode,
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return new_session


@router.get("/sessions", response_model=List[ChatSessionListResponse])
async def get_user_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    사용자의 채팅 세션 목록 조회

    Args:
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        limit: 조회할 최대 개수
        offset: 건너뛸 개수

    Returns:
        List[ChatSessionListResponse]: 세션 목록
    """
    # 세션과 마지막 메시지 조회
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.user_id)
        .options(selectinload(ChatSession.messages))
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()

    # 응답 데이터 구성
    session_list = []
    for session in sessions:
        last_message = None
        if session.messages:
            # 메시지를 정렬하여 마지막 메시지 가져오기
            sorted_messages = sorted(session.messages, key=lambda m: m.message_order)
            if sorted_messages:
                last_message = sorted_messages[-1].content

        session_list.append(
            ChatSessionListResponse(
                session_id=session.session_id,
                user_id=session.user_id,
                title=session.title,
                mode=session.mode,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=len(session.messages),
                last_message=last_message,
            )
        )

    return session_list


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    특정 채팅 세션 조회

    Args:
        session_id: 세션 ID
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션

    Returns:
        ChatSessionResponse: 세션 정보 (메시지 포함)
    """
    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.user_id,
        )
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채팅 세션을 찾을 수 없습니다",
        )

    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    채팅 세션 삭제

    Args:
        session_id: 세션 ID
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.user_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="채팅 세션을 찾을 수 없습니다",
        )

    await db.delete(session)
    await db.commit()


@router.post("/save", response_model=ChatSessionResponse)
async def save_chat(
    save_request: SaveChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    채팅 저장 (세션 + 메시지)

    기존 세션이 있으면 업데이트, 없으면 새로 생성

    Args:
        save_request: 저장할 채팅 데이터
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션

    Returns:
        ChatSessionResponse: 저장된 세션 정보
    """
    session = None

    # 기존 세션이 있으면 조회
    if save_request.session_id:
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.session_id == save_request.session_id,
                ChatSession.user_id == current_user.user_id,
            )
        )
        session = result.scalar_one_or_none()

    # 세션이 없으면 새로 생성
    if not session:
        session = ChatSession(
            user_id=current_user.user_id,
            title=save_request.title,
            mode=save_request.mode,
        )
        db.add(session)
        await db.flush()  # session_id 생성
    else:
        # 기존 세션이 있으면 기존 메시지 삭제 (덮어쓰기)
        await db.execute(
            delete(ChatMessage).where(ChatMessage.session_id == session.session_id)
        )

    # 메시지 저장
    for idx, msg in enumerate(save_request.messages):
        new_message = ChatMessage(
            session_id=session.session_id,
            role=msg.role,
            content=msg.content,
            intent=msg.intent,
            backtest_conditions=msg.backtest_conditions,
            ui_language=msg.ui_language,
            message_order=idx,
        )
        db.add(new_message)

    await db.commit()
    await db.refresh(session)

    return session
