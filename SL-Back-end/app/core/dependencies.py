"""
FastAPI 의존성 함수들
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import TokenData
from app.core.cache import get_redis

logger = logging.getLogger(__name__)

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

    # Redis가 있으면 블랙리스트 체크
    try:
        redis_client = get_redis()
        if redis_client:
            blacklist_key = f"token_blacklist:{token}"
            is_blacklisted = await redis_client.exists(blacklist_key)
            if is_blacklisted:
                logger.info(f"Blocked blacklisted token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="로그아웃된 토큰입니다",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except HTTPException:
        raise
    except Exception as e:
        # Redis 에러는 로깅만 하고 계속 진행 (Redis 없어도 작동하도록)
        logger.warning(f"Redis blacklist check failed: {e}")

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

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    현재 로그인한 유저 가져오기 (Optional)

    토큰이 없어도 에러를 발생시키지 않고 None을 반환합니다.
    공개 API에서 로그인 여부에 따라 다른 동작을 할 때 사용합니다.

    Args:
        credentials: HTTP Authorization 헤더의 토큰 (optional)
        db: 데이터베이스 세션

    Returns:
        Optional[User]: 현재 유저 객체 또는 None (비로그인)
    """
    # 토큰이 없으면 None 반환
    if credentials is None:
        return None

    token = credentials.credentials

    # Redis가 있으면 블랙리스트 체크
    try:
        redis_client = get_redis()
        if redis_client:
            blacklist_key = f"token_blacklist:{token}"
            is_blacklisted = await redis_client.exists(blacklist_key)
            if is_blacklisted:
                logger.info(f"Blocked blacklisted token")
                return None
    except Exception as e:
        logger.warning(f"Redis blacklist check failed: {e}")

    # 토큰 디코드
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id_str: Optional[str] = payload.get("user_id")
    if user_id_str is None:
        return None

    try:
        user_id: UUID = UUID(user_id_str)
    except (ValueError, AttributeError):
        return None

    # DB에서 유저 조회
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user