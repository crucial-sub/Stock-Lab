"""
투자 전략 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DisplayCondition(BaseModel):
    """UI 표시용 조건"""
    condition: str = Field(..., description="조건 표시 문자열 (예: ROE > 15%)")
    condition_info: List[str] = Field(..., description="조건 설명 배열")


class StrategyRecommendationRequest(BaseModel):
    """전략 추천 요청"""
    user_tags: List[str] = Field(..., description="사용자 설문 결과 태그", min_length=1)
    top_n: int = Field(default=3, description="추천할 전략 개수", ge=1, le=10)


class StrategyMatch(BaseModel):
    """추천된 전략 정보 (목록용)"""
    id: str = Field(..., description="전략 ID")
    name: str = Field(..., description="전략명")
    summary: str = Field(..., description="전략 요약")
    tags: List[str] = Field(..., description="전략 태그")
    match_score: int = Field(..., description="매칭 점수 (0-100)", ge=0, le=100)
    matched_tags: List[str] = Field(..., description="일치하는 태그")
    unmatched_tags: List[str] = Field(..., description="일치하지 않는 태그")
    display_conditions: List[DisplayCondition] = Field(..., description="UI 표시용 조건")


class StrategyDetail(BaseModel):
    """전략 상세 정보 (백테스트 실행용)"""
    id: str = Field(..., description="전략 ID")
    name: str = Field(..., description="전략명")
    summary: str = Field(..., description="전략 요약")
    description: Optional[str] = Field(None, description="전략 상세 설명")
    tags: List[str] = Field(..., description="전략 태그")
    backtest_config: Dict[str, Any] = Field(..., description="백테스트 실행 설정")
    display_conditions: List[DisplayCondition] = Field(..., description="UI 표시용 조건")
    popularity_score: int = Field(..., description="인기도 점수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")


class InvestmentStrategyCreate(BaseModel):
    """전략 생성 요청 (관리자용)"""
    id: str = Field(..., description="전략 ID")
    name: str = Field(..., description="전략명")
    summary: str = Field(..., description="전략 요약")
    description: Optional[str] = Field(None, description="전략 상세 설명")
    tags: List[str] = Field(..., description="전략 태그", min_length=1)
    backtest_config: Dict[str, Any] = Field(..., description="백테스트 실행 설정")
    display_conditions: List[DisplayCondition] = Field(..., description="UI 표시용 조건")
