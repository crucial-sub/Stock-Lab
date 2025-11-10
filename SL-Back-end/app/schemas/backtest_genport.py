"""
GenPort 스타일 백테스트 스키마 정의
스크린샷 기반으로 설계된 응답 모델
- 논리식 조건 지원 추가
- 필수 Enum 타입 추가
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum


# ==================== Enums (필수 항목만) ====================

class RebalanceFrequency(str, Enum):
    """리밸런싱 주기"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"


class PositionSizingMethod(str, Enum):
    """포지션 크기 결정 방법"""
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    MARKET_CAP = "MARKET_CAP"
    RISK_PARITY = "RISK_PARITY"


class SellConditionType(str, Enum):
    """매도 조건 타입"""
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    HOLD_DAYS = "HOLD_DAYS"
    REBALANCE = "REBALANCE"


class PortfolioHolding(BaseModel):
    """현재 보유 종목 정보"""
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목명")
    quantity: int = Field(..., description="보유 수량")
    avg_price: Decimal = Field(..., description="평균 매수가")
    current_price: Decimal = Field(..., description="현재가")
    value: Decimal = Field(..., description="평가금액")
    profit: Decimal = Field(..., description="손익")
    profit_rate: Decimal = Field(..., description="수익률 (%)")
    weight: Decimal = Field(..., description="포트폴리오 비중 (%)")
    buy_date: date = Field(..., description="최초 매수일")
    hold_days: int = Field(..., description="보유일수")

    # 팩터 정보
    factors: Dict[str, float] = Field(default_factory=dict, description="현재 팩터 값")


class DailyPerformance(BaseModel):
    """일별 성과 데이터"""
    date: date
    portfolio_value: Decimal = Field(..., description="포트폴리오 가치")
    cash_balance: Decimal = Field(..., description="현금 잔고")
    invested_amount: Decimal = Field(..., description="투자 금액")
    daily_return: Decimal = Field(..., description="일 수익률 (%)")
    cumulative_return: Decimal = Field(..., description="누적 수익률 (%)")
    drawdown: Decimal = Field(..., description="낙폭 (%)")
    benchmark_return: Optional[Decimal] = Field(None, description="벤치마크 수익률 (%)")
    trade_count: int = Field(0, description="당일 거래 횟수")


class MonthlyPerformance(BaseModel):
    """월별 성과 데이터"""
    year: int
    month: int
    return_rate: Decimal = Field(..., description="월 수익률 (%)")
    benchmark_return: Optional[Decimal] = Field(None, description="벤치마크 월 수익률 (%)")
    win_rate: Decimal = Field(..., description="승률 (%)")
    trade_count: int = Field(..., description="거래 횟수")
    avg_hold_days: int = Field(..., description="평균 보유일수")


class YearlyPerformance(BaseModel):
    """연도별 성과 데이터"""
    year: int
    return_rate: Decimal = Field(..., description="연 수익률 (%)")
    benchmark_return: Optional[Decimal] = Field(None, description="벤치마크 연 수익률 (%)")
    max_drawdown: Decimal = Field(..., description="최대 낙폭 (%)")
    sharpe_ratio: Decimal = Field(..., description="샤프 비율")
    trades: int = Field(..., description="총 거래 횟수")


class TradeRecord(BaseModel):
    """거래 기록"""
    trade_id: str = Field(..., description="거래 ID")
    trade_date: date = Field(..., description="거래일")
    trade_type: str = Field(..., description="거래 유형 (BUY/SELL)")
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목명")
    quantity: int = Field(..., description="수량")
    price: Decimal = Field(..., description="거래가")
    amount: Decimal = Field(..., description="거래대금")
    commission: Decimal = Field(..., description="수수료")
    tax: Decimal = Field(..., description="세금")

    # 매도 시에만
    profit: Optional[Decimal] = Field(None, description="실현 손익")
    profit_rate: Optional[Decimal] = Field(None, description="수익률 (%)")
    hold_days: Optional[int] = Field(None, description="보유일수")

    # 거래 시점 팩터 정보
    factors: Dict[str, float] = Field(default_factory=dict, description="거래 시점 팩터 값")
    selection_reason: Optional[str] = Field(None, description="매매 사유")


class BacktestStatistics(BaseModel):
    """백테스트 통계"""
    # 수익률 지표
    total_return: Decimal = Field(..., description="총 수익률 (%)")
    annualized_return: Decimal = Field(..., description="연환산 수익률 (CAGR) (%)")
    benchmark_return: Optional[Decimal] = Field(None, description="벤치마크 수익률 (%)")
    excess_return: Optional[Decimal] = Field(None, description="초과 수익률 (%)")

    # 리스크 지표
    max_drawdown: Decimal = Field(..., description="최대 낙폭 (MDD) (%)")
    volatility: Decimal = Field(..., description="변동성 (%)")
    downside_volatility: Decimal = Field(..., description="하방 변동성 (%)")

    # 리스크 조정 수익률
    sharpe_ratio: Decimal = Field(..., description="샤프 비율")
    sortino_ratio: Decimal = Field(..., description="소르티노 비율")
    calmar_ratio: Decimal = Field(..., description="칼마 비율")

    # 거래 통계
    total_trades: int = Field(..., description="총 거래 횟수")
    winning_trades: int = Field(..., description="수익 거래 횟수")
    losing_trades: int = Field(..., description="손실 거래 횟수")
    win_rate: Decimal = Field(..., description="승률 (%)")
    avg_win: Decimal = Field(..., description="평균 수익 (%)")
    avg_loss: Decimal = Field(..., description="평균 손실 (%)")
    profit_loss_ratio: Decimal = Field(..., description="손익비")

    # 자산 정보
    initial_capital: Decimal = Field(..., description="초기 자본금")
    final_capital: Decimal = Field(..., description="최종 자본금")
    peak_capital: Decimal = Field(..., description="최대 자본금")

    # 기간 정보
    start_date: date = Field(..., description="시작일")
    end_date: date = Field(..., description="종료일")
    trading_days: int = Field(..., description="거래일수")


class BacktestCondition(BaseModel):
    """백테스트 조건 (기존 방식 + 논리식 지원)"""
    factor: str = Field(..., description="팩터 코드")
    operator: str = Field(..., description="연산자 (>, <, >=, <=, ==)")
    value: Union[float, List[float]] = Field(..., description="비교값 또는 범위")
    description: Optional[str] = Field(None, description="조건 설명")

    # 논리식용 필드 (선택적)
    id: Optional[str] = Field(None, description="조건 ID (논리식 사용 시: A, B, C 등)")

    @validator('value')
    def validate_value_type(cls, v, values):
        """연산자에 따른 값 타입 검증"""
        if 'operator' in values:
            op = values['operator']
            if op == 'BETWEEN' and not isinstance(v, list):
                raise ValueError("BETWEEN operator requires a list of two values")
        return v


class BacktestConditionExpression(BaseModel):
    """논리식 기반 조건 (새로운 방식)"""
    expression: str = Field(..., description="논리식 (예: '(A and B) or C')")
    conditions: List[BacktestCondition] = Field(..., description="조건 정의 리스트")
    factor_weights: Optional[Dict[str, float]] = Field(
        None,
        description="팩터 가중치 (선택적, 순위 매기기용)"
    )

    @validator('expression')
    def validate_expression(cls, v):
        """논리식 기본 검증"""
        allowed_keywords = {'and', 'or', 'not', '(', ')'}
        tokens = v.replace('(', ' ( ').replace(')', ' ) ').lower().split()

        for token in tokens:
            if token not in allowed_keywords and not (token.isalpha() and len(token) == 1):
                # 조건 ID가 아니고 허용된 키워드도 아니면 에러
                if token not in allowed_keywords:
                    raise ValueError(f"Invalid token in expression: {token}")
        return v


class BacktestSettings(BaseModel):
    """백테스트 설정"""
    rebalance_frequency: str = Field(..., description="리밸런싱 주기")
    max_positions: int = Field(..., description="최대 보유 종목 수")
    position_sizing: str = Field(..., description="포지션 사이징 방법")
    benchmark: str = Field(..., description="벤치마크")
    commission_rate: float = Field(..., description="수수료율 (사용자 설정)")
    tax_rate: float = Field(..., description="거래세율 (고정값 0.23%)")
    slippage: float = Field(..., description="슬리피지 (사용자 설정)")


class BacktestCreateRequest(BaseModel):
    """백테스트 생성 요청"""
    # 기본 조건 방식 (하위 호환)
    buy_conditions: Optional[List[BacktestCondition]] = Field(
        None,
        description="매수 조건 리스트 (기존 방식)"
    )

    # 논리식 조건 방식 (새로운 방식)
    buy_expression: Optional[BacktestConditionExpression] = Field(
        None,
        description="매수 논리식 조건 (새로운 방식)"
    )

    sell_conditions: List[BacktestCondition] = Field(..., description="매도 조건")

    # 백테스트 설정
    start_date: date = Field(..., description="시작일")
    end_date: date = Field(..., description="종료일")
    initial_capital: float = Field(100_000_000, description="초기 자본")
    rebalance_frequency: str = Field("MONTHLY", description="리밸런싱 주기")
    max_positions: int = Field(20, description="최대 보유 종목 수")
    position_sizing: str = Field("EQUAL_WEIGHT", description="포지션 사이징 방법")
    benchmark: Optional[str] = Field(None, description="벤치마크")
    commission_rate: float = Field(0.00015, description="수수료율")
    slippage: float = Field(0.001, description="슬리피지")

    @validator('buy_conditions', 'buy_expression')
    def validate_buy_conditions(cls, v, values, field):
        """buy_conditions 또는 buy_expression 중 하나는 반드시 있어야 함"""
        if field.name == 'buy_expression':
            # buy_expression 검증 시점에 buy_conditions 확인
            buy_conds = values.get('buy_conditions')
            if not v and not buy_conds:
                raise ValueError("Either buy_conditions or buy_expression must be provided")
        return v


class BacktestResultGenPort(BaseModel):
    """GenPort 스타일 백테스트 결과"""

    # 백테스트 정보
    backtest_id: str = Field(..., description="백테스트 ID")
    backtest_name: str = Field(..., description="백테스트 이름")
    status: str = Field(..., description="상태")
    created_at: datetime = Field(..., description="생성 시간")
    completed_at: Optional[datetime] = Field(None, description="완료 시간")

    # 설정 정보
    settings: BacktestSettings
    buy_conditions: List[BacktestCondition]
    sell_conditions: List[BacktestCondition]

    # 통계 요약
    statistics: BacktestStatistics

    # 현재 포트폴리오
    current_holdings: List[PortfolioHolding] = Field(
        default_factory=list,
        description="현재 보유 종목 리스트"
    )

    # 일별 데이터
    daily_performance: List[DailyPerformance] = Field(
        default_factory=list,
        description="일별 성과 데이터"
    )

    # 월별 데이터
    monthly_performance: List[MonthlyPerformance] = Field(
        default_factory=list,
        description="월별 성과 데이터"
    )

    # 연도별 데이터
    yearly_performance: List[YearlyPerformance] = Field(
        default_factory=list,
        description="연도별 성과 데이터"
    )

    # 거래 내역
    trades: List[TradeRecord] = Field(
        default_factory=list,
        description="전체 거래 내역"
    )

    # 리밸런싱 이력
    rebalance_dates: List[date] = Field(
        default_factory=list,
        description="리밸런싱 실행 날짜"
    )

    # 차트 데이터 (프론트엔드 시각화용)
    chart_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="차트 시각화를 위한 데이터"
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class BacktestListItem(BaseModel):
    """백테스트 목록 아이템"""
    backtest_id: str
    backtest_name: str
    created_at: datetime
    status: str
    total_return: Optional[Decimal]
    max_drawdown: Optional[Decimal]
    sharpe_ratio: Optional[Decimal]
    start_date: Optional[date]
    end_date: Optional[date]


class BacktestListResponse(BaseModel):
    """백테스트 목록 응답"""
    items: List[BacktestListItem]
    total: int
    page: int
    page_size: int


class BacktestCreateRequest(BaseModel):
    """백테스트 생성 요청"""
    buy_conditions: List[BacktestCondition] = Field(..., description="매수 조건 목록")
    sell_conditions: List[BacktestCondition] = Field(..., description="매도 조건 목록")
    start_date: date = Field(..., description="백테스트 시작일")
    end_date: date = Field(..., description="백테스트 종료일")
    initial_capital: Decimal = Field(Decimal("100000000"), description="초기 자본금")
    rebalance_frequency: str = Field("MONTHLY", description="리밸런싱 주기")
    max_positions: int = Field(20, ge=1, le=100, description="최대 보유 종목 수")
    position_sizing: str = Field("EQUAL_WEIGHT", description="포지션 사이징 방법")
    benchmark: str = Field("KOSPI", description="벤치마크")
    commission_rate: float = Field(0.00015, ge=0, le=0.01, description="수수료율")
    slippage: float = Field(0.001, ge=0, le=0.1, description="슬리피지")


class FactorInfo(BaseModel):
    """팩터 정보"""
    code: str = Field(..., description="팩터 코드 (예: PER, ROE)")
    name: str = Field(..., description="팩터 이름")
    category: str = Field(..., description="팩터 카테고리")
    description: str = Field(..., description="팩터 설명")
    data_source: str = Field(..., description="데이터 출처")
    recommended_operator: str = Field(..., description="권장 연산자")
    typical_range: str = Field(..., description="일반적인 값 범위")


class FactorListResponse(BaseModel):
    """팩터 목록 응답"""
    factors: List[FactorInfo]
    total: int