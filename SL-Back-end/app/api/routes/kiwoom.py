"""
키움증권 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
    StockOrderResponse
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """
    키움증권 연동 해제
    """
    try:
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )

        user.kiwoom_app_key = None
        user.kiwoom_app_secret = None
        user.kiwoom_access_token = None
        user.kiwoom_token_expires_at = None

        db.commit()

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
    db: Session = Depends(get_db)
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
        # 토큰 갱신이 필요한 경우 갱신
        access_token = KiwoomService.refresh_token_if_needed(db, current_user)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="키움증권 연동이 필요합니다. 먼저 API KEY를 등록해주세요."
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


@router.post("/order/buy", response_model=StockOrderResponse)
async def buy_stock(
    order_request: StockOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    주식 매수 주문
    """
    try:
        # 토큰 갱신이 필요한 경우 갱신
        access_token = KiwoomService.refresh_token_if_needed(db, current_user)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="키움증권 연동이 필요합니다. 먼저 API KEY를 등록해주세요."
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
    db: Session = Depends(get_db)
):
    """
    주식 매도 주문
    """
    try:
        # 토큰 갱신이 필요한 경우 갱신
        access_token = KiwoomService.refresh_token_if_needed(db, current_user)

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="키움증권 연동이 필요합니다. 먼저 API KEY를 등록해주세요."
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
