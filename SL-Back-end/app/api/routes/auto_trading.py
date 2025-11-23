"""
자동매매 API 라우터
- 모의투자 계좌 전용
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auto_trading import (
    AutoTradingActivateRequest,
    AutoTradingActivateResponse,
    AutoTradingDeactivateRequest,
    AutoTradingDeactivateResponse,
    AutoTradingStrategyNameUpdateRequest,
    AutoTradingStrategyNameUpdateResponse,
    AutoTradingStatusResponse,
    AutoTradingStrategyResponse,
    LivePositionResponse,
    LiveTradeResponse,
    LiveDailyPerformanceResponse,
    AutoTradingLogResponse,
    RebalancePreviewResponse,
    TradeSignalItem,
    AutoTradingLogListResponse,
    AutoTradingRiskSnapshotResponse,
    AutoTradingRiskEnforceResponse,
    PortfolioDashboardResponse,
    AutoTradingExecutionReportResponse,
    ExecutionReportRow,
    ExecutionReportSummary,
    AutoTradingPositionRisk,
    AutoTradingRiskAlert
)
from app.services.auto_trading_service import AutoTradingService
from app.services.auto_trading_executor import AutoTradingExecutor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auto-trading",
    tags=["auto-trading"]
)


def _to_trade_signal(stock: Dict[str, Any]) -> TradeSignalItem:
    """헬퍼: dict -> TradeSignalItem"""
    return TradeSignalItem(
        stock_code=stock.get("stock_code"),
        stock_name=stock.get("company_name") or stock.get("stock_name"),
        quantity=stock.get("quantity"),
        target_weight=stock.get("target_weight"),
        current_price=stock.get("current_price"),
        per=stock.get("per"),
        pbr=stock.get("pbr"),
        metadata=stock
    )


@router.post("/activate", response_model=AutoTradingActivateResponse)
async def activate_auto_trading(
    request: AutoTradingActivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    자동매매 활성화
    - 백테스트 완료된 전략을 실시간 자동매매로 전환
    - 모의투자 계좌 전용
    """
    try:
        strategy = await AutoTradingService.activate_strategy(
            db=db,
            user_id=current_user.user_id,
            session_id=request.session_id,
            initial_capital=request.initial_capital,
            allocated_capital=request.allocated_capital,
            strategy_name=request.strategy_name
        )

        return AutoTradingActivateResponse(
            message="자동매매가 활성화되었습니다.",
            strategy_id=strategy.strategy_id,
            is_active=strategy.is_active,
            activated_at=strategy.activated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"자동매매 활성화 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 활성화에 실패했습니다."
        )


@router.get("/strategies/{strategy_id}/deactivation-conditions")
async def check_deactivation_conditions(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    비활성화 조건 확인
    - 보유 종목 수, 장시간 여부 체크
    - 추천 비활성화 모드 반환
    """
    try:
        conditions = await AutoTradingService.check_deactivation_conditions(
            db=db,
            strategy_id=strategy_id,
            user_id=current_user.user_id
        )
        return conditions

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"비활성화 조건 확인 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비활성화 조건 확인에 실패했습니다."
        )


@router.patch("/strategies/{strategy_id}/name", response_model=AutoTradingStrategyNameUpdateResponse)
async def update_strategy_name(
    strategy_id: UUID,
    request: AutoTradingStrategyNameUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    자동매매 전략 이름 수정
    - 활성/비활성 상관없이 전략 이름 변경 가능
    """
    try:
        from sqlalchemy import select, and_
        from app.models.auto_trading import AutoTradingStrategy

        # 전략 조회 및 권한 확인
        query = select(AutoTradingStrategy).where(
            and_(
                AutoTradingStrategy.strategy_id == strategy_id,
                AutoTradingStrategy.user_id == current_user.user_id
            )
        )
        result = await db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="자동매매 전략을 찾을 수 없습니다."
            )

        # 이름 업데이트
        strategy.strategy_name = request.strategy_name
        await db.commit()
        await db.refresh(strategy)

        return AutoTradingStrategyNameUpdateResponse(
            message="전략 이름이 성공적으로 변경되었습니다.",
            strategy_id=strategy.strategy_id,
            strategy_name=strategy.strategy_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 이름 수정 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전략 이름 수정에 실패했습니다."
        )


@router.post("/strategies/{strategy_id}/deactivate", response_model=AutoTradingDeactivateResponse)
async def deactivate_auto_trading(
    strategy_id: UUID,
    request: AutoTradingDeactivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    자동매매 비활성화
    - 보유 종목 전량 매도 옵션 제공
    - 비활성화 모드 지원: immediate, sell_and_deactivate, scheduled_sell
    """
    try:
        strategy, sold_count = await AutoTradingService.deactivate_strategy(
            db=db,
            strategy_id=strategy_id,
            user_id=current_user.user_id,
            sell_all=request.sell_all_positions,
            deactivation_mode=request.deactivation_mode
        )

        # 메시지 생성
        if request.deactivation_mode == "scheduled_sell":
            message = "자동매매 비활성화가 예약되었습니다. 다음 장 시작 시 보유 종목을 매도하고 비활성화됩니다."
        else:
            message = f"자동매매가 비활성화되었습니다. (매도: {sold_count}개 종목)"

        return AutoTradingDeactivateResponse(
            message=message,
            strategy_id=strategy.strategy_id,
            is_active=strategy.is_active,
            deactivated_at=strategy.deactivated_at or datetime.now(),
            positions_sold=sold_count
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"자동매매 비활성화 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 비활성화에 실패했습니다."
        )


@router.get("/strategies/{strategy_id}/status", response_model=AutoTradingStatusResponse)
async def get_auto_trading_status(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    자동매매 전략 상태 조회
    - 현재 보유 종목
    - 오늘 매매 내역
    - 최근 성과
    """
    try:
        status_data = await AutoTradingService.get_strategy_status(
            db=db,
            strategy_id=strategy_id,
            user_id=current_user.user_id
        )

        return AutoTradingStatusResponse(
            strategy=AutoTradingStrategyResponse.from_orm(status_data["strategy"]),
            positions=[LivePositionResponse.from_orm(p) for p in status_data["positions"]],
            today_trades=[LiveTradeResponse.from_orm(t) for t in status_data["today_trades"]],
            latest_performance=LiveDailyPerformanceResponse.from_orm(status_data["latest_performance"]) if status_data["latest_performance"] else None,
            total_positions=status_data["total_positions"],
            total_trades=status_data["total_trades"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"자동매매 상태 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 상태 조회에 실패했습니다."
        )


@router.get("/my-strategies", response_model=List[AutoTradingStrategyResponse])
async def get_my_auto_trading_strategies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    내 자동매매 전략 목록 조회
    """
    try:
        from sqlalchemy import select
        from app.models.auto_trading import AutoTradingStrategy, LivePosition
        from app.services.kiwoom_service import KiwoomService
        from decimal import Decimal

        query = select(AutoTradingStrategy).where(
            AutoTradingStrategy.user_id == current_user.user_id
        ).order_by(AutoTradingStrategy.created_at.desc())

        result = await db.execute(query)
        strategies = result.scalars().all()

        # 키움 API를 통해 각 전략의 실제 수익률 계산
        if current_user.kiwoom_access_token:
            try:
                account_data = KiwoomService.get_account_evaluation(
                    access_token=current_user.kiwoom_access_token
                )

                for strategy in strategies:
                    if not strategy.is_active:
                        continue

                    # 이 전략의 보유 종목 조회
                    positions_query = select(LivePosition).where(
                        LivePosition.strategy_id == strategy.strategy_id
                    )
                    positions_result = await db.execute(positions_query)
                    positions = positions_result.scalars().all()

                    strategy_stock_codes = {pos.stock_code for pos in positions}
                    strategy_eval_sum = Decimal("0")
                    strategy_profit_sum = Decimal("0")

                    # 키움 API 보유 종목 중 이 전략의 종목만 필터링
                    for holding in account_data.get("acnt_evlt_remn_indv_tot", []):
                        stock_code = holding.get("stk_cd", "")
                        if stock_code.startswith("A"):
                            stock_code = stock_code[1:]

                        if stock_code in strategy_stock_codes:
                            evltv_amt = holding.get("evlt_amt")
                            if evltv_amt:
                                strategy_eval_sum += Decimal(str(int(evltv_amt)))

                            evltv_prft = holding.get("evltv_prft")
                            if evltv_prft:
                                strategy_profit_sum += Decimal(str(int(evltv_prft)))

                    # 현금 잔고 추가
                    strategy_eval_sum += strategy.cash_balance

                    # allocated_capital 기준 수익률 계산
                    strategy.kiwoom_total_eval = strategy_eval_sum
                    strategy.kiwoom_total_profit = strategy_profit_sum
                    strategy.kiwoom_total_profit_rate = Decimal("0")

                    if strategy.allocated_capital > 0:
                        strategy.kiwoom_total_profit_rate = (strategy_profit_sum / strategy.allocated_capital) * Decimal("100")

                    logger.info(f"📊 전략 {strategy.strategy_id}: 평가액={strategy_eval_sum:,.0f}원, 손익={strategy_profit_sum:,.0f}원, 수익률={strategy.kiwoom_total_profit_rate:.2f}%")

            except Exception as kiwoom_err:
                logger.warning(f"키움 API 조회 실패: {kiwoom_err}")

        return [AutoTradingStrategyResponse.from_orm(s) for s in strategies]

    except Exception as e:
        logger.error(f"자동매매 전략 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동매매 전략 목록 조회에 실패했습니다."
        )


@router.post("/strategies/{strategy_id}/execute")
async def execute_auto_trading(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    자동매매 실행 (수동 트리거)
    - 종목 선정 + 매수 주문
    - 나중에 스케줄러로 자동화
    """
    try:
        from sqlalchemy import select, and_
        from app.models.auto_trading import AutoTradingStrategy

        # 1. 전략 조회
        query = select(AutoTradingStrategy).where(
            and_(
                AutoTradingStrategy.strategy_id == strategy_id,
                AutoTradingStrategy.user_id == current_user.user_id,
                AutoTradingStrategy.is_active == True
            )
        )
        result = await db.execute(query)
        strategy = result.scalar_one_or_none()

        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="활성화된 자동매매 전략을 찾을 수 없습니다."
            )

        # 2. 종목 선정
        selected_stocks = await AutoTradingExecutor.select_stocks_for_strategy(
            db=db,
            strategy=strategy
        )

        if not selected_stocks:
            return {
                "message": "조건에 맞는 종목이 없습니다.",
                "selected_count": 0,
                "bought_count": 0
            }

        # 3. 매수 주문 실행
        bought_count = await AutoTradingExecutor.execute_buy_orders(
            db=db,
            strategy=strategy,
            selected_stocks=selected_stocks
        )

        return {
            "message": f"자동매매 실행 완료",
            "selected_count": len(selected_stocks),
            "bought_count": bought_count,
            "stocks": selected_stocks[:5]  # 상위 5개만 반환
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동매매 실행 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자동매매 실행에 실패했습니다: {str(e)}"
        )


@router.get(
    "/strategies/{strategy_id}/rebalance-preview",
    response_model=RebalancePreviewResponse
)
async def get_rebalance_preview(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """최근 리밸런싱 미리보기 조회"""
    log_entry = await AutoTradingService.get_latest_rebalance_preview(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id
    )
    if not log_entry or not log_entry.details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="리밸런싱 미리보기 기록이 없습니다."
        )
    candidates = [
        _to_trade_signal(stock) for stock in log_entry.details.get("stocks", [])
    ]
    generated_at = log_entry.details.get("generated_at", log_entry.created_at)
    if isinstance(generated_at, str):
        try:
            generated_at = datetime.fromisoformat(generated_at)
        except Exception:
            generated_at = log_entry.created_at

    return RebalancePreviewResponse(
        generated_at=generated_at,
        candidates=candidates,
        note=log_entry.message
    )


@router.post(
    "/strategies/{strategy_id}/rebalance-preview",
    response_model=RebalancePreviewResponse
)
async def generate_rebalance_preview(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """즉시 리밸런싱 프리뷰 생성"""
    stocks = await AutoTradingService.generate_rebalance_preview(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id
    )
    return RebalancePreviewResponse(
        generated_at=datetime.utcnow(),
        candidates=[_to_trade_signal(stock) for stock in stocks],
        note="자동 생성"
    )


@router.get(
    "/strategies/{strategy_id}/logs",
    response_model=AutoTradingLogListResponse
)
async def get_strategy_logs(
    strategy_id: UUID,
    event_type: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """전략 이벤트 로그 조회"""
    logs = await AutoTradingService.get_strategy_logs(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id,
        event_type=event_type,
        limit=limit
    )
    return AutoTradingLogListResponse(
        logs=[AutoTradingLogResponse.from_orm(log) for log in logs]
    )


@router.get(
    "/strategies/{strategy_id}/risk",
    response_model=AutoTradingRiskSnapshotResponse
)
async def get_risk_snapshot(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """위험 스냅샷 조회"""
    snapshot = await AutoTradingService.get_risk_snapshot(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id
    )
    positions = [
        AutoTradingPositionRisk(**pos) for pos in snapshot["positions"]
    ]
    alerts = [
        AutoTradingRiskAlert(**alert) for alert in snapshot["alerts"]
    ]
    return AutoTradingRiskSnapshotResponse(
        as_of=snapshot["as_of"],
        cash_balance=snapshot["cash_balance"],
        invested_value=snapshot["invested_value"],
        total_value=snapshot["total_value"],
        exposure_ratio=snapshot["exposure_ratio"],
        alerts=alerts,
        positions=positions
    )


@router.post(
    "/strategies/{strategy_id}/risk/enforce",
    response_model=AutoTradingRiskEnforceResponse
)
async def enforce_risk_controls(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """위험 통제 강제 실행"""
    actions = await AutoTradingService.enforce_risk_controls(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id
    )
    message = "위험 통제 실행" if actions else "위험 조건에 해당하는 포지션이 없습니다."
    return AutoTradingRiskEnforceResponse(message=message, actions=actions)


@router.get(
    "/strategies/{strategy_id}/execution-report",
    response_model=AutoTradingExecutionReportResponse
)
async def get_execution_report(
    strategy_id: UUID,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """실거래 대비 백테스트 검증"""
    report = await AutoTradingService.get_execution_report(
        db=db,
        strategy_id=strategy_id,
        user_id=current_user.user_id,
        days=days
    )
    rows = [
        ExecutionReportRow(
            date=row["date"],
            live_total_value=row["live_total_value"],
            live_daily_return=row["live_daily_return"],
            backtest_total_value=row["backtest_total_value"],
            backtest_daily_return=row["backtest_daily_return"],
            tracking_error=row["tracking_error"]
        )
        for row in report["rows"]
    ]
    summary = ExecutionReportSummary(**report["summary"])
    return AutoTradingExecutionReportResponse(
        strategy_id=strategy_id,
        session_id=report.get("session_id"),
        generated_at=datetime.utcnow(),
        rows=rows,
        summary=summary
    )


@router.get("/dashboard", response_model=PortfolioDashboardResponse)
async def get_portfolio_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    포트폴리오 대시보드 통계
    - 전체 자산
    - 총 수익률
    - 활성 전략 수
    - 보유 종목 수
    - 오늘 매매 건수
    """
    try:
        dashboard_data = await AutoTradingService.get_portfolio_dashboard(
            db=db,
            user_id=current_user.user_id
        )

        return PortfolioDashboardResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"대시보드 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대시보드 조회에 실패했습니다."
        )
