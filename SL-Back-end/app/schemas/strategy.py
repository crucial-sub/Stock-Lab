"""
Strategy 스키마
투자전략 관련 request/response 모델
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class StrategySharingSettings(BaseModel):
    """투자전략 공개 설정"""
    is_public: bool = Field(default=False, description="공개 여부 (랭킹 집계)")
    is_anonymous: bool = Field(default=False, description="익명 여부")
    hide_strategy_details: bool = Field(default=False, description="전략 내용 숨김 여부")


class StrategySharingUpdate(BaseModel):
    """투자전략 공개 설정 업데이트"""
    is_public: Optional[bool] = None
    is_anonymous: Optional[bool] = None
    hide_strategy_details: Optional[bool] = None


class StrategyUpdate(BaseModel):
    """투자전략 정보 업데이트"""
    strategy_name: Optional[str] = Field(default=None, description="전략 이름")
    description: Optional[str] = Field(default=None, description="전략 설명")


class StrategyListItem(BaseModel):
    """백테스트 목록 아이템 (quant/main 페이지용 - 간소화)"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    session_id: str = Field(..., serialization_alias="sessionId")
    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")
    is_active: bool = Field(default=True, serialization_alias="isActive")
    is_public: bool = Field(default=False, serialization_alias="isPublic", description="공개 여부")
    status: str = Field(..., description="상태 (PENDING/RUNNING/COMPLETED/FAILED)")
    total_return: Optional[float] = Field(None, serialization_alias="totalReturn", description="누적 수익률 (%)")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")


class StrategyStatisticsSummary(BaseModel):
    """투자전략 통계 요약 (목록용)"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    total_return: Optional[float] = Field(None, serialization_alias="totalReturn")
    annualized_return: Optional[float] = Field(None, serialization_alias="annualizedReturn")
    max_drawdown: Optional[float] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[float] = Field(None, serialization_alias="sharpeRatio")
    win_rate: Optional[float] = Field(None, serialization_alias="winRate")


class StrategyDetailItem(BaseModel):
    """백테스트 결과 상세 정보 (내 백테스트 목록용)"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    session_id: str = Field(..., serialization_alias="sessionId")
    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")
    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    description: Optional[str] = None

    # 공개 설정
    is_public: bool = Field(..., serialization_alias="isPublic")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")
    hide_strategy_details: bool = Field(..., serialization_alias="hideStrategyDetails")
    is_active: bool = Field(default=True, serialization_alias="isActive")

    # 백테스트 정보
    initial_capital: Optional[float] = Field(None, serialization_alias="initialCapital")
    backtest_start_date: Optional[date] = Field(None, serialization_alias="backtestStartDate")
    backtest_end_date: Optional[date] = Field(None, serialization_alias="backtestEndDate")

    # 실행 상태
    status: str = Field(..., description="상태 (PENDING/RUNNING/COMPLETED/FAILED)")
    progress: int = Field(default=0, description="진행률 (%)")
    error_message: Optional[str] = Field(None, serialization_alias="errorMessage")

    # 주요 통계 (빠른 접근용)
    total_return: Optional[float] = Field(None, serialization_alias="totalReturn", description="누적 수익률 (%)")

    # 통계 상세 (완료된 경우에만)
    statistics: Optional[StrategyStatisticsSummary] = None

    # 메타데이터
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")


class StrategyRankingItem(BaseModel):
    """투자전략 랭킹 아이템 (공개 랭킹 페이지용)"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")

    # 소유자 정보 (익명 설정에 따라 표시)
    owner_name: Optional[str] = Field(None, serialization_alias="ownerName")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")

    # 전략 정보 (숨김 설정에 따라 표시)
    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    description: Optional[str] = None
    hide_strategy_details: bool = Field(..., serialization_alias="hideStrategyDetails")

    # 백테스트 기간
    backtest_start_date: Optional[date] = Field(None, serialization_alias="backtestStartDate")
    backtest_end_date: Optional[date] = Field(None, serialization_alias="backtestEndDate")

    # 통계 (항상 공개)
    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: Optional[float] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[float] = Field(None, serialization_alias="sharpeRatio")
    volatility: Optional[float] = None
    win_rate: Optional[float] = Field(None, serialization_alias="winRate")

    # 거래 통계
    total_trades: Optional[int] = Field(None, serialization_alias="totalTrades")

    # 메타데이터
    created_at: datetime = Field(..., serialization_alias="createdAt")


class MyStrategiesResponse(BaseModel):
    """내 투자전략 목록 응답"""
    strategies: List[StrategyListItem]
    total: int


class StrategyRankingResponse(BaseModel):
    """공개 투자전략 랭킹 응답"""
    rankings: List[StrategyRankingItem]
    total: int
    page: int
    limit: int
    sort_by: str = Field(..., serialization_alias="sortBy")  # "total_return" or "annualized_return"


class BacktestDeleteRequest(BaseModel):
    """백테스트 삭제 요청"""
    session_ids: List[str] = Field(..., description="삭제할 백테스트 세션 ID 목록")
