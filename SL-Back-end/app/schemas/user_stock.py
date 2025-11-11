"""
사용자 관심종목/최근 본 주식 스키마
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ==================== 관심종목 ====================

class FavoriteStockAdd(BaseModel):
    """관심종목 추가 요청"""
    stock_code: str = Field(..., description="종목 코드")


class FavoriteStockItem(BaseModel):
    """관심종목 항목"""
    model_config = ConfigDict(populate_by_name=True)

    stock_code: str = Field(..., serialization_alias="stockCode", description="종목 코드")
    stock_name: str = Field(..., serialization_alias="stockName", description="종목명")
    current_price: Optional[int] = Field(None, serialization_alias="currentPrice", description="현재가")
    change_rate: Optional[float] = Field(None, serialization_alias="changeRate", description="등락률(%)")
    previous_close: Optional[int] = Field(None, serialization_alias="previousClose", description="전일 종가")
    volume: Optional[int] = Field(None, description="거래량")
    trading_value: Optional[int] = Field(None, serialization_alias="tradingValue", description="거래대금")
    market_cap: Optional[int] = Field(None, serialization_alias="marketCap", description="시가총액")
    created_at: datetime = Field(..., serialization_alias="createdAt", description="등록일시")


class FavoriteStockListResponse(BaseModel):
    """관심종목 리스트 응답"""
    model_config = ConfigDict(populate_by_name=True)

    items: List[FavoriteStockItem]
    total: int = Field(..., description="전체 관심종목 수")


# ==================== 최근 본 주식 ====================

class RecentStockItem(BaseModel):
    """최근 본 주식 항목"""
    model_config = ConfigDict(populate_by_name=True)

    stock_code: str = Field(..., serialization_alias="stockCode", description="종목 코드")
    stock_name: str = Field(..., serialization_alias="stockName", description="종목명")
    current_price: Optional[int] = Field(None, serialization_alias="currentPrice", description="현재가")
    change_rate: Optional[float] = Field(None, serialization_alias="changeRate", description="등락률(%)")
    previous_close: Optional[int] = Field(None, serialization_alias="previousClose", description="전일 종가")
    volume: Optional[int] = Field(None, description="거래량")
    trading_value: Optional[int] = Field(None, serialization_alias="tradingValue", description="거래대금")
    market_cap: Optional[int] = Field(None, serialization_alias="marketCap", description="시가총액")
    viewed_at: datetime = Field(..., serialization_alias="viewedAt", description="조회일시")


class RecentStockListResponse(BaseModel):
    """최근 본 주식 리스트 응답"""
    model_config = ConfigDict(populate_by_name=True)

    items: List[RecentStockItem]
    total: int = Field(..., description="전체 개수")
