"""
인증 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.cache import get_redis
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserDeleteRequest

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    회원가입

    Args:
        user_in: 회원가입 정보 (name, nickname, email, phone_number, password)
        db: 데이터베이스 세션

    Returns:
        UserResponse: 생성된 유저 정보

    Raises:
        HTTPException: 이메일, 닉네임 또는 전화번호가 이미 존재하는 경우
    """
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # 닉네임 중복 확인
    result = await db.execute(select(User).where(User.nickname == user_in.nickname))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 닉네임입니다"
        )

    # 전화번호 중복 확인
    result = await db.execute(select(User).where(User.phone_number == user_in.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 전화번호입니다"
        )

    # 비밀번호 해싱
    hashed_password = get_password_hash(user_in.password)

    # 유저 생성
    new_user = User(
        name=user_in.name,
        nickname=user_in.nickname,
        email=user_in.email,
        phone_number=user_in.phone_number,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회원가입에 실패했습니다"
        )


@router.post("/login", response_model=Token)
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    로그인

    Args:
        email: 이메일
        password: 비밀번호
        db: 데이터베이스 세션

    Returns:
        Token: JWT 액세스 토큰

    Raises:
        HTTPException: 인증 실패
    """
    # 유저 조회
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )

    # 비밀번호 확인
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )

    # 비활성화 계정 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )

    # JWT 토큰 생성
    access_token = create_access_token(
        data={"user_id": str(user.user_id), "email": user.email}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    로그아웃

    Args:
        credentials: HTTP Authorization 헤더의 토큰

    Returns:
        dict: 로그아웃 성공 메시지

    Notes:
        - Redis가 연결되어 있으면 토큰을 블랙리스트에 추가 (만료 시간까지)
        - Redis가 없으면 클라이언트 측 쿠키 삭제만으로 충분 (Stateless JWT)
    """
    token = credentials.credentials

    # Redis가 연결되어 있으면 토큰을 블랙리스트에 추가
    try:
        redis_client = get_redis()
        if redis_client:
            # 토큰 디코딩하여 만료 시간 확인
            payload = decode_access_token(token)
            if payload and "exp" in payload:
                import time
                exp_timestamp = payload["exp"]
                current_timestamp = int(time.time())
                ttl = exp_timestamp - current_timestamp

                # 만료 시간이 남아있으면 블랙리스트에 추가
                if ttl > 0:
                    blacklist_key = f"token_blacklist:{token}"
                    await redis_client.setex(blacklist_key, ttl, "1")
                    logger.info(f"Token added to blacklist with TTL: {ttl}s")
                    return {
                        "message": "로그아웃되었습니다 (토큰 무효화됨)",
                        "redis_enabled": True
                    }
    except Exception as e:
        # Redis 에러는 로깅만 하고 계속 진행
        logger.warning(f"Redis blacklist add failed: {e}")

    # Redis가 없거나 에러 발생 시 클라이언트 측 처리에만 의존
    return {
        "message": "로그아웃되었습니다",
        "redis_enabled": False
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    현재 로그인한 유저 정보 조회

    Args:
        current_user: 현재 로그인한 유저

    Returns:
        UserResponse: 유저 정보
    """
    return current_user


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    특정 유저 정보 조회

    Args:
        user_id: 조회할 유저 ID (UUID)
        db: 데이터베이스 세션
        current_user: 현재 로그인한 유저 (인증 필요)

    Returns:
        UserResponse: 유저 정보

    Raises:
        HTTPException: 유저를 찾을 수 없는 경우
    """
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저를 찾을 수 없습니다"
        )

    return user


@router.get("/check-nickname/{nickname}")
async def check_nickname_availability(
    nickname: str,
    db: AsyncSession = Depends(get_db)
):
    """
    닉네임 중복 확인

    Args:
        nickname: 확인할 닉네임
        db: 데이터베이스 세션

    Returns:
        dict: 사용 가능 여부
    """
    result = await db.execute(select(User).where(User.nickname == nickname))
    user = result.scalar_one_or_none()

    return {
        "nickname": nickname,
        "available": user is None
    }


@router.patch("/update-nickname", response_model=UserResponse)
async def update_nickname(
    new_nickname: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    닉네임 변경

    Args:
        new_nickname: 새 닉네임
        current_user: 현재 로그인한 유저
        db: 데이터베이스 세션

    Returns:
        UserResponse: 업데이트된 유저 정보

    Raises:
        HTTPException: 닉네임이 이미 사용 중인 경우
    """
    # 닉네임 중복 확인
    result = await db.execute(select(User).where(User.nickname == new_nickname))
    existing_user = result.scalar_one_or_none()

    if existing_user and existing_user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 닉네임입니다"
        )

    # 닉네임 업데이트
    current_user.nickname = new_nickname
    try:
        await db.commit()
        await db.refresh(current_user)
        return current_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="닉네임 변경에 실패했습니다"
        )


@router.delete("/delete-account", status_code=status.HTTP_200_OK)
async def delete_account(
    delete_request: UserDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    회원탈퇴

    Args:
        delete_request: 회원탈퇴 요청 정보 (email, password, phone_number)
        db: 데이터베이스 세션

    Returns:
        dict: 회원탈퇴 성공 메시지

    Raises:
        HTTPException: 인증 실패 또는 유저를 찾을 수 없는 경우
    """
    # 이메일로 유저 조회
    result = await db.execute(select(User).where(User.email == delete_request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 계정입니다"
        )

    # 비밀번호 확인
    if not verify_password(delete_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 올바르지 않습니다"
        )

    # 전화번호 확인
    if user.phone_number != delete_request.phone_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="전화번호가 올바르지 않습니다"
        )

    # 이미 비활성화된 계정인지 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 탈퇴된 계정입니다"
        )

    try:
        # 계정 삭제 (실제로는 소프트 삭제: is_active를 False로 설정)
        user.is_active = False
        await db.commit()

        return {
            "message": "회원탈퇴가 정상적으로 처리되었습니다",
            "email": user.email
        }
    except Exception as e:
        
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원탈퇴 처리 중 오류가 발생했습니다"
        )
