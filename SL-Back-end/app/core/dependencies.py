"""
FastAPI 의존성 함수들
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import TokenData

# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    현재 로그인한 유저 가져오기

    Args:
        credentials: HTTP Authorization 헤더의 토큰
        db: 데이터베이스 세션

    Returns:
        User: 현재 유저 객체

    Raises:
        HTTPException: 토큰이 유효하지 않거나 유저를 찾을 수 없는 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("user_id")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id: UUID = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception

    # DB에서 유저 조회
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 활성화된 유저 가져오기

    Args:
        current_user: 현재 유저

    Returns:
        User: 활성화된 유저 객체

    Raises:
        HTTPException: 유저가 비활성화된 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 슈퍼유저 가져오기

    Args:
        current_user: 현재 유저

    Returns:
        User: 슈퍼유저 객체

    Raises:
        HTTPException: 슈퍼유저가 아닌 경우
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다"
        )
    return current_user
