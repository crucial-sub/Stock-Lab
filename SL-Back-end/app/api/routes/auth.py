"""
인증 관련 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserDeleteRequest

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    회원가입

    Args:
        user_in: 회원가입 정보 (name, email, phone_number, password)
        db: 데이터베이스 세션

    Returns:
        UserResponse: 생성된 유저 정보

    Raises:
        HTTPException: 이메일 또는 전화번호가 이미 존재하는 경우
    """
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
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
