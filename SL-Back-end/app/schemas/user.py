"""
User 스키마 (Pydantic)
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    """User 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)
    nickname: str = Field(..., min_length=2, max_length=8, description="사용자 닉네임 (2~8자)")
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20, pattern=r'^\d+$')


class UserCreate(UserBase):
    """회원가입 요청 스키마"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """유저 정보 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    nickname: Optional[str] = Field(None, min_length=2, max_length=8)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, pattern=r'^\d+$')
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserInDB(UserBase):
    """DB에 저장된 User 스키마"""
    user_id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """유저 정보 응답 스키마 (비밀번호 제외)"""
    user_id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    has_kiwoom_account: bool = False  # 키움 계좌 연동 여부

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT 토큰 데이터 스키마"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


class UserDeleteRequest(BaseModel):
    """회원탈퇴 요청 스키마"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=20, pattern=r'^\d+$')
