"""
시세 페이지 API 스키마
- 전체 종목 리스트 조회
- 정렬 기능 (거래량, 등락률, 거래대금, 시가총액)
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class SortBy(str, Enum):
    """정렬 기준"""
    VOLUME = "volume"  # 거래량 순
    CHANGE_RATE = "change_rate"  # 등락률 순
    TRADING_VALUE = "trading_value"  # 거래대금 순
    MARKET_CAP = "market_cap"  # 시가총액 순
    NAME = "name"  # 종목명 순


class SortOrder(str, Enum):
    """정렬 순서"""
    ASC = "asc"  # 오름차순
    DESC = "desc"  # 내림차순


class MarketQuoteItem(BaseModel):
    """시세 항목"""
    model_config = ConfigDict(populate_by_name=True)

    rank: int = Field(..., description="순위 (정렬 기준에 따라 변동)")
    name: str = Field(..., description="종목명")
    code: str = Field(..., description="종목 코드")
    price: int = Field(..., description="현재가 (종가)")
    change_amount: int = Field(..., serialization_alias="changeAmount", description="전일 대비 가격 차이 (원)")
    change_rate: float = Field(..., serialization_alias="changeRate", description="전일 대비 등락률 (%)")
    trend: str = Field(..., description="등락 추세 (up/down/flat)")
    volume: int = Field(..., description="거래량 (주)")
    trading_value: int = Field(..., serialization_alias="tradingValue", description="거래대금 (원)")
    market_cap: Optional[int] = Field(None, serialization_alias="marketCap", description="시가총액 (원)")
    is_favorite: bool = Field(False, serialization_alias="isFavorite", description="관심종목 여부")


class MarketQuoteListResponse(BaseModel):
    """시세 리스트 응답"""
    model_config = ConfigDict(populate_by_name=True)

    items: List[MarketQuoteItem]
    total: int = Field(..., description="전체 종목 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., serialization_alias="pageSize", description="페이지 크기")
    has_next: bool = Field(..., serialization_alias="hasNext", description="다음 페이지 존재 여부")
