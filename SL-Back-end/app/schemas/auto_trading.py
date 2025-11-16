"""
자동매매 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID


# Request Schemas
class AutoTradingActivateRequest(BaseModel):
    """자동매매 활성화 요청"""
    session_id: str = Field(..., description="백테스트 세션 ID")
    initial_capital: Optional[Decimal] = Field(50000000, description="초기 자본금 (기본: 5천만원)")


class AutoTradingDeactivateRequest(BaseModel):
    """자동매매 비활성화 요청"""
    sell_all_positions: bool = Field(True, description="보유 종목 전량 매도 여부")


# Response Schemas
class LivePositionResponse(BaseModel):
    """보유 종목 응답"""
    position_id: UUID
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_buy_price: Decimal
    current_price: Optional[Decimal]
    buy_date: date
    hold_days: int
    unrealized_profit: Optional[Decimal]
    unrealized_profit_pct: Optional[Decimal]
    selection_reason: Optional[str]

    class Config:
        from_attributes = True


class LiveTradeResponse(BaseModel):
    """매매 내역 응답"""
    trade_id: UUID
    trade_date: date
    trade_time: Optional[time]
    trade_type: str
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    price: Decimal
    amount: Decimal
    commission: Decimal
    tax: Decimal
    profit: Optional[Decimal]
    profit_rate: Optional[Decimal]
    hold_days: Optional[int]
    selection_reason: Optional[str]
    order_status: str

    class Config:
        from_attributes = True


class LiveDailyPerformanceResponse(BaseModel):
    """일일 성과 응답"""
    performance_id: UUID
    date: date
    cash_balance: Decimal
    stock_value: Decimal
    total_value: Decimal
    daily_return: Optional[Decimal]
    cumulative_return: Optional[Decimal]
    buy_count: int
    sell_count: int
    trade_count: int
    position_count: int

    class Config:
        from_attributes = True


class AutoTradingStrategyResponse(BaseModel):
    """자동매매 전략 응답"""
    strategy_id: UUID
    user_id: UUID
    simulation_session_id: str
    is_active: bool
    initial_capital: Decimal
    current_capital: Decimal
    cash_balance: Decimal
    per_stock_ratio: Decimal
    max_positions: int
    rebalance_frequency: str
    created_at: datetime
    activated_at: Optional[datetime]
    deactivated_at: Optional[datetime]
    last_executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AutoTradingStatusResponse(BaseModel):
    """자동매매 상태 응답"""
    strategy: AutoTradingStrategyResponse
    positions: List[LivePositionResponse]
    today_trades: List[LiveTradeResponse]
    latest_performance: Optional[LiveDailyPerformanceResponse]
    total_positions: int
    total_trades: int


class AutoTradingActivateResponse(BaseModel):
    """자동매매 활성화 응답"""
    message: str
    strategy_id: UUID
    is_active: bool
    activated_at: datetime


class AutoTradingDeactivateResponse(BaseModel):
    """자동매매 비활성화 응답"""
    message: str
    strategy_id: UUID
    is_active: bool
    deactivated_at: datetime
    positions_sold: int


class AutoTradingLogResponse(BaseModel):
    """자동매매 로그 응답"""
    log_id: UUID
    event_type: str
    event_level: str
    message: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
