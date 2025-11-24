"""
키움증권 API 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


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


class PerformanceChartDataPoint(BaseModel):
    """성과 차트 데이터 포인트"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    total_value: str = Field(..., description="총 자산 가치")
    daily_return: Optional[str] = Field(None, description="일일 수익률 (%)")
    cumulative_return: Optional[str] = Field(None, description="누적 수익률 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-21",
                "total_value": "10500000",
                "daily_return": "0.50",
                "cumulative_return": "5.00"
            }
        }


class AccountPerformanceChartResponse(BaseModel):
    """계좌 성과 차트 응답"""
    data_points: List[PerformanceChartDataPoint] = Field(default_factory=list, description="차트 데이터 포인트 리스트")
    initial_capital: str = Field(..., description="초기 자본금")
    current_value: str = Field(..., description="현재 총 자산")
    total_return: str = Field(..., description="총 수익률 (%)")
    days: int = Field(..., description="데이터 일수")

    class Config:
        json_schema_extra = {
            "example": {
                "data_points": [
                    {
                        "date": "2025-11-21",
                        "total_value": "10500000",
                        "daily_return": "0.50",
                        "cumulative_return": "5.00"
                    }
                ],
                "initial_capital": "10000000",
                "current_value": "10500000",
                "total_return": "5.00",
                "days": 30
            }
        }
