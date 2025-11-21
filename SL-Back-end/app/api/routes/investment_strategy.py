"""
투자 전략 추천 API 엔드포인트
AI 어시스턴트에서 사용자 설문 결과 기반 전략 추천 및 전략 상세 정보 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List

from app.core.database import get_db
from app.models.investment_strategy import InvestmentStrategy
from app.schemas.investment_strategy import (
    StrategyRecommendationRequest,
    StrategyMatch,
    StrategyDetail,
    DisplayCondition,
)

router = APIRouter()


def calculate_match_score(user_tags: List[str], strategy_tags: List[str]) -> int:
    """
    태그 매칭 점수 계산

    Args:
        user_tags: 사용자 설문 결과 태그
        strategy_tags: 전략 태그

    Returns:
        매칭 점수 (0-100)
    """
    if not user_tags:
        return 0

    matched_count = len(set(user_tags) & set(strategy_tags))
    return round((matched_count / len(user_tags)) * 100)


@router.post("/recommend", response_model=List[StrategyMatch])
async def recommend_strategies(
    request: StrategyRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    AI 어시스턴트 설문 결과 기반 전략 추천

    - 사용자 태그와 전략 태그 매칭
    - 매칭 점수 계산 후 상위 N개 반환
    - 점수 내림차순, 동점 시 ID 오름차순 정렬

    Args:
        request: 추천 요청 (user_tags, top_n)
        db: 데이터베이스 세션

    Returns:
        List[StrategyMatch]: 추천된 전략 목록
    """
    # 활성화된 전략 조회
    result = await db.execute(
        select(InvestmentStrategy).where(InvestmentStrategy.is_active == True)
    )
    strategies = result.scalars().all()

    if not strategies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활성화된 전략이 없습니다."
        )

    # 매칭 점수 계산
    matches = []
    for strategy in strategies:
        score = calculate_match_score(request.user_tags, strategy.tags)
        matched_tags = list(set(request.user_tags) & set(strategy.tags))
        unmatched_tags = list(set(request.user_tags) - set(strategy.tags))

        # display_conditions를 Pydantic 모델로 변환
        display_conditions = [
            DisplayCondition(**cond) for cond in strategy.display_conditions
        ]

        matches.append(
            StrategyMatch(
                id=strategy.id,
                name=strategy.name,
                summary=strategy.summary,
                tags=strategy.tags,
                match_score=score,
                matched_tags=matched_tags,
                unmatched_tags=unmatched_tags,
                display_conditions=display_conditions,
            )
        )

    # 점수 내림차순, 동점 시 ID 오름차순 정렬
    matches.sort(key=lambda x: (-x.match_score, x.id))

    return matches[: request.top_n]


@router.get("/{strategy_id}", response_model=StrategyDetail)
async def get_strategy_detail(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    전략 상세 정보 조회 (백테스트 실행용)

    - 완전한 backtest_config 반환
    - 조회 시 인기도 점수 자동 증가

    Args:
        strategy_id: 전략 ID
        db: 데이터베이스 세션

    Returns:
        StrategyDetail: 전략 상세 정보

    Raises:
        HTTPException: 전략을 찾을 수 없는 경우 404
    """
    # 전략 조회
    result = await db.execute(
        select(InvestmentStrategy).where(
            InvestmentStrategy.id == strategy_id,
            InvestmentStrategy.is_active == True,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"전략을 찾을 수 없습니다: {strategy_id}"
        )

    # 인기도 점수 증가
    await db.execute(
        update(InvestmentStrategy)
        .where(InvestmentStrategy.id == strategy_id)
        .values(popularity_score=InvestmentStrategy.popularity_score + 1)
    )
    await db.commit()

    # Refresh to get updated popularity_score
    await db.refresh(strategy)

    # display_conditions를 Pydantic 모델로 변환
    display_conditions = [
        DisplayCondition(**cond) for cond in strategy.display_conditions
    ]

    return StrategyDetail(
        id=strategy.id,
        name=strategy.name,
        summary=strategy.summary,
        description=strategy.description,
        tags=strategy.tags,
        backtest_config=strategy.backtest_config,
        display_conditions=display_conditions,
        popularity_score=strategy.popularity_score,
        created_at=strategy.created_at,
        updated_at=strategy.updated_at,
    )
