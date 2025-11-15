"""
Strategy API 라우터
- 내 투자전략 목록 조회
- 공개 투자전략 랭킹 조회
- 투자전략 공개 설정 변경
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from typing import Optional, Literal
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.simulation import (
    PortfolioStrategy,
    SimulationSession,
    SimulationStatistics,
    StrategyFactor,
    TradingRule
)
from app.models.user import User
from app.schemas.strategy import (
    StrategyListItem,
    StrategyDetailItem,
    StrategyRankingItem,
    MyStrategiesResponse,
    StrategyRankingResponse,
    StrategySharingUpdate,
    StrategyStatisticsSummary,
    BacktestDeleteRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/strategies/my", response_model=MyStrategiesResponse)
async def get_my_strategies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    내 백테스트 결과 목록 조회
    - 로그인한 사용자의 모든 백테스트 결과 반환 (진행중/완료/실패 모두 포함)
    - 최신 순으로 정렬
    """
    try:
        user_id = current_user.user_id

        # 1. 사용자의 모든 시뮬레이션 세션 조회 (전략 정보 포함)
        sessions_query = (
            select(SimulationSession, PortfolioStrategy, SimulationStatistics)
            .join(
                PortfolioStrategy,
                PortfolioStrategy.strategy_id == SimulationSession.strategy_id
            )
            .outerjoin(
                SimulationStatistics,
                SimulationStatistics.session_id == SimulationSession.session_id
            )
            .where(SimulationSession.user_id == user_id)
            .order_by(SimulationSession.created_at.desc())
        )

        result = await db.execute(sessions_query)
        rows = result.all()

        # 2. 백테스트 결과 리스트 생성
        my_strategies = []
        for session, strategy, stats in rows:
            # 간소화된 목록 아이템 생성
            strategy_item = StrategyListItem(
                session_id=session.session_id,
                strategy_id=strategy.strategy_id,
                strategy_name=strategy.strategy_name,
                is_active=session.is_active if hasattr(session, 'is_active') else True,
                status=session.status,
                total_return=float(stats.total_return) if stats and stats.total_return else None,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
            my_strategies.append(strategy_item)

        return MyStrategiesResponse(
            strategies=my_strategies,
            total=len(my_strategies)
        )

    except Exception as e:
        logger.error(f"내 백테스트 결과 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/public/ranking", response_model=StrategyRankingResponse)
async def get_public_Strategies_ranking(
    sort_by: Literal["total_return", "annualized_return"] = Query(
        default="annualized_return",
        description="정렬 기준: total_return (총 수익률) 또는 annualized_return (연환산 수익률)"
    ),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    공개 투자전략 랭킹 조회
    - is_public=True인 전략만 조회
    - 각 전략의 최신 백테스트 결과 기준으로 정렬
    - 익명 설정 및 전략 내용 숨김 설정 반영
    """
    try:
        # 1. 공개 전략 중 완료된 시뮬레이션이 있는 전략만 조회
        # Subquery: 각 전략의 최신 완료된 시뮬레이션 찾기
        latest_sessions_subquery = (
            select(
                SimulationSession.strategy_id,
                func.max(SimulationSession.completed_at).label("max_completed_at")
            )
            .where(SimulationSession.status == "COMPLETED")
            .group_by(SimulationSession.strategy_id)
            .subquery()
        )

        # 2. 전략, 세션, 통계, 사용자 정보 조인
        query = (
            select(
                PortfolioStrategy,
                SimulationSession,
                SimulationStatistics,
                User
            )
            .join(
                latest_sessions_subquery,
                and_(
                    PortfolioStrategy.strategy_id == latest_sessions_subquery.c.strategy_id,
                    PortfolioStrategy.is_public == True
                )
            )
            .join(
                SimulationSession,
                and_(
                    SimulationSession.strategy_id == latest_sessions_subquery.c.strategy_id,
                    SimulationSession.completed_at == latest_sessions_subquery.c.max_completed_at,
                    SimulationSession.status == "COMPLETED"
                )
            )
            .join(
                SimulationStatistics,
                SimulationStatistics.session_id == SimulationSession.session_id
            )
            .outerjoin(
                User,
                User.user_id == PortfolioStrategy.user_id
            )
        )

        # 3. 정렬 기준 적용
        if sort_by == "total_return":
            query = query.order_by(desc(SimulationStatistics.total_return))
        else:  # annualized_return
            query = query.order_by(desc(SimulationStatistics.annualized_return))

        # 4. 페이지네이션
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # 5. 전체 개수 조회 (페이지네이션용)
        count_query = (
            select(func.count())
            .select_from(PortfolioStrategy)
            .join(
                latest_sessions_subquery,
                and_(
                    PortfolioStrategy.strategy_id == latest_sessions_subquery.c.strategy_id,
                    PortfolioStrategy.is_public == True
                )
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 6. 응답 데이터 변환
        rankings = []
        for strategy, session, stats, user in rows:
            # 익명 설정에 따라 소유자 이름 표시
            owner_name = None
            if not strategy.is_anonymous and user:
                owner_name = user.name

            # 전략 내용 숨김 설정에 따라 상세 정보 표시
            strategy_type_display = None if strategy.hide_strategy_details else strategy.strategy_type
            description_display = None if strategy.hide_strategy_details else strategy.description

            ranking_item = StrategyRankingItem(
                strategy_id=strategy.strategy_id,
                strategy_name=strategy.strategy_name,
                owner_name=owner_name,
                is_anonymous=strategy.is_anonymous,
                strategy_type=strategy_type_display,
                description=description_display,
                hide_strategy_details=strategy.hide_strategy_details,
                backtest_start_date=session.start_date,
                backtest_end_date=session.end_date,
                total_return=float(stats.total_return) if stats.total_return else 0.0,
                annualized_return=float(stats.annualized_return) if stats.annualized_return else 0.0,
                max_drawdown=float(stats.max_drawdown) if stats.max_drawdown else None,
                sharpe_ratio=float(stats.sharpe_ratio) if stats.sharpe_ratio else None,
                volatility=float(stats.volatility) if stats.volatility else None,
                win_rate=float(stats.win_rate) if stats.win_rate else None,
                total_trades=stats.total_trades,
                created_at=strategy.created_at
            )
            rankings.append(ranking_item)

        return StrategyRankingResponse(
            rankings=rankings,
            total=total or 0,
            page=page,
            limit=limit,
            sort_by=sort_by
        )

    except Exception as e:
        logger.error(f"공개 투자전략 랭킹 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/strategies/{strategy_id}/settings")
async def update_strategy_sharing_settings(
    strategy_id: str,
    settings: StrategySharingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투자전략 공개 설정 변경
    - 본인이 소유한 전략만 수정 가능
    - is_public, is_anonymous, hide_strategy_details 설정 변경
    """
    try:
        user_id = current_user.user_id

        # 1. 전략 조회 및 권한 확인
        strategy_query = select(PortfolioStrategy).where(
            PortfolioStrategy.strategy_id == strategy_id
        )
        strategy_result = await db.execute(strategy_query)
        strategy = strategy_result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없습니다")

        if strategy.user_id != user_id:
            raise HTTPException(status_code=403, detail="이 전략을 수정할 권한이 없습니다")

        # 2. 설정 업데이트
        update_data = settings.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)

        # updated_at은 자동으로 갱신되지만 명시적으로 설정
        from datetime import datetime
        strategy.updated_at = datetime.now()

        await db.commit()
        await db.refresh(strategy)

        return {
            "message": "공개 설정이 업데이트되었습니다",
            "strategy_id": strategy.strategy_id,
            "settings": {
                "is_public": strategy.is_public,
                "is_anonymous": strategy.is_anonymous,
                "hide_strategy_details": strategy.hide_strategy_details
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"투자전략 공개 설정 변경 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategies/sessions")
async def delete_backtest_sessions(
    delete_request: BacktestDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 세션 삭제
    - 본인이 소유한 백테스트 세션만 삭제 가능
    - 여러 세션을 한 번에 삭제 가능
    """
    try:
        user_id = current_user.user_id
        session_ids = delete_request.session_ids

        if not session_ids:
            raise HTTPException(status_code=400, detail="삭제할 세션 ID가 없습니다")

        # 1. 세션 조회 및 권한 확인
        sessions_query = select(SimulationSession).where(
            SimulationSession.session_id.in_(session_ids)
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        if not sessions:
            raise HTTPException(status_code=404, detail="백테스트 세션을 찾을 수 없습니다")

        # 2. 권한 확인 - 모든 세션이 현재 사용자 소유인지 확인
        unauthorized_sessions = [
            session.session_id for session in sessions
            if session.user_id != user_id
        ]

        if unauthorized_sessions:
            raise HTTPException(
                status_code=403,
                detail=f"삭제 권한이 없는 세션이 포함되어 있습니다: {unauthorized_sessions}"
            )

        # 3. 세션 삭제
        deleted_count = 0
        for session in sessions:
            await db.delete(session)
            deleted_count += 1

        await db.commit()

        return {
            "message": f"{deleted_count}개의 백테스트가 삭제되었습니다",
            "deleted_session_ids": session_ids,
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"백테스트 세션 삭제 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
