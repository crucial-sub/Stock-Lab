"""
키움증권 API 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KiwoomCredentialsRequest(BaseModel):
    """키움증권 인증 정보 등록 요청"""
    app_key: str = Field(..., description="키움증권 앱 키")
    app_secret: str = Field(..., description="키움증권 앱 시크릿")


class KiwoomCredentialsResponse(BaseModel):
    """키움증권 인증 정보 등록 응답"""
    message: str
    access_token: str
    expires_at: datetime

    class Config:
        from_attributes = True


class AccountBalanceResponse(BaseModel):
    """계좌 잔고 조회 응답"""
    data: dict
    message: str = "계좌 잔고 조회 성공"

    class Config:
        from_attributes = True


class StockOrderRequest(BaseModel):
    """주식 주문 요청"""
    stock_code: str = Field(..., description="종목 코드")
    quantity: str = Field(..., description="주문 수량")
    price: Optional[str] = Field("", description="주문 단가 (시장가일 경우 빈 문자열)")
    trade_type: str = Field("3", description="매매 구분 (3: 시장가)")
    dmst_stex_tp: str = Field("KRX", description="국내거래소구분")


class StockOrderResponse(BaseModel):
    """주식 주문 응답"""
    data: dict
    message: str = "주문이 정상적으로 처리되었습니다."

    class Config:
        from_attributes = True
