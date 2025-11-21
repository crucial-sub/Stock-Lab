"""
Strategy API 라우터
- 내 투자전략 목록 조회
- 공개 투자전략 랭킹 조회
- 투자전략 공개 설정 변경
"""
from datetime import datetime
import logging
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func

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
    BacktestDeleteRequest,
    StrategyUpdate,
    PublicStrategiesResponse,
    PublicStrategyListItem,
)
from app.schemas.community import CloneStrategyData

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
                is_active=session.is_active if hasattr(session, 'is_active') else False,
                is_public=strategy.is_public if hasattr(strategy, 'is_public') else False,
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


@router.get("/strategies/public", response_model=PublicStrategiesResponse)
async def get_public_strategies(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    공개 투자전략 목록 조회 (최신순)
    - is_public=True 전략만 대상으로 created_at 기준 내림차순 정렬
    - 익명 설정 및 전략 내용 숨김 설정 반영
    """
    try:
        offset = (page - 1) * limit

        # 최근 완료된 세션 기준 통계 조인 (없어도 통과하도록 OUTER JOIN)
        latest_sessions_subquery = (
            select(
                SimulationSession.strategy_id,
                func.max(SimulationSession.completed_at).label("max_completed_at"),
            )
            .where(SimulationSession.status == "COMPLETED")
            .group_by(SimulationSession.strategy_id)
            .subquery()
        )

        query = (
            select(PortfolioStrategy, User, SimulationStatistics)
            .join(User, User.user_id == PortfolioStrategy.user_id, isouter=True)
            .join(
                latest_sessions_subquery,
                PortfolioStrategy.strategy_id == latest_sessions_subquery.c.strategy_id,
                isouter=True,
            )
            .join(
                SimulationSession,
                and_(
                    SimulationSession.strategy_id
                    == latest_sessions_subquery.c.strategy_id,
                    SimulationSession.completed_at
                    == latest_sessions_subquery.c.max_completed_at,
                    SimulationSession.status == "COMPLETED",
                ),
                isouter=True,
            )
            .join(
                SimulationStatistics,
                SimulationStatistics.session_id == SimulationSession.session_id,
                isouter=True,
            )
            .where(PortfolioStrategy.is_public == True)  # noqa: E712
            .order_by(PortfolioStrategy.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        # 전체 개수
        count_query = (
            select(func.count())
            .select_from(PortfolioStrategy)
            .where(PortfolioStrategy.is_public == True)  # noqa: E712
        )
        total = (await db.execute(count_query)).scalar() or 0

        strategies: List[PublicStrategyListItem] = []
        for strategy, user, stats in rows:
            owner_name = None if strategy.is_anonymous else (user.name if user else None)
            description = None if strategy.hide_strategy_details else strategy.description

            strategies.append(
                PublicStrategyListItem(
                    strategy_id=strategy.strategy_id,
                    strategy_name=strategy.strategy_name,
                    description=description,
                    is_anonymous=strategy.is_anonymous,
                    hide_strategy_details=strategy.hide_strategy_details,
                    owner_name=owner_name,
                    total_return=float(stats.total_return)
                    if stats and stats.total_return is not None
                    else None,
                    annualized_return=float(stats.annualized_return)
                    if stats and stats.annualized_return is not None
                    else None,
                    created_at=strategy.created_at,
                    updated_at=strategy.updated_at,
                )
            )

        has_next = (page * limit) < total

        return PublicStrategiesResponse(
            strategies=strategies,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
        )

    except Exception as e:
        logger.error(f"공개 투자전략 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: str,
    payload: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """투자전략 이름/설명 수정"""
    try:
        strategy_query = select(PortfolioStrategy).where(
            PortfolioStrategy.strategy_id == strategy_id
        )
        result = await db.execute(strategy_query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(status_code=404, detail="투자전략을 찾을 수 없습니다")

        if strategy.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return {"message": "수정할 내용이 없습니다."}

        for field, value in update_data.items():
            setattr(strategy, field, value)

        strategy.updated_at = datetime.now()

        await db.commit()
        await db.refresh(strategy)

        return {
            "message": "투자전략이 수정되었습니다.",
            "strategyName": strategy.strategy_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"투자전략 수정 실패: {e}", exc_info=True)
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

        # 2. is_public 변경 여부 확인 (Redis 동기화용)
        old_is_public = strategy.is_public

        # 3. 설정 업데이트
        update_data = settings.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)

        # updated_at은 자동으로 갱신되지만 명시적으로 설정
        from datetime import datetime
        strategy.updated_at = datetime.now()

        await db.commit()
        await db.refresh(strategy)

        # 🎯 4. Redis 랭킹 동기화
        if "is_public" in update_data and old_is_public != strategy.is_public:
            try:
                from app.services.ranking_service import get_ranking_service

                ranking_service = await get_ranking_service()

                if ranking_service.enabled:
                    # 해당 전략의 모든 완료된 세션 조회
                    sessions_query = select(
                        SimulationSession.session_id,
                        SimulationStatistics.total_return
                    ).join(
                        SimulationStatistics,
                        SimulationStatistics.session_id == SimulationSession.session_id
                    ).where(
                        and_(
                            SimulationSession.strategy_id == strategy_id,
                            SimulationSession.status == "COMPLETED",
                            SimulationStatistics.total_return.isnot(None)
                        )
                    )
                    sessions_result = await db.execute(sessions_query)
                    sessions = sessions_result.all()

                    if strategy.is_public:
                        # 공개로 변경 → Redis에 추가
                        for session_id, total_return in sessions:
                            await ranking_service.add_to_ranking(
                                session_id=session_id,
                                total_return=float(total_return),
                                strategy_id=strategy_id,
                                is_public=True
                            )
                        logger.info(f"✅ Redis 랭킹 추가: {len(sessions)}개 세션")
                    else:
                        # 비공개로 변경 → Redis에서 제거
                        for session_id, _ in sessions:
                            await ranking_service.remove_from_ranking(session_id)
                        logger.info(f"🗑️ Redis 랭킹 제거: {len(sessions)}개 세션")

            except Exception as e:
                logger.warning(f"⚠️ Redis 랭킹 동기화 실패 (무시): {e}")

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

        # 🎯 4. Redis 랭킹에서 삭제된 세션 제거
        try:
            from app.services.ranking_service import get_ranking_service
            ranking_service = await get_ranking_service()

            if ranking_service.enabled:
                for session_id in session_ids:
                    await ranking_service.remove_from_ranking(session_id)
                logger.info(f"🗑️ Redis 랭킹에서 제거 완료: {len(session_ids)}개 세션")
        except Exception as e:
            logger.warning(f"⚠️ Redis 랭킹 제거 실패 (무시): {e}")

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


@router.get("/strategies/sessions/{session_id}/clone-data", response_model=CloneStrategyData)
async def get_session_clone_data(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 세션 복제 데이터 조회 (백테스트 창으로 전달)
    - 본인이 소유한 세션만 조회 가능
    - 매수/매도 조건, 기간, 종목 등 모든 설정을 포함
    """
    try:
        user_id = current_user.user_id

        # 세션, 전략, 트레이딩 룰 조회
        query = (
            select(SimulationSession, PortfolioStrategy, TradingRule)
            .join(
                PortfolioStrategy,
                PortfolioStrategy.strategy_id == SimulationSession.strategy_id
            )
            .join(
                TradingRule,
                TradingRule.strategy_id == PortfolioStrategy.strategy_id
            )
            .where(
                and_(
                    SimulationSession.session_id == session_id,
                    SimulationSession.user_id == user_id  # 본인 세션만
                )
            )
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="백테스트 세션을 찾을 수 없거나 접근 권한이 없습니다")

        session, strategy, trading_rule = row

        # buy_condition과 sell_condition 파싱
        buy_condition = trading_rule.buy_condition or {}
        sell_condition = trading_rule.sell_condition or {}

        return CloneStrategyData(
            strategy_name=f"{strategy.strategy_name} (복제)",
            is_day_or_month="daily",  # 기본값
            initial_investment=int(session.initial_capital / 10000),  # 원 -> 만원
            start_date=session.start_date.strftime("%Y%m%d"),
            end_date=session.end_date.strftime("%Y%m%d"),
            commission_rate=float(trading_rule.commission_rate * 100) if trading_rule.commission_rate else 0.015,
            slippage=0.1,  # 기본값
            buy_conditions=buy_condition.get('conditions', []),
            buy_logic=buy_condition.get('logic', 'AND'),
            priority_factor=buy_condition.get('priority_factor'),
            priority_order=buy_condition.get('priority_order', 'desc'),
            per_stock_ratio=buy_condition.get('per_stock_ratio', 5.0),
            max_holdings=trading_rule.max_positions or 20,
            max_buy_value=buy_condition.get('max_buy_value'),
            max_daily_stock=buy_condition.get('max_daily_stock'),
            buy_price_basis=buy_condition.get('buy_price_basis', 'CLOSE'),
            buy_price_offset=buy_condition.get('buy_price_offset', 0.0),
            target_and_loss=sell_condition.get('target_and_loss'),
            hold_days=sell_condition.get('hold_days'),
            condition_sell=sell_condition.get('condition_sell'),
            trade_targets=buy_condition.get('trade_targets', {
                "use_all_stocks": True,
                "selected_themes": [],
                "selected_stocks": []
            })
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"백테스트 세션 복제 데이터 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
