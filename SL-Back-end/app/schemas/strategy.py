"""
투자전략 공유 및 관리 관련 스키마
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ShareSettingsUpdate(BaseModel):
    """투자전략 공유 설정 업데이트"""
    is_public: Optional[bool] = Field(None, description="공개 여부 (랭킹에 노출)")
    is_anonymous: Optional[bool] = Field(None, description="익명 공개 여부 (이름 숨김)")
    show_strategy: Optional[bool] = Field(None, description="전략 상세 공개 여부 (팩터 조건 공개)")
    description: Optional[str] = Field(None, max_length=1000, description="투자전략 설명")


class ShareSettingsResponse(BaseModel):
    """투자전략 공유 설정 응답"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    is_public: bool
    is_anonymous: bool
    show_strategy: bool
    description: Optional[str]
    share_url: Optional[str]
    view_count: int
    like_count: int


class MyStrategyItem(BaseModel):
    """내 투자전략 목록 아이템"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    session_name: Optional[str]
    description: Optional[str]

    # 실행 정보
    status: str
    start_date: str
    end_date: str
    created_at: datetime

    # 수익률 정보
    total_return: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]

    # 공유 설정
    is_public: bool
    is_anonymous: bool
    view_count: int
    like_count: int


class RankingStrategyItem(BaseModel):
    """랭킹 투자전략 아이템"""
    model_config = ConfigDict(from_attributes=True)

    rank: int
    session_id: str
    session_name: Optional[str]
    description: Optional[str]

    # 작성자 정보 (익명 처리 가능)
    author_name: str
    is_anonymous: bool

    # 수익률 정보
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float

    # 거래 정보
    total_trades: int
    win_rate: float

    # 전략 정보 (show_strategy=True일 때만)
    show_strategy: bool
    strategy_summary: Optional[str]

    # 커뮤니티 정보
    view_count: int
    like_count: int
    created_at: datetime


class StrategyDetailResponse(BaseModel):
    """투자전략 상세 조회 (공유 링크)"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    session_name: Optional[str]
    description: Optional[str]

    # 작성자 정보
    author_name: str
    is_anonymous: bool

    # 백테스트 기간
    start_date: str
    end_date: str
    initial_capital: float
    benchmark: Optional[str]

    # 수익률 통계
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float

    # 전략 정보 (show_strategy=True일 때만 표시)
    show_strategy: bool
    buy_conditions: Optional[list]
    sell_conditions: Optional[list]

    # 커뮤니티
    view_count: int
    like_count: int
    created_at: datetime


class LikeResponse(BaseModel):
    """좋아요 응답"""
    session_id: str
    like_count: int
    is_liked: bool
