"""
키움증권 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.kiwoom import (
    KiwoomCredentialsRequest,
    KiwoomCredentialsResponse,
    AccountBalanceResponse,
    StockOrderRequest,
    StockOrderResponse,
    AccountPerformanceChartResponse,
    PerformanceChartDataPoint
)
from app.services.kiwoom_service import KiwoomService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/kiwoom",
    tags=["kiwoom"]
)


@router.post("/credentials", response_model=KiwoomCredentialsResponse)
async def register_kiwoom_credentials(
    credentials: KiwoomCredentialsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    키움증권 API KEY 등록

    - **app_key**: 키움증권 앱 키
    - **app_secret**: 키움증권 앱 시크릿
    """
    try:
        # 1. 키움증권 API로 토큰 발급 시도
        response_data = KiwoomService.get_access_token(
            credentials.app_key,
            credentials.app_secret
        )

        # 2. 토큰 발급 성공시 DB에 저장
        # 키움 API는 'token' 필드로 응답 (access_token이 아님)
        access_token = response_data.get("token")

        if not access_token:
            # 키움 API의 에러 메시지 확인
            return_code = response_data.get("return_code")
            return_msg = response_data.get("return_msg", "키움증권 API로부터 토큰을 받지 못했습니다.")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=return_msg
            )

        # expires_dt를 파싱하여 만료 시간(초) 계산
        # 형식: YYYYMMDDHHmmss (예: 20251117005216)
        expires_dt = response_data.get("expires_dt")
        if expires_dt:
            from datetime import datetime
            try:
                expire_time = datetime.strptime(expires_dt, "%Y%m%d%H%M%S")
                now = datetime.now()
                expires_in = int((expire_time - now).total_seconds())
            except:
                expires_in = 86400  # 파싱 실패시 기본 24시간
        else:
            expires_in = 86400  # 기본 24시간

        # 3. 사용자 정보 업데이트
        updated_user = await KiwoomService.update_user_kiwoom_credentials(
            db=db,
            user_id=str(current_user.user_id),
            app_key=credentials.app_key,
            app_secret=credentials.app_secret,
            access_token=access_token,
            expires_in=expires_in
        )

        return KiwoomCredentialsResponse(
            message="키움증권 연동이 완료되었습니다.",
            access_token=access_token,
            expires_at=updated_user.kiwoom_token_expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키움증권 인증 정보 등록 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"키움증권 연동에 실패했습니다: {str(e)}"
        )


@router.get("/credentials/status")
async def get_kiwoom_status(
    current_user: User = Depends(get_current_user)
):
    """
    키움증권 연동 상태 조회
    """
    is_connected = bool(
        current_user.kiwoom_app_key and
        current_user.kiwoom_access_token and
        current_user.kiwoom_token_expires_at
    )

    return {
        "is_connected": is_connected,
        "expires_at": current_user.kiwoom_token_expires_at if is_connected else None
    }


@router.delete("/credentials")
async def delete_kiwoom_credentials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    키움증권 연동 해제
    """
    try:
        from sqlalchemy import select

        stmt = select(User).where(User.user_id == current_user.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )

        user.kiwoom_app_key = None
        user.kiwoom_app_secret = None
        user.kiwoom_access_token = None
        user.kiwoom_token_expires_at = None

        await db.commit()

        return {"message": "키움증권 연동이 해제되었습니다."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"키움증권 연동 해제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="키움증권 연동 해제에 실패했습니다."
        )


@router.get("/account/balance", response_model=AccountBalanceResponse)
async def get_account_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    통합 계좌 잔고 조회 (실시간)

    5개의 키움 API를 통합하여 제공:
    - 예수금 정보 (kt00001): 현금 잔액, 주문가능금액 등
    - 계좌 평가/잔고 (kt00018): 보유 종목, 평가액 등
    - 수익률 (ka10085): 수익률 정보
    - 미체결 (ka10075): 미체결 주문 내역
    - 체결 (ka10076): 체결 주문 내역
    """
    try:
        # 토큰 유효성 확인 및 자동 갱신 (만료된 경우에도 처리)
        try:
            access_token = await KiwoomService.ensure_valid_token(db, current_user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

        # 통합 잔고 조회 (5개 API 호출)
        unified_data = KiwoomService.get_unified_balance(access_token)

        return AccountBalanceResponse(
            data=unified_data,
            message="통합 계좌 잔고 조회 성공"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"통합 계좌 잔고 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통합 계좌 잔고 조회에 실패했습니다: {str(e)}"
        )


@router.get("/account/performance-chart", response_model=AccountPerformanceChartResponse)
async def get_account_performance_chart(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    계좌 성과 차트 데이터 조회

    - 활성화된 모든 자동매매 전략의 일일 성과를 집계
    - 총 자산 가치와 수익률 추이를 시계열로 제공
    - days: 조회할 최근 일수 (기본 30일)
    """
    try:
        from sqlalchemy import select, and_, func
        from app.models.auto_trading import AutoTradingStrategy, LiveDailyPerformance
        from decimal import Decimal
        from collections import defaultdict

        # 1. 사용자의 활성 전략 조회
        strategies_query = select(AutoTradingStrategy).where(
            AutoTradingStrategy.user_id == current_user.user_id
        )
        strategies_result = await db.execute(strategies_query)
        strategies = strategies_result.scalars().all()

        if not strategies:
            # 전략이 없는 경우 빈 데이터 반환
            return AccountPerformanceChartResponse(
                data_points=[],
                initial_capital="0",
                current_value="0",
                total_return="0",
                days=0
            )

        strategy_ids = [s.strategy_id for s in strategies]

        # 2. 최근 N일의 일일 성과 데이터 조회
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        performances_query = select(LiveDailyPerformance).where(
            and_(
                LiveDailyPerformance.strategy_id.in_(strategy_ids),
                LiveDailyPerformance.date >= start_date,
                LiveDailyPerformance.date <= end_date
            )
        ).order_by(LiveDailyPerformance.date.asc())

        performances_result = await db.execute(performances_query)
        performances = performances_result.scalars().all()

        if not performances:
            # 성과 데이터가 없는 경우
            total_initial = sum(s.initial_capital for s in strategies)
            total_current = sum(s.current_capital for s in strategies)

            return AccountPerformanceChartResponse(
                data_points=[],
                initial_capital=str(total_initial),
                current_value=str(total_current),
                total_return="0",
                days=0
            )

        # 3. 날짜별로 전략들의 성과 집계
        daily_aggregated = defaultdict(lambda: {
            'total_value': Decimal("0"),
            'count': 0
        })

        for perf in performances:
            daily_aggregated[perf.date]['total_value'] += perf.total_value
            daily_aggregated[perf.date]['count'] += 1

        # 4. 초기 자본 계산 (모든 전략의 초기 자본 합계)
        total_initial_capital = sum(s.initial_capital for s in strategies)

        # 5. 데이터 포인트 생성
        data_points = []
        sorted_dates = sorted(daily_aggregated.keys())

        for i, current_date in enumerate(sorted_dates):
            total_value = daily_aggregated[current_date]['total_value']

            # 일일 수익률 계산 (전일 대비)
            if i > 0:
                prev_date = sorted_dates[i - 1]
                prev_value = daily_aggregated[prev_date]['total_value']
                if prev_value > 0:
                    daily_return = ((total_value - prev_value) / prev_value) * 100
                else:
                    daily_return = Decimal("0")
            else:
                daily_return = None

            # 누적 수익률 계산 (초기 자본 대비)
            if total_initial_capital > 0:
                cumulative_return = ((total_value - total_initial_capital) / total_initial_capital) * 100
            else:
                cumulative_return = Decimal("0")

            data_points.append(
                PerformanceChartDataPoint(
                    date=str(current_date),
                    total_value=str(total_value),
                    daily_return=str(daily_return) if daily_return is not None else None,
                    cumulative_return=str(cumulative_return)
                )
            )

        # 6. 현재 총 자산 및 총 수익률 계산
        if data_points:
            current_value_decimal = daily_aggregated[sorted_dates[-1]]['total_value']
            if total_initial_capital > 0:
                total_return_decimal = ((current_value_decimal - total_initial_capital) / total_initial_capital) * 100
            else:
                total_return_decimal = Decimal("0")
        else:
            current_value_decimal = total_initial_capital
            total_return_decimal = Decimal("0")

        return AccountPerformanceChartResponse(
            data_points=data_points,
            initial_capital=str(total_initial_capital),
            current_value=str(current_value_decimal),
            total_return=str(total_return_decimal),
            days=len(data_points)
        )

    except Exception as e:
        logger.error(f"계좌 성과 차트 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"계좌 성과 차트 조회에 실패했습니다: {str(e)}"
        )


@router.post("/order/buy", response_model=StockOrderResponse)
async def buy_stock(
    order_request: StockOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    주식 매수 주문
    """
    try:
        # 토큰 유효성 확인 및 자동 갱신 (만료된 경우에도 처리)
        try:
            access_token = await KiwoomService.ensure_valid_token(db, current_user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

        # 매수 주문
        order_result = KiwoomService.buy_stock(
            access_token=access_token,
            stock_code=order_request.stock_code,
            quantity=order_request.quantity,
            price=order_request.price,
            trade_type=order_request.trade_type,
            dmst_stex_tp=order_request.dmst_stex_tp
        )

        return StockOrderResponse(
            data=order_result,
            message="매수 주문이 정상적으로 처리되었습니다."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"매수 주문 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매수 주문에 실패했습니다: {str(e)}"
        )


@router.post("/order/sell", response_model=StockOrderResponse)
async def sell_stock(
    order_request: StockOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    주식 매도 주문
    """
    try:
        # 토큰 유효성 확인 및 자동 갱신 (만료된 경우에도 처리)
        try:
            access_token = await KiwoomService.ensure_valid_token(db, current_user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

        # 매도 주문
        order_result = KiwoomService.sell_stock(
            access_token=access_token,
            stock_code=order_request.stock_code,
            quantity=order_request.quantity,
            price=order_request.price,
            trade_type=order_request.trade_type,
            dmst_stex_tp=order_request.dmst_stex_tp
        )

        return StockOrderResponse(
            data=order_result,
            message="매도 주문이 정상적으로 처리되었습니다."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"매도 주문 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"매도 주문에 실패했습니다: {str(e)}"
        )
