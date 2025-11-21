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
    initial_capital: Optional[Decimal] = Field(None, description="초기 자본금 (None이면 키움 계좌 잔고 자동 조회)")
    allocated_capital: Decimal = Field(..., description="전략에 할당할 자본금 (원). 여러 전략에 계좌 잔액을 나누어 배분 가능.", gt=0)
    strategy_name: Optional[str] = Field(None, description="자동매매 전략 이름 (미입력시 자동 생성)")


class AutoTradingDeactivateRequest(BaseModel):
    """자동매매 비활성화 요청"""
    sell_all_positions: bool = Field(True, description="보유 종목 전량 매도 여부")
    deactivation_mode: Optional[str] = Field(None, description="비활성화 모드: immediate(즉시), sell_and_deactivate(매도 후 비활성화), scheduled_sell(예약 매도)")


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
    strategy_name: Optional[str] = Field(None, description="자동매매 전략 이름")
    is_active: bool
    initial_capital: Decimal
    allocated_capital: Decimal
    current_capital: Decimal
    cash_balance: Decimal
    per_stock_ratio: Decimal
    max_positions: int
    rebalance_frequency: str
    created_at: datetime
    activated_at: Optional[datetime]
    deactivated_at: Optional[datetime]
    last_executed_at: Optional[datetime]
    scheduled_deactivation: Optional[bool] = Field(None, description="예약 비활성화 여부")
    deactivation_mode: Optional[str] = Field(None, description="비활성화 모드")
    deactivation_requested_at: Optional[datetime] = Field(None, description="비활성화 요청 시각")
    kiwoom_total_eval: Optional[Decimal] = Field(None, description="키움 API 총 평가액")
    kiwoom_total_profit: Optional[Decimal] = Field(None, description="키움 API 평가손익")
    kiwoom_total_profit_rate: Optional[Decimal] = Field(None, description="키움 API 수익률(%)")

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


class TradeSignalItem(BaseModel):
    """리밸런싱/시그널 항목"""
    stock_code: str
    stock_name: Optional[str]
    quantity: Optional[int]
    target_weight: Optional[float]
    current_price: Optional[float]
    per: Optional[float]
    pbr: Optional[float]
    metadata: Optional[Dict[str, Any]] = None


class RebalancePreviewResponse(BaseModel):
    """리밸런싱 미리보기 응답"""
    generated_at: datetime
    candidates: List[TradeSignalItem]
    note: Optional[str] = None


class AutoTradingLogListResponse(BaseModel):
    """로그 리스트 응답"""
    logs: List[AutoTradingLogResponse]


class AutoTradingRiskAlert(BaseModel):
    """위험 경보"""
    type: str
    severity: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class AutoTradingPositionRisk(BaseModel):
    """포지션별 위험 정보"""
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    market_value: Decimal
    avg_buy_price: Decimal
    current_price: Decimal
    unrealized_profit: Decimal
    unrealized_profit_pct: Decimal
    hold_days: int


class AutoTradingRiskSnapshotResponse(BaseModel):
    """위험 스냅샷 응답"""
    as_of: datetime
    cash_balance: Decimal
    invested_value: Decimal
    total_value: Decimal
    exposure_ratio: float
    alerts: List[AutoTradingRiskAlert]
    positions: List[AutoTradingPositionRisk]


class ExecutionReportRow(BaseModel):
    """실거래 vs 백테스트 비교 행"""
    date: date
    live_total_value: Optional[Decimal]
    live_daily_return: Optional[Decimal]
    backtest_total_value: Optional[Decimal]
    backtest_daily_return: Optional[Decimal]
    tracking_error: Optional[Decimal]


class ExecutionReportSummary(BaseModel):
    """실행 보고서 요약"""
    days: int
    average_tracking_error: Optional[Decimal]
    cumulative_live_return: Optional[Decimal]
    cumulative_backtest_return: Optional[Decimal]
    realized_vs_expected: Optional[Decimal]


class AutoTradingExecutionReportResponse(BaseModel):
    """실거래 검증 리포트"""
    strategy_id: UUID
    session_id: str
    generated_at: datetime
    rows: List[ExecutionReportRow]
    summary: ExecutionReportSummary


class AutoTradingRiskEnforceResponse(BaseModel):
    """위험 통제 실행 결과"""
    message: str
    actions: List[Dict[str, Any]]


class PortfolioDashboardResponse(BaseModel):
    """포트폴리오 대시보드 응답"""
    total_assets: Decimal  # 총 자산 (자동매매 계좌 전체)
    total_return: Decimal  # 총 수익률 (%)
    total_profit: Decimal  # 총 수익금
    active_strategy_count: int  # 활성 전략 수
    total_positions: int  # 전체 보유 종목 수
    total_trades_today: int  # 오늘 총 매매 건수
    total_allocated_capital: Decimal  # 자동매매에 할당된 총 금액
