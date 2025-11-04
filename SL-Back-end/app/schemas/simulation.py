"""
백테스팅 시뮬레이션 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# =====================
# Enums
# =====================

class StrategyType(str, Enum):
    """전략 유형"""
    VALUE = "VALUE"
    GROWTH = "GROWTH"
    QUALITY = "QUALITY"
    MOMENTUM = "MOMENTUM"
    MULTI = "MULTI"


class UniverseType(str, Enum):
    """유니버스 유형"""
    ALL = "ALL"
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KOSPI200 = "KOSPI200"


class MarketCapFilter(str, Enum):
    """시가총액 필터"""
    ALL = "ALL"
    LARGE = "LARGE"  # 상위 30%
    MID = "MID"  # 중위 40%
    SMALL = "SMALL"  # 하위 30%


class UsageType(str, Enum):
    """팩터 사용 유형"""
    SCREENING = "SCREENING"  # 스크리닝 (조건 충족 종목 필터링)
    RANKING = "RANKING"  # 랭킹 (상위 N개 선택)
    SCORING = "SCORING"  # 스코어링 (점수화하여 가중합)


class Operator(str, Enum):
    """연산자"""
    GT = "GT"  # Greater Than (>)
    LT = "LT"  # Less Than (<)
    GTE = "GTE"  # >=
    LTE = "LTE"  # <=
    EQ = "EQ"  # ==
    TOP_N = "TOP_N"  # 상위 N%
    BOTTOM_N = "BOTTOM_N"  # 하위 N%


class RebalanceFrequency(str, Enum):
    """리밸런싱 주기"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class PositionSizing(str, Enum):
    """포지션 크기 결정 방식"""
    EQUAL_WEIGHT = "EQUAL_WEIGHT"  # 동일 가중
    MARKET_CAP = "MARKET_CAP"  # 시가총액 가중
    RISK_PARITY = "RISK_PARITY"  # 리스크 패리티
    SCORE_WEIGHT = "SCORE_WEIGHT"  # 스코어 가중


class SimulationStatus(str, Enum):
    """시뮬레이션 상태"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =====================
# 전략 생성/수정
# =====================

class StrategyFactorCreate(BaseModel):
    """전략 팩터 생성"""
    factor_id: str
    usage_type: UsageType
    operator: Optional[Operator] = None
    threshold_value: Optional[Decimal] = None
    weight: Optional[Decimal] = Field(None, ge=0, le=1, description="가중치 (0~1)")
    direction: Optional[str] = Field(None, description="POSITIVE or NEGATIVE")


class TradingRuleCreate(BaseModel):
    """매매 규칙 생성"""
    rule_type: str = Field(default="REBALANCE")
    rebalance_frequency: RebalanceFrequency
    rebalance_day: Optional[int] = Field(None, ge=1, le=31)
    position_sizing: PositionSizing = PositionSizing.EQUAL_WEIGHT
    max_positions: int = Field(..., ge=1, le=200)
    min_position_weight: Optional[Decimal] = Field(None, ge=0, le=1)
    max_position_weight: Optional[Decimal] = Field(None, ge=0, le=1)
    stop_loss_pct: Optional[Decimal] = None
    take_profit_pct: Optional[Decimal] = None
    commission_rate: Decimal = Field(default=Decimal("0.00015"), description="수수료율")
    tax_rate: Decimal = Field(default=Decimal("0.0023"), description="세금율")


class PortfolioStrategyCreate(BaseModel):
    """포트폴리오 전략 생성"""
    strategy_name: str = Field(..., min_length=1, max_length=200)
    strategy_type: Optional[StrategyType] = None
    description: Optional[str] = None
    backtest_start_date: date
    backtest_end_date: date
    universe_type: UniverseType = UniverseType.ALL
    market_cap_filter: MarketCapFilter = MarketCapFilter.ALL
    sector_filter: Optional[List[str]] = None
    initial_capital: Decimal = Field(..., gt=0)
    strategy_factors: List[StrategyFactorCreate]
    trading_rule: TradingRuleCreate

    @validator('backtest_end_date')
    def validate_dates(cls, v, values):
        if 'backtest_start_date' in values and v <= values['backtest_start_date']:
            raise ValueError('종료일은 시작일보다 커야 합니다')
        return v


class PortfolioStrategyResponse(BaseModel):
    """포트폴리오 전략 응답"""
    strategy_id: str
    strategy_name: str
    strategy_type: Optional[str]
    description: Optional[str]
    backtest_start_date: date
    backtest_end_date: date
    universe_type: str
    market_cap_filter: str
    initial_capital: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================
# 시뮬레이션 실행
# =====================

class SimulationRequest(BaseModel):
    """시뮬레이션 실행 요청"""
    strategy_id: str
    session_name: Optional[str] = None
    start_date: date
    end_date: date
    initial_capital: Decimal = Field(..., gt=0)
    benchmark: Optional[str] = Field(default="KOSPI", description="벤치마크")

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('종료일은 시작일보다 커야 합니다')
        return v


class SimulationSessionResponse(BaseModel):
    """시뮬레이션 세션 응답"""
    session_id: str
    strategy_id: str
    session_name: Optional[str]
    start_date: date
    end_date: date
    initial_capital: Decimal
    benchmark: Optional[str]
    status: str
    progress: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# =====================
# 시뮬레이션 결과
# =====================

class SimulationStatisticsResponse(BaseModel):
    """시뮬레이션 통계 응답"""
    session_id: str

    # 수익률
    total_return: Optional[Decimal]
    annualized_return: Optional[Decimal]
    benchmark_return: Optional[Decimal]
    excess_return: Optional[Decimal]

    # 리스크
    volatility: Optional[Decimal]
    max_drawdown: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    sortino_ratio: Optional[Decimal]

    # 거래
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Optional[Decimal]
    avg_profit: Optional[Decimal]
    avg_loss: Optional[Decimal]
    profit_factor: Optional[Decimal]
    avg_holding_period: Optional[int]

    # 자본
    final_capital: Optional[Decimal]
    total_commission: Optional[Decimal]
    total_tax: Optional[Decimal]

    class Config:
        from_attributes = True


class SimulationDailyValueResponse(BaseModel):
    """일별 가치 응답"""
    date: date
    portfolio_value: Decimal
    cash: Decimal
    position_value: Decimal
    daily_return: Optional[Decimal]
    cumulative_return: Optional[Decimal]
    benchmark_return: Optional[Decimal]
    benchmark_cum_return: Optional[Decimal]
    daily_drawdown: Optional[Decimal]

    class Config:
        from_attributes = True


class SimulationTradeResponse(BaseModel):
    """거래 기록 응답"""
    trade_id: int
    trade_date: date
    stock_code: str
    stock_name: Optional[str]
    trade_type: str
    quantity: int
    price: Decimal
    amount: Decimal
    commission: Optional[Decimal]
    tax: Optional[Decimal]
    realized_pnl: Optional[Decimal]
    return_pct: Optional[Decimal]
    holding_days: Optional[int]
    reason: Optional[str]

    class Config:
        from_attributes = True


class SimulationPositionResponse(BaseModel):
    """포지션 응답"""
    date: date
    stock_code: str
    stock_name: Optional[str]
    quantity: int
    avg_buy_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Optional[Decimal]
    return_pct: Optional[Decimal]
    weight: Optional[Decimal]

    class Config:
        from_attributes = True


class SimulationResultResponse(BaseModel):
    """시뮬레이션 종합 결과"""
    session: SimulationSessionResponse
    statistics: Optional[SimulationStatisticsResponse]
    daily_values: List[SimulationDailyValueResponse]
    trades: List[SimulationTradeResponse]
    final_positions: List[SimulationPositionResponse]


# =====================
# 성과 비교
# =====================

class StrategyComparisonRequest(BaseModel):
    """전략 비교 요청"""
    session_ids: List[str] = Field(..., min_items=2, max_items=10)


class StrategyComparisonItem(BaseModel):
    """전략 비교 항목"""
    session_id: str
    strategy_name: str
    total_return: Optional[Decimal]
    annualized_return: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    max_drawdown: Optional[Decimal]
    win_rate: Optional[Decimal]


class StrategyComparisonResponse(BaseModel):
    """전략 비교 응답"""
    strategies: List[StrategyComparisonItem]
