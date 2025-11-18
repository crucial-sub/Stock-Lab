"""
커뮤니티 API 스키마
- 게시글, 댓글, 좋아요 관련 Request/Response 스키마
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============================================================
# 게시글 관련 스키마
# ============================================================

class PostCreate(BaseModel):
    """게시글 작성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    content: str = Field(..., min_length=1, description="내용")
    tags: Optional[List[str]] = Field(None, description="태그 목록")
    post_type: str = Field("DISCUSSION", description="게시글 유형 (STRATEGY_SHARE/DISCUSSION/QUESTION)")

    # 전략 공유인 경우
    strategy_id: Optional[str] = Field(None, description="공유할 전략 ID")
    session_id: Optional[str] = Field(None, description="공유할 백테스트 세션 ID")
    is_anonymous: bool = Field(False, description="익명 여부")


class PostUpdate(BaseModel):
    """게시글 수정 요청"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class PostSummary(BaseModel):
    """게시글 목록용 요약 정보"""
    post_id: str = Field(..., serialization_alias="postId")
    title: str
    content_preview: str = Field(..., serialization_alias="contentPreview", description="내용 미리보기 (한 줄)")
    author_nickname: Optional[str] = Field(None, serialization_alias="authorNickname")
    author_id: Optional[str] = Field(None, serialization_alias="authorId", description="작성자 ID")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")
    tags: Optional[List[str]] = None
    post_type: str = Field(..., serialization_alias="postType")
    session_snapshot: Optional['SessionSnapshot'] = Field(
        None, serialization_alias="sessionSnapshot"
    )

    # 통계
    view_count: int = Field(..., serialization_alias="viewCount")
    like_count: int = Field(..., serialization_alias="likeCount")
    comment_count: int = Field(..., serialization_alias="commentCount")

    # 시간
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    class Config:
        populate_by_name = True


class StrategySnapshot(BaseModel):
    """전략 스냅샷 (공유용)"""
    strategy_name: str = Field(..., serialization_alias="strategyName")
    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    description: Optional[str] = None
    buy_conditions: List[dict] = Field(..., serialization_alias="buyConditions")
    sell_conditions: dict = Field(..., serialization_alias="sellConditions")
    trade_targets: dict = Field(..., serialization_alias="tradeTargets")

    class Config:
        populate_by_name = True


class SessionSnapshot(BaseModel):
    """백테스트 세션 스냅샷 (공유용)"""
    initial_capital: Decimal = Field(..., serialization_alias="initialCapital")
    start_date: str = Field(..., serialization_alias="startDate")
    end_date: str = Field(..., serialization_alias="endDate")
    total_return: Decimal = Field(..., serialization_alias="totalReturn")
    annualized_return: Optional[Decimal] = Field(None, serialization_alias="annualizedReturn")
    max_drawdown: Optional[Decimal] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[Decimal] = Field(None, serialization_alias="sharpeRatio")
    win_rate: Optional[Decimal] = Field(None, serialization_alias="winRate")

    @field_serializer('initial_capital', 'total_return', 'annualized_return', 'max_drawdown', 'sharpe_ratio', 'win_rate')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

    class Config:
        populate_by_name = True


class PostDetail(BaseModel):
    """게시글 상세 정보"""
    post_id: str = Field(..., serialization_alias="postId")
    title: str
    content: str
    author_nickname: Optional[str] = Field(None, serialization_alias="authorNickname")
    author_id: Optional[str] = Field(None, serialization_alias="authorId", description="작성자 ID (본인 여부 확인용)")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")
    tags: Optional[List[str]] = None
    post_type: str = Field(..., serialization_alias="postType")

    # 전략 공유 정보
    strategy_snapshot: Optional[StrategySnapshot] = Field(None, serialization_alias="strategySnapshot")
    session_snapshot: Optional[SessionSnapshot] = Field(None, serialization_alias="sessionSnapshot")

    # 통계
    view_count: int = Field(..., serialization_alias="viewCount")
    like_count: int = Field(..., serialization_alias="likeCount")
    comment_count: int = Field(..., serialization_alias="commentCount")
    is_liked: bool = Field(False, serialization_alias="isLiked", description="현재 사용자의 좋아요 여부")

    # 시간
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    class Config:
        populate_by_name = True


class PostListResponse(BaseModel):
    """게시글 목록 응답"""
    posts: List[PostSummary]
    total: int
    page: int
    limit: int
    has_next: bool = Field(..., serialization_alias="hasNext")

    class Config:
        populate_by_name = True


# ============================================================
# 댓글 관련 스키마
# ============================================================

class CommentCreate(BaseModel):
    """댓글 작성 요청"""
    content: str = Field(..., min_length=1, description="댓글 내용")
    parent_comment_id: Optional[str] = Field(None, serialization_alias="parentCommentId", description="부모 댓글 ID (대댓글인 경우)")
    is_anonymous: bool = Field(False, serialization_alias="isAnonymous")

    class Config:
        populate_by_name = True


class CommentUpdate(BaseModel):
    """댓글 수정 요청"""
    content: str = Field(..., min_length=1)


class CommentItem(BaseModel):
    """댓글 정보"""
    comment_id: str = Field(..., serialization_alias="commentId")
    post_id: str = Field(..., serialization_alias="postId")
    content: str
    author_nickname: Optional[str] = Field(None, serialization_alias="authorNickname")
    author_id: Optional[str] = Field(None, serialization_alias="authorId")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")
    parent_comment_id: Optional[str] = Field(None, serialization_alias="parentCommentId")
    like_count: int = Field(..., serialization_alias="likeCount")
    is_liked: bool = Field(False, serialization_alias="isLiked")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")

    # 대댓글 목록 (재귀)
    replies: List['CommentItem'] = []

    class Config:
        populate_by_name = True


class CommentListResponse(BaseModel):
    """댓글 목록 응답"""
    comments: List[CommentItem]
    total: int


# ============================================================
# 좋아요 관련 스키마
# ============================================================

class LikeResponse(BaseModel):
    """좋아요 응답"""
    is_liked: bool = Field(..., serialization_alias="isLiked", description="좋아요 상태")
    like_count: int = Field(..., serialization_alias="likeCount", description="총 좋아요 수")

    class Config:
        populate_by_name = True


# ============================================================
# 랭킹 관련 스키마
# ============================================================

class RankingItem(BaseModel):
    """수익률 랭킹 항목"""
    rank: int = Field(..., description="순위")
    strategy_id: str = Field(..., serialization_alias="strategyId")
    session_id: str = Field(..., serialization_alias="sessionId")
    strategy_name: str = Field(..., serialization_alias="strategyName")
    author_nickname: Optional[str] = Field(None, serialization_alias="authorNickname")
    total_return: Decimal = Field(..., serialization_alias="totalReturn")
    annualized_return: Optional[Decimal] = Field(None, serialization_alias="annualizedReturn")
    max_drawdown: Optional[Decimal] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[Decimal] = Field(None, serialization_alias="sharpeRatio")

    @field_serializer('total_return', 'annualized_return', 'max_drawdown', 'sharpe_ratio')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None

    class Config:
        populate_by_name = True


class TopRankingsResponse(BaseModel):
    """상위 랭킹 응답 (상위 3개)"""
    rankings: List[RankingItem]
    updated_at: datetime = Field(..., serialization_alias="updatedAt", description="마지막 업데이트 시간")

    class Config:
        populate_by_name = True

# ForwardRef 해제
PostSummary.model_rebuild()


class RankingListResponse(BaseModel):
    """전체 랭킹 목록 응답"""
    rankings: List[RankingItem]
    total: int
    page: int
    limit: int

    class Config:
        populate_by_name = True


# ============================================================
# 전략 복제 관련 스키마
# ============================================================

class CloneStrategyData(BaseModel):
    """전략 복제 데이터"""
    # 기본 설정
    strategy_name: str = Field(..., serialization_alias="strategyName")
    is_day_or_month: str = Field(..., serialization_alias="isDayOrMonth")
    initial_investment: int = Field(..., serialization_alias="initialInvestment")
    start_date: str = Field(..., serialization_alias="startDate")
    end_date: str = Field(..., serialization_alias="endDate")
    commission_rate: float = Field(..., serialization_alias="commissionRate")
    slippage: float = Field(..., serialization_alias="slippage")

    # 매수 조건
    buy_conditions: List[dict] = Field(..., serialization_alias="buyConditions")
    buy_logic: str = Field(..., serialization_alias="buyLogic")
    priority_factor: Optional[str] = Field(None, serialization_alias="priorityFactor")
    priority_order: str = Field(..., serialization_alias="priorityOrder")

    # 매수 비중
    per_stock_ratio: float = Field(..., serialization_alias="perStockRatio")
    max_holdings: int = Field(..., serialization_alias="maxHoldings")
    max_buy_value: Optional[int] = Field(None, serialization_alias="maxBuyValue")
    max_daily_stock: Optional[int] = Field(None, serialization_alias="maxDailyStock")
    buy_price_basis: str = Field(..., serialization_alias="buyPriceBasis")
    buy_price_offset: float = Field(..., serialization_alias="buyPriceOffset")

    # 매도 조건
    target_and_loss: Optional[dict] = Field(None, serialization_alias="targetAndLoss")
    hold_days: Optional[dict] = Field(None, serialization_alias="holdDays")
    condition_sell: Optional[dict] = Field(None, serialization_alias="conditionSell")

    # 매매 대상
    trade_targets: dict = Field(..., serialization_alias="tradeTargets")

    class Config:
        populate_by_name = True
