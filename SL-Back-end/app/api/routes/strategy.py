"""
투자전략 관리 및 공유 API
- 내 투자전략 관리
- 공유 설정
- 랭킹 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Optional
from datetime import date
import secrets

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.simulation import SimulationSession, SimulationStatistics
from app.schemas.strategy import (
    ShareSettingsUpdate,
    ShareSettingsResponse,
    MyStrategyItem,
    RankingStrategyItem,
    StrategyDetailResponse,
    LikeResponse
)

router = APIRouter()


def generate_share_url(session_id: str) -> str:
    """공유 URL 슬러그 생성"""
    random_suffix = secrets.token_urlsafe(8)
    return f"{session_id[:8]}-{random_suffix}"


@router.get("/my-strategies", response_model=List[MyStrategyItem])
async def get_my_strategies(
    current_user: User = Depends(get_current_active_user),
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    내 투자전략 목록 조회

    Args:
        status_filter: 상태 필터 (COMPLETED, RUNNING, FAILED 등)
        current_user: 현재 로그인 사용자
        db: 데이터베이스 세션

    Returns:
        내 투자전략 목록
    """
    query = (
        select(
            SimulationSession,
            SimulationStatistics.total_return,
            SimulationStatistics.sharpe_ratio,
            SimulationStatistics.max_drawdown
        )
        .outerjoin(SimulationStatistics, SimulationSession.session_id == SimulationStatistics.session_id)
        .where(SimulationSession.user_id == current_user.user_id)
    )

    if status_filter:
        query = query.where(SimulationSession.status == status_filter)

    query = query.order_by(SimulationSession.created_at.desc())

    result = await db.execute(query)
    strategies = result.all()

    return [
        MyStrategyItem(
            session_id=session.session_id,
            session_name=session.session_name,
            description=session.description,
            status=session.status,
            start_date=session.start_date.isoformat() if session.start_date else "",
            end_date=session.end_date.isoformat() if session.end_date else "",
            created_at=session.created_at,
            total_return=float(total_return) if total_return else None,
            sharpe_ratio=float(sharpe_ratio) if sharpe_ratio else None,
            max_drawdown=float(max_drawdown) if max_drawdown else None,
            is_public=session.is_public,
            is_anonymous=session.is_anonymous,
            view_count=session.view_count,
            like_count=session.like_count
        )
        for session, total_return, sharpe_ratio, max_drawdown in strategies
    ]


@router.patch("/{session_id}/share-settings", response_model=ShareSettingsResponse)
async def update_share_settings(
    session_id: str,
    settings: ShareSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투자전략 공유 설정 업데이트

    Args:
        session_id: 투자전략 세션 ID
        settings: 공유 설정 (공개 여부, 익명, 전략 공개)
        current_user: 현재 로그인 사용자
        db: 데이터베이스 세션

    Returns:
        업데이트된 공유 설정
    """
    # 투자전략 조회 및 권한 확인
    result = await db.execute(
        select(SimulationSession).where(SimulationSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없습니다")

    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    # 설정 업데이트
    if settings.is_public is not None:
        session.is_public = settings.is_public

        # 공개로 전환 시 공유 URL 생성
        if settings.is_public and not session.share_url:
            session.share_url = generate_share_url(session_id)

    if settings.is_anonymous is not None:
        session.is_anonymous = settings.is_anonymous

    if settings.show_strategy is not None:
        session.show_strategy = settings.show_strategy

    if settings.description is not None:
        session.description = settings.description

    await db.commit()
    await db.refresh(session)

    return ShareSettingsResponse(
        session_id=session.session_id,
        is_public=session.is_public,
        is_anonymous=session.is_anonymous,
        show_strategy=session.show_strategy,
        description=session.description,
        share_url=session.share_url,
        view_count=session.view_count,
        like_count=session.like_count
    )


@router.get("/rankings/today", response_model=List[RankingStrategyItem])
async def get_today_top_strategies(
    limit: int = 10,
    sort_by: str = "total_return",  # total_return, sharpe_ratio, like_count
    db: AsyncSession = Depends(get_db)
):
    """
    오늘 생성된 투자전략 TOP 랭킹

    Args:
        limit: 조회할 투자전략 수 (기본 10개)
        sort_by: 정렬 기준 (total_return, sharpe_ratio, like_count)
        db: 데이터베이스 세션

    Returns:
        TOP 투자전략 목록
    """
    today = date.today()

    # 정렬 컬럼 매핑
    sort_columns = {
        "total_return": SimulationStatistics.total_return.desc(),
        "sharpe_ratio": SimulationStatistics.sharpe_ratio.desc(),
        "like_count": SimulationSession.like_count.desc()
    }

    sort_column = sort_columns.get(sort_by, SimulationStatistics.total_return.desc())

    # 익명 처리를 위한 CASE 문
    author_name_expr = case(
        (SimulationSession.is_anonymous == True, "익명"),
        else_=User.name
    )

    query = (
        select(
            SimulationSession,
            SimulationStatistics,
            author_name_expr.label("author_name")
        )
        .join(SimulationStatistics, SimulationSession.session_id == SimulationStatistics.session_id)
        .join(User, SimulationSession.user_id == User.user_id)
        .where(SimulationSession.status == 'COMPLETED')
        .where(SimulationSession.is_public == True)  # 공개된 것만
        .where(func.date(SimulationSession.created_at) == today)
        .order_by(sort_column)
        .limit(limit)
    )

    result = await db.execute(query)
    strategies = result.all()

    return [
        RankingStrategyItem(
            rank=idx + 1,
            session_id=session.session_id,
            session_name=session.session_name,
            description=session.description,
            author_name=author_name,
            is_anonymous=session.is_anonymous,
            total_return=float(stats.total_return),
            annualized_return=float(stats.annualized_return),
            sharpe_ratio=float(stats.sharpe_ratio),
            max_drawdown=float(stats.max_drawdown),
            volatility=float(stats.volatility),
            total_trades=stats.total_trades,
            win_rate=float(stats.win_rate),
            show_strategy=session.show_strategy,
            strategy_summary=f"{stats.total_trades}회 거래, 승률 {stats.win_rate:.1f}%" if session.show_strategy else None,
            view_count=session.view_count,
            like_count=session.like_count,
            created_at=session.created_at
        )
        for idx, (session, stats, author_name) in enumerate(strategies)
    ]


@router.get("/rankings/all-time", response_model=List[RankingStrategyItem])
async def get_all_time_top_strategies(
    limit: int = 50,
    sort_by: str = "total_return",
    min_trades: int = 10,  # 최소 거래 횟수 (신뢰도 확보)
    db: AsyncSession = Depends(get_db)
):
    """
    전체 기간 TOP 투자전략 랭킹 (명예의 전당)

    Args:
        limit: 조회할 투자전략 수
        sort_by: 정렬 기준
        min_trades: 최소 거래 횟수 (너무 적은 거래는 제외)
        db: 데이터베이스 세션

    Returns:
        전체 TOP 투자전략 목록
    """
    sort_columns = {
        "total_return": SimulationStatistics.total_return.desc(),
        "sharpe_ratio": SimulationStatistics.sharpe_ratio.desc(),
        "like_count": SimulationSession.like_count.desc()
    }

    sort_column = sort_columns.get(sort_by, SimulationStatistics.total_return.desc())

    author_name_expr = case(
        (SimulationSession.is_anonymous == True, "익명"),
        else_=User.name
    )

    query = (
        select(
            SimulationSession,
            SimulationStatistics,
            author_name_expr.label("author_name")
        )
        .join(SimulationStatistics, SimulationSession.session_id == SimulationStatistics.session_id)
        .join(User, SimulationSession.user_id == User.user_id)
        .where(SimulationSession.status == 'COMPLETED')
        .where(SimulationSession.is_public == True)
        .where(SimulationStatistics.total_trades >= min_trades)  # 최소 거래 횟수
        .order_by(sort_column)
        .limit(limit)
    )

    result = await db.execute(query)
    strategies = result.all()

    return [
        RankingStrategyItem(
            rank=idx + 1,
            session_id=session.session_id,
            session_name=session.session_name,
            description=session.description,
            author_name=author_name,
            is_anonymous=session.is_anonymous,
            total_return=float(stats.total_return),
            annualized_return=float(stats.annualized_return),
            sharpe_ratio=float(stats.sharpe_ratio),
            max_drawdown=float(stats.max_drawdown),
            volatility=float(stats.volatility),
            total_trades=stats.total_trades,
            win_rate=float(stats.win_rate),
            show_strategy=session.show_strategy,
            strategy_summary=f"{stats.total_trades}회 거래, 승률 {stats.win_rate:.1f}%" if session.show_strategy else None,
            view_count=session.view_count,
            like_count=session.like_count,
            created_at=session.created_at
        )
        for idx, (session, stats, author_name) in enumerate(strategies)
    ]


@router.get("/shared/{share_url}", response_model=StrategyDetailResponse)
async def get_shared_strategy(
    share_url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    공유 링크로 투자전략 상세 조회

    Args:
        share_url: 공유 URL 슬러그
        db: 데이터베이스 세션

    Returns:
        투자전략 상세 정보
    """
    author_name_expr = case(
        (SimulationSession.is_anonymous == True, "익명"),
        else_=User.name
    )

    query = (
        select(
            SimulationSession,
            SimulationStatistics,
            author_name_expr.label("author_name")
        )
        .join(SimulationStatistics, SimulationSession.session_id == SimulationStatistics.session_id)
        .join(User, SimulationSession.user_id == User.user_id)
        .where(SimulationSession.share_url == share_url)
        .where(SimulationSession.is_public == True)  # 공개된 것만
    )

    result = await db.execute(query)
    data = result.one_or_none()

    if not data:
        raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없거나 비공개 상태입니다")

    session, stats, author_name = data

    # 조회수 증가
    session.view_count += 1
    await db.commit()

    # 전략 정보는 show_strategy=True일 때만
    buy_conditions = None
    sell_conditions = None

    if session.show_strategy:
        # TODO: 실제 전략 조건 가져오기 (strategy_factors 조인)
        buy_conditions = []
        sell_conditions = []

    return StrategyDetailResponse(
        session_id=session.session_id,
        session_name=session.session_name,
        description=session.description,
        author_name=author_name,
        is_anonymous=session.is_anonymous,
        start_date=session.start_date.isoformat(),
        end_date=session.end_date.isoformat(),
        initial_capital=float(session.initial_capital),
        benchmark=session.benchmark,
        total_return=float(stats.total_return),
        annualized_return=float(stats.annualized_return),
        sharpe_ratio=float(stats.sharpe_ratio),
        max_drawdown=float(stats.max_drawdown),
        volatility=float(stats.volatility),
        win_rate=float(stats.win_rate),
        show_strategy=session.show_strategy,
        buy_conditions=buy_conditions,
        sell_conditions=sell_conditions,
        view_count=session.view_count,
        like_count=session.like_count,
        created_at=session.created_at
    )


@router.post("/{session_id}/like", response_model=LikeResponse)
async def toggle_like(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투자전략 좋아요 토글

    Args:
        session_id: 투자전략 세션 ID
        current_user: 현재 로그인 사용자
        db: 데이터베이스 세션

    Returns:
        좋아요 상태

    Note:
        실제로는 user_strategy_likes 테이블을 만들어 중복 좋아요 방지해야 함
        현재는 간단히 카운트만 증가
    """
    result = await db.execute(
        select(SimulationSession).where(SimulationSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없습니다")

    if not session.is_public:
        raise HTTPException(status_code=403, detail="비공개 투자전략입니다")

    # TODO: user_strategy_likes 테이블로 좋아요 관리
    # 현재는 단순 증가
    session.like_count += 1
    await db.commit()

    return LikeResponse(
        session_id=session.session_id,
        like_count=session.like_count,
        is_liked=True
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투자전략 삭제

    Args:
        session_id: 투자전략 세션 ID
        current_user: 현재 로그인 사용자
        db: 데이터베이스 세션
    """
    result = await db.execute(
        select(SimulationSession).where(SimulationSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없습니다")

    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")

    await db.delete(session)
    await db.commit()
