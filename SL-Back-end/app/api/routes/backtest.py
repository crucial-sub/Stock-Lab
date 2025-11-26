"""
백테스트 API 라우터
- 백테스트 실행
- 결과 조회
- 상태 확인
"""
from fastapi import APIRouter, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import uuid
import logging
import asyncio

from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.simulation import (
    SimulationSession,
    PortfolioStrategy,
    StrategyFactor,
    TradingRule,
    SimulationStatistics,
    SimulationDailyValue,
    SimulationTrade,
    Factor
)
from app.models.backtest import BacktestSession
from app.models.company import Company
from app.models.user import User
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter()

THEME_DEFINITIONS = [
    {"id": 1, "name": "construction", "display_name": "건설"},
    {"id": 2, "name": "metal", "display_name": "금속"},
    {"id": 3, "name": "finance", "display_name": "금융"},
    {"id": 4, "name": "machinery", "display_name": "기계 / 장비"},
    {"id": 5, "name": "other_finance", "display_name": "기타 금융"},
    {"id": 6, "name": "other_manufacturing", "display_name": "기타 제조"},
    {"id": 7, "name": "other", "display_name": "기타"},
    {"id": 8, "name": "agriculture", "display_name": "농업 / 임업 / 어업"},
    {"id": 9, "name": "insurance", "display_name": "보험"},
    {"id": 10, "name": "real_estate", "display_name": "부동산"},
    {"id": 11, "name": "non_metal", "display_name": "비금속"},
    {"id": 12, "name": "textile", "display_name": "섬유 / 의류"},
    {"id": 13, "name": "entertainment", "display_name": "오락 / 문화"},
    {"id": 14, "name": "transport", "display_name": "운송 / 창고"},
    {"id": 15, "name": "transport_equipment", "display_name": "운송장비 / 부품"},
    {"id": 16, "name": "distribution", "display_name": "유통"},
    {"id": 17, "name": "bank", "display_name": "은행"},
    {"id": 18, "name": "food", "display_name": "음식료 / 담배"},
    {"id": 19, "name": "medical", "display_name": "의료 / 정밀기기"},
    {"id": 20, "name": "service", "display_name": "일반 서비스"},
    {"id": 21, "name": "utility", "display_name": "전기 / 가스 / 수도"},
    {"id": 22, "name": "electronics", "display_name": "전기 / 전자"},
    {"id": 23, "name": "pharma", "display_name": "제약"},
    {"id": 24, "name": "paper", "display_name": "종이 / 목재"},
    {"id": 25, "name": "securities", "display_name": "증권"},
    {"id": 26, "name": "publishing", "display_name": "출판 / 매체 복제"},
    {"id": 27, "name": "telecom", "display_name": "통신"},
    {"id": 28, "name": "chemical", "display_name": "화학"},
    {"id": 29, "name": "it_service", "display_name": "IT서비스"}
]

THEME_CODE_TO_INDUSTRY = {
    theme["name"]: theme["display_name"] for theme in THEME_DEFINITIONS
}

# Request/Response Models
class BuyCondition(BaseModel):
    """매수 조건"""
    name: str  # 조건식 이름 e.g. "A"
    exp_left_side: str  # 조건식 좌변 e.g. "이동평균({PER},{20일})"
    inequality: str  # 부등호 e.g. ">"
    exp_right_side: float  # 조건식 우변 e.g. 10


class TargetAndLoss(BaseModel):
    """목표가/손절가"""
    target_gain: Optional[float] = None
    stop_loss: Optional[float] = None


class HoldDays(BaseModel):
    """보유 기간"""
    min_hold_days: int
    max_hold_days: int
    sell_price_basis: str
    sell_price_offset: float


class ConditionSell(BaseModel):
    """조건 매도"""
    sell_conditions: List[Dict[str, Any]]  # 매도 조건식 리스트
    sell_logic: str
    sell_price_basis: str
    sell_price_offset: float


class TradeTargets(BaseModel):
    """매매 대상"""
    use_all_stocks: bool
    selected_universes: List[str] = []
    selected_themes: List[str] = []  # 산업명 리스트
    selected_stocks: List[str] = []  # 종목 코드 리스트
    selected_stock_count: Optional[int] = None  # UI 전용
    total_stock_count: Optional[int] = None  # UI 전용


class BacktestRequest(BaseModel):
    """백테스트 실행 요청 - 프론트엔드 스키마와 완전히 일치"""
    # 기본 설정
    strategy_name: str
    is_day_or_month: str  # "daily" or "monthly"
    start_date: str  # YYYYMMDD
    end_date: str  # YYYYMMDD
    initial_investment: float  # 만원 단위
    commission_rate: float  # %
    slippage: float  # 슬리피지 %

    # 매수 조건
    buy_conditions: List[BuyCondition]
    buy_logic: str
    priority_factor: str
    priority_order: str  # "asc" or "desc"
    per_stock_ratio: float  # %
    max_holdings: int
    max_buy_value: Optional[float] = None  # 만원 단위
    max_daily_stock: Optional[int] = None
    buy_price_basis: str  # 매수 가격 기준
    buy_price_offset: float  # 기준가 대비 증감값(%)

    # 매도 조건
    target_and_loss: Optional[TargetAndLoss] = None
    hold_days: Optional[HoldDays] = None
    condition_sell: Optional[ConditionSell] = None

    # 매매 대상
    trade_targets: TradeTargets

    # 공개 설정 (선택 사항)
    is_public: Optional[bool] = False
    is_anonymous: Optional[bool] = False
    hide_strategy_details: Optional[bool] = False


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    backtest_id: str = Field(..., serialization_alias="backtestId")
    status: str
    message: str
    created_at: datetime = Field(..., serialization_alias="createdAt")

    class Config:
        populate_by_name = True


class BacktestStatusResponse(BaseModel):
    """백테스트 상태 응답"""
    backtest_id: str = Field(..., serialization_alias="backtestId")
    status: str
    progress: int
    message: Optional[str] = None
    started_at: Optional[datetime] = Field(None, serialization_alias="startedAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")
    error_message: Optional[str] = Field(None, serialization_alias="errorMessage")
    # 백테스트 기간
    start_date: Optional[str] = Field(None, serialization_alias="startDate")
    end_date: Optional[str] = Field(None, serialization_alias="endDate")
    # 실시간 통계 (백테스트 진행 중에만 제공)
    current_date: Optional[str] = Field(None, serialization_alias="currentDate")
    buy_count: Optional[int] = Field(None, serialization_alias="buyCount")
    sell_count: Optional[int] = Field(None, serialization_alias="sellCount")
    current_return: Optional[float] = Field(None, serialization_alias="currentReturn")
    current_capital: Optional[float] = Field(None, serialization_alias="currentCapital")
    current_mdd: Optional[float] = Field(None, serialization_alias="currentMdd")
    # 차트 데이터 (진행 중에도 제공)
    yield_points: Optional[list] = Field(None, serialization_alias="yieldPoints")


class BacktestResultStatistics(BaseModel):
    """백테스트 결과 통계"""
    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: float = Field(..., serialization_alias="maxDrawdown")
    volatility: float = Field(..., serialization_alias="volatility")
    sharpe_ratio: float = Field(..., serialization_alias="sharpeRatio")
    win_rate: float = Field(..., serialization_alias="winRate")
    profit_factor: float = Field(..., serialization_alias="profitFactor")
    total_trades: int = Field(..., serialization_alias="totalTrades")
    winning_trades: int = Field(..., serialization_alias="winningTrades")
    losing_trades: int = Field(..., serialization_alias="losingTrades")
    initial_capital: float = Field(..., serialization_alias="initialCapital")
    final_capital: float = Field(..., serialization_alias="finalCapital")


class BacktestTrade(BaseModel):
    """백테스트 거래 내역"""
    stock_name: str = Field(..., serialization_alias="stockName")
    stock_code: str = Field(..., serialization_alias="stockCode")
    buy_price: float = Field(..., serialization_alias="buyPrice")
    sell_price: float = Field(..., serialization_alias="sellPrice")
    profit: float = Field(..., serialization_alias="profit")
    profit_rate: float = Field(..., serialization_alias="profitRate")
    holding_days: int = Field(..., serialization_alias="holdingDays")  # ✅ 보유기간 추가
    buy_date: str = Field(..., serialization_alias="buyDate")
    sell_date: str = Field(..., serialization_alias="sellDate")
    weight: float = Field(..., serialization_alias="weight")
    valuation: float = Field(..., serialization_alias="valuation")
    quantity: int = Field(..., serialization_alias="quantity")
    reason: Optional[str] = Field(None, serialization_alias="reason")  # ✅ 매매 사유 추가


class BacktestYieldPoint(BaseModel):
    """백테스트 일별 포트폴리오 데이터"""
    model_config = ConfigDict(populate_by_name=True)

    date: str
    portfolio_value: int = Field(..., serialization_alias="portfolioValue")  # 포트폴리오 총 가치
    cash: int  # 현금 잔고
    position_value: int = Field(..., serialization_alias="positionValue")  # 보유 포지션 가치
    daily_return: float = Field(..., serialization_alias="dailyReturn")  # 일간 수익률
    cumulative_return: float = Field(..., serialization_alias="cumulativeReturn")  # 누적 수익률
    value: float  # 차트용 (cumulative_return과 동일, 하위 호환성)
    daily_drawdown: float = Field(default=0, serialization_alias="dailyDrawdown")  # 일일 낙폭 (%)
    benchmark_return: float = Field(default=0, serialization_alias="benchmarkReturn")  # 벤치마크 일일 수익률 (%)
    benchmark_cum_return: float = Field(default=0, serialization_alias="benchmarkCumReturn")  # 벤치마크 누적 수익률 (%)
    buy_count: int = Field(default=0, serialization_alias="buyCount")  # 당일 매수 횟수
    sell_count: int = Field(default=0, serialization_alias="sellCount")  # 당일 매도 횟수


class UniverseStock(BaseModel):
    """유니버스 종목 정보"""
    stock_code: str = Field(..., serialization_alias="stockCode")
    stock_name: str = Field(..., serialization_alias="stockName")


class BacktestResultResponse(BaseModel):
    """백테스트 결과 응답"""
    id: str
    status: str
    statistics: BacktestResultStatistics
    trades: List[BacktestTrade]
    yield_points: List[BacktestYieldPoint] = Field(..., serialization_alias="yieldPoints")
    universe_stocks: List[UniverseStock] = Field(default_factory=list, serialization_alias="universeStocks")
    summary: Optional[str] = None
    created_at: datetime = Field(..., serialization_alias="createdAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")


class StrategyFactorSettings(BaseModel):
    """전략 팩터 설정"""
    factor_id: str = Field(..., serialization_alias="factorId")
    factor_name: str = Field(..., serialization_alias="factorName")
    usage_type: str = Field(..., serialization_alias="usageType")
    operator: Optional[str] = None
    threshold_value: Optional[float] = Field(None, serialization_alias="thresholdValue")
    weight: Optional[float] = None
    direction: Optional[str] = None


class TradingRuleSettings(BaseModel):
    """매매 규칙 설정"""
    rule_type: str = Field(..., serialization_alias="ruleType")
    rebalance_frequency: Optional[str] = Field(None, serialization_alias="rebalanceFrequency")
    rebalance_day: Optional[int] = Field(None, serialization_alias="rebalanceDay")
    position_sizing: Optional[str] = Field(None, serialization_alias="positionSizing")
    max_positions: Optional[int] = Field(None, serialization_alias="maxPositions")
    min_position_weight: Optional[float] = Field(None, serialization_alias="minPositionWeight")
    max_position_weight: Optional[float] = Field(None, serialization_alias="maxPositionWeight")
    stop_loss_pct: Optional[float] = Field(None, serialization_alias="stopLossPct")
    take_profit_pct: Optional[float] = Field(None, serialization_alias="takeProfitPct")
    commission_rate: Optional[float] = Field(None, serialization_alias="commissionRate")
    tax_rate: Optional[float] = Field(None, serialization_alias="taxRate")
    buy_condition: Optional[Dict[str, Any]] = Field(None, serialization_alias="buyCondition")
    sell_condition: Optional[Dict[str, Any]] = Field(None, serialization_alias="sellCondition")


class BacktestSettingsResponse(BaseModel):
    """백테스트 설정 응답"""
    session_name: Optional[str] = Field(None, serialization_alias="sessionName")
    start_date: str = Field(..., serialization_alias="startDate")
    end_date: str = Field(..., serialization_alias="endDate")
    initial_capital: float = Field(..., serialization_alias="initialCapital")
    benchmark: Optional[str] = None
    strategy_name: str = Field(..., serialization_alias="strategyName")
    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    strategy_description: Optional[str] = Field(None, serialization_alias="strategyDescription")
    universe_type: Optional[str] = Field(None, serialization_alias="universeType")
    market_cap_filter: Optional[str] = Field(None, serialization_alias="marketCapFilter")
    sector_filter: Optional[List[str]] = Field(None, serialization_alias="sectorFilter")
    factors: List[StrategyFactorSettings] = []
    trading_rules: List[TradingRuleSettings] = Field([], serialization_alias="tradingRules")


@router.post("/backtest/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 실행
    - 비동기로 백그라운드 실행
    - 세션 ID 즉시 반환
    - 🚀 PRODUCTION: 사용자당 동시 1개 백테스트 제한
    """
    try:
        # 🚀 PRODUCTION OPTIMIZATION: Rate Limiting (사용자당 동시 3개 백테스트)
        try:
            from app.core.cache import get_redis
            redis_client = get_redis()
            if redis_client:
                rate_limit_key = f"backtest:running:{current_user.user_id}"
                running_count = await redis_client.get(rate_limit_key)

                if running_count and int(running_count) >= 3:
                    raise HTTPException(
                        status_code=429,
                        detail="동시 실행 가능한 백테스트는 최대 3개입니다. 완료 후 다시 시도해주세요."
                    )

                # 실행 중인 백테스트 카운터 증가 (TTL: 1시간)
                current_count = int(running_count) if running_count else 0
                await redis_client.setex(rate_limit_key, 3600, current_count + 1)
                logger.info(f"🚦 Rate Limit 체크 통과: user_id={current_user.user_id}, 실행 중: {current_count + 1}/3")
        except HTTPException:
            # 429 에러는 그대로 전달
            raise
        except Exception as e:
            # Redis 에러는 무시하고 계속 진행 (Rate Limiting 없이)
            logger.warning(f"Rate Limiting 스킵 (Redis 에러): {e}")

        # 🚀 벡터화 평가 지원: 유명 전략 사용 시 DB에서 expression과 conditions 로드
        loaded_strategy_config = None
        if request.strategy_name:
            from sqlalchemy import text
            logger.info(f"🎯 전략 감지: {request.strategy_name}")

            # id 또는 name으로 조회 (한글/영문 모두 지원)
            result = await db.execute(
                text('SELECT backtest_config FROM investment_strategies WHERE id = :id OR name = :name'),
                {'id': request.strategy_name, 'name': request.strategy_name}
            )
            config = result.scalar_one_or_none()

            if config:
                # Case 1: expression과 conditions가 이미 있는 경우 (peter_lynch 형식)
                if 'expression' in config and 'conditions' in config:
                    loaded_strategy_config = {
                        'expression': config['expression'],
                        'conditions': config['conditions'],
                        'priority_factor': config.get('priority_factor', request.priority_factor),
                        'priority_order': config.get('priority_order', request.priority_order)
                    }
                    logger.info(f"✅ 벡터화 설정 로드: expression={loaded_strategy_config['expression']}, conditions={len(loaded_strategy_config['conditions'])}개")

                # Case 2: buy_conditions만 있는 경우 → 자동 변환
                elif 'buy_conditions' in config and config['buy_conditions']:
                    logger.info(f"🔄 buy_conditions → conditions 자동 변환 시작")

                    def convert_buy_conditions(buy_conditions: list) -> tuple:
                        """
                        buy_conditions 형식을 벡터화 평가용 conditions로 변환

                        입력 형식 (warren_buffett 등):
                        {"name": "A", "inequality": ">", "exp_left_side": "기본값({ROE})", "exp_right_side": 12}

                        출력 형식 (peter_lynch):
                        {"id": "A", "factor": "ROE", "operator": ">", "value": 12}
                        """
                        import re
                        conditions = []
                        condition_ids = []

                        for bc in buy_conditions:
                            # 팩터 추출: "기본값({ROE})" → "ROE"
                            exp_left = bc.get('exp_left_side', '')
                            factor_match = re.search(r'\{([A-Z_0-9]+)\}', exp_left)
                            if not factor_match:
                                logger.warning(f"⚠️ 팩터 추출 실패: {exp_left}")
                                continue

                            factor = factor_match.group(1)
                            condition_id = bc.get('name', f'C{len(conditions)}')
                            operator = bc.get('inequality', '>')
                            value = bc.get('exp_right_side', 0)

                            conditions.append({
                                'id': condition_id,
                                'factor': factor,
                                'operator': operator,
                                'value': value
                            })
                            condition_ids.append(condition_id)

                        # expression 생성: buy_logic에 따라 and/or 연결
                        buy_logic = config.get('buy_logic', 'and')
                        expression = f' {buy_logic} '.join(condition_ids)

                        return expression, conditions

                    expression, conditions = convert_buy_conditions(config['buy_conditions'])

                    if conditions:
                        loaded_strategy_config = {
                            'expression': expression,
                            'conditions': conditions,
                            'priority_factor': config.get('priority_factor', request.priority_factor),
                            'priority_order': config.get('priority_order', request.priority_order)
                        }
                        logger.info(f"✅ 자동 변환 완료: expression={expression}, conditions={len(conditions)}개")
                    else:
                        logger.warning(f"⚠️ 전략 '{request.strategy_name}' buy_conditions 변환 실패")
                else:
                    logger.warning(f"⚠️ 전략 '{request.strategy_name}' 설정에 expression/conditions/buy_conditions 없음")
            else:
                logger.warning(f"⚠️ 전략 '{request.strategy_name}'을 DB에서 찾을 수 없음")

        # 1. 세션 ID 생성
        session_id = str(uuid.uuid4())

        # 2. 날짜 파싱 (YYYYMMDD -> date)
        from datetime import datetime as dt
        logger.info(f"🔍 받은 날짜 - start_date: {request.start_date}, end_date: {request.end_date}")
        start_date = dt.strptime(request.start_date, "%Y%m%d").date()
        end_date = dt.strptime(request.end_date, "%Y%m%d").date()
        logger.info(f"🔍 파싱된 날짜 - start_date: {start_date}, end_date: {end_date}")

        # 3. 투자 금액 변환 (만원 -> 원)
        initial_capital = Decimal(str(request.initial_investment * 10000))

        # 4. 전략 생성
        strategy_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        strategy_name = f"{current_user.nickname}-{timestamp}"

        # 선택된 매매 대상 문자열 생성
        targets_str = "전체 종목" if request.trade_targets.use_all_stocks else f"{', '.join(request.trade_targets.selected_themes[:3])}{'...' if len(request.trade_targets.selected_themes) > 3 else ''}"

        strategy = PortfolioStrategy(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            description=f"User: {current_user.user_id}, Target: {targets_str}",
            strategy_type="FACTOR_BASED",
            universe_type="THEME",  # 테마 기반 선택
            initial_capital=initial_capital,
            user_id=str(current_user.user_id),
            is_public=request.is_public or False,
            is_anonymous=request.is_anonymous or False,
            hide_strategy_details=request.hide_strategy_details or False
        )
        db.add(strategy)

        # 5. 거래 규칙 생성 - 프론트엔드 설정 저장
        trading_rule = TradingRule(
            strategy_id=strategy_id,
            rule_type="CONDITION_BASED",
            rebalance_frequency=request.is_day_or_month.upper(),  # "DAILY" or "MONTHLY"
            max_positions=request.max_holdings,
            position_sizing="EQUAL_WEIGHT",  # per_stock_ratio 사용
            stop_loss_pct=Decimal(str(request.target_and_loss.stop_loss)) if request.target_and_loss and request.target_and_loss.stop_loss else None,
            commission_rate=Decimal(str(request.commission_rate / 100)),  # % -> decimal
            tax_rate=Decimal("0.0023"),  # 0.23% 거래세
            # 프론트엔드 조건식을 JSON으로 저장
            buy_condition={
                "conditions": [c.model_dump() for c in request.buy_conditions],
                "logic": request.buy_logic,
                "priority_factor": request.priority_factor,
                "priority_order": request.priority_order,
                "per_stock_ratio": request.per_stock_ratio,
                "max_buy_value": request.max_buy_value,
                "max_daily_stock": request.max_daily_stock,
                "buy_price_basis": request.buy_price_basis,
                "buy_price_offset": request.buy_price_offset,
                "trade_targets": request.trade_targets.model_dump()  # 매매 대상 저장
            },
            sell_condition={
                "target_and_loss": request.target_and_loss.model_dump() if request.target_and_loss else None,
                "hold_days": request.hold_days.model_dump() if request.hold_days else None,
                "condition_sell": request.condition_sell.model_dump() if request.condition_sell else None
            }
        )
        db.add(trading_rule)

        # 6. 매수 조건을 파싱하여 StrategyFactor로 저장
        import re
        for condition in request.buy_conditions:
            # BuyCondition 모델은 이미 분리된 필드를 가지고 있음
            # exp_left_side: 조건식 좌변 (e.g., "이동평균({PER},{20일})")
            # inequality: 부등호 (e.g., ">")
            # exp_right_side: 조건식 우변 (e.g., 10)
            expression_str = f"{condition.exp_left_side} {condition.inequality} {condition.exp_right_side}"

            # exp_left_side에서 팩터 이름 추출
            # 예: "이동평균({PER},{20일})" 또는 "{PER}" 또는 "{주가순자산률 (PBR)}"
            # 정규식으로 중괄호 안의 팩터 이름 추출
            match = re.search(r'\{([^}]+)\}', condition.exp_left_side)
            if match:
                full_factor_name = match.group(1)  # e.g., "주가순자산률 (PBR)" or "PER"
                operator = condition.inequality  # e.g., "<", ">", "=="
                threshold = str(condition.exp_right_side)  # e.g., "30"

                # 괄호 안의 영문 코드 추출 (예: "주가순자산률 (PBR)" -> "PBR")
                code_match = re.search(r'\(([A-Z_]+)\)', full_factor_name)
                if code_match:
                    factor_name = code_match.group(1)
                else:
                    # 괄호가 없으면 전체 이름 사용 (공백 제거)
                    factor_name = full_factor_name.strip()

                # Factor 테이블에서 factor_id 조회 (대소문자 구분 없이)
                factor_query = select(Factor).where(func.upper(Factor.factor_id) == factor_name.upper())
                factor_result = await db.execute(factor_query)
                factor = factor_result.scalar_one_or_none()

                if not factor:
                    # Factor가 없으면 생성 (기본 카테고리: VALUE)
                    factor = Factor(
                        factor_id=factor_name,
                        category_id="VALUE",  # 기본값: 가치 팩터 (대문자)
                        factor_name=factor_name,
                        calculation_type="FUNDAMENTAL",
                        description=f"Auto-created factor from user condition"
                    )
                    db.add(factor)
                    await db.flush()  # factor_id를 얻기 위해 flush

                # StrategyFactor 생성 (실제 DB의 factor_id 사용)
                strategy_factor = StrategyFactor(
                    strategy_id=strategy_id,
                    factor_id=factor.factor_id,  # 조회된 Factor 객체의 실제 ID 사용
                    usage_type="SCREENING",  # 스크리닝용
                    operator=operator.replace("<", "LT").replace(">", "GT").replace("==", "EQ"),
                    threshold_value=threshold,
                    weight=Decimal("1.0"),
                    direction="POSITIVE"
                )
                db.add(strategy_factor)

        # 우선순위 팩터도 추가 (정렬용)
        if request.priority_factor and request.priority_factor != "없음":
            # 중괄호 제거 및 팩터 코드 추출 (예: "{PER}" -> "PER", "{주가순자산률 (PBR)}" -> "PBR")
            import re
            priority_factor_name = request.priority_factor
            match = re.search(r'\{([^}]+)\}', priority_factor_name)
            if match:
                full_name = match.group(1)
                # 괄호 안의 영문 코드 추출
                code_match = re.search(r'\(([A-Z_]+)\)', full_name)
                if code_match:
                    priority_factor_name = code_match.group(1)
                else:
                    priority_factor_name = full_name.strip()

            logger.info(f"우선순위 팩터 파싱: 입력='{request.priority_factor}', 추출='{priority_factor_name}'")

            priority_factor_query = select(Factor).where(func.upper(Factor.factor_id) == priority_factor_name.upper())
            priority_factor_result = await db.execute(priority_factor_query)
            priority_factor = priority_factor_result.scalar_one_or_none()

            if priority_factor:
                # 기존 팩터 사용
                logger.info(f"기존 팩터 사용: {priority_factor.factor_id}")
                priority_strategy_factor = StrategyFactor(
                    strategy_id=strategy_id,
                    factor_id=priority_factor.factor_id,
                    usage_type="SCORING",
                    weight=Decimal("1.0"),
                    direction="POSITIVE" if request.priority_order == "desc" else "NEGATIVE"
                )
                db.add(priority_strategy_factor)
            else:
                logger.warning(f"우선순위 팩터 '{priority_factor_name}'가 DB에 없습니다. 무시합니다.")

        # 7. 세션 생성 (현재 로그인한 사용자 ID 사용)
        session = SimulationSession(
            session_id=session_id,
            strategy_id=strategy_id,
            user_id=current_user.user_id,  # 현재 로그인한 사용자 ID
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            benchmark="KOSPI",
            status="PENDING",
            progress=0,
            is_portfolio=True,  # 포트폴리오 목록에 표시되도록 설정
            created_at=datetime.now()
        )
        db.add(session)

        await db.commit()

        # 7. 백그라운드에서 백테스트 실행
        logger.info(f"백테스트 시작 - Session: {session_id}, Strategy: {request.strategy_name}")
        logger.info(f"Start date: {start_date}, End date: {end_date}, Initial capital: {initial_capital}")
        logger.info(f"Trade targets: {request.trade_targets.model_dump()}")

        # 매매 대상 결정:
        # 1. 유니버스가 선택되어 있으면 유니버스 사용 (use_all_stocks 무시)
        # 2. 유니버스가 없고 테마/종목이 선택되어 있으면 테마/종목 사용
        # 3. 아무것도 선택되지 않았거나 use_all_stocks이 true면 전체 종목 사용
        has_universe_selection = request.trade_targets.selected_universes and len(request.trade_targets.selected_universes) > 0
        has_theme_selection = request.trade_targets.selected_themes and len(request.trade_targets.selected_themes) > 0
        has_stock_selection = request.trade_targets.selected_stocks and len(request.trade_targets.selected_stocks) > 0

        if has_universe_selection:
            # 유니버스 선택이 있으면 유니버스 기반 필터링 (테마와 AND 결합 가능)
            target_universes = request.trade_targets.selected_universes
            # 테마도 함께 전달 (AND 필터링)
            selected_theme_codes = request.trade_targets.selected_themes if has_theme_selection else []
            target_themes = [
                THEME_CODE_TO_INDUSTRY.get(code, code) for code in selected_theme_codes
            ]
            target_stocks = request.trade_targets.selected_stocks if has_stock_selection else []
            logger.info(f"🎯 유니버스 & 테마 AND 필터링 모드: universes={target_universes}, themes={len(target_themes)}, stocks={len(target_stocks)}")
        elif has_theme_selection or has_stock_selection:
            # 테마/종목 선택이 있으면 테마/종목 기반 필터링
            selected_theme_codes = request.trade_targets.selected_themes
            target_themes = [
                THEME_CODE_TO_INDUSTRY.get(code, code) for code in selected_theme_codes
            ]
            target_stocks = request.trade_targets.selected_stocks
            target_universes = []
            logger.info(f"🎯 테마/종목 필터링 모드: themes={len(target_themes)}, stocks={len(target_stocks)}")
        else:
            # 아무것도 선택되지 않았으면 전체 종목 사용
            target_themes = []
            target_stocks = []
            target_universes = []
            logger.info(f"🎯 전체 종목 모드")

        asyncio.create_task(
            execute_backtest_wrapper(
                session_id,
                strategy_id,
                start_date,
                end_date,
                initial_capital,
                "KOSPI",
                target_themes,  # 선택된 테마(산업) 목록
                target_stocks,  # 선택된 개별 종목 코드 목록
                target_universes,  # 선택된 유니버스 목록
                request.trade_targets.use_all_stocks,  # 전체 종목 사용 여부
                loaded_strategy_config or [c.model_dump() for c in request.buy_conditions],  # 🚀 벡터화: 유명 전략이면 expression+conditions, 아니면 리스트
                request.buy_logic,
                request.priority_factor,
                request.priority_order,
                request.max_holdings,
                request.per_stock_ratio,
                request.is_day_or_month,
                request.commission_rate,
                request.slippage,
                request.target_and_loss.model_dump() if request.target_and_loss else None,
                request.hold_days.model_dump() if request.hold_days else None,
                request.condition_sell.model_dump() if request.condition_sell else None,
                request.max_buy_value,
                request.max_daily_stock,
                str(current_user.user_id)  # 🚀 PRODUCTION: Rate Limiting용 user_id
            )
        )

        return BacktestResponse(
            backtest_id=session_id,
            status="pending",
            message="백테스트가 시작되었습니다",
            created_at=datetime.now()
        )

    except HTTPException:
        # HTTPException은 그대로 전달 (429, 404 등)
        # 429 에러가 아닌 경우 Rate Limit 카운터 감소
        raise
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}", exc_info=True)
        
        # 🚀 Rate Limit 카운터 감소 (백테스트 시작 실패 시)
        try:
            from app.core.cache import get_redis
            redis_client = get_redis()
            if redis_client:
                rate_limit_key = f"backtest:running:{current_user.user_id}"
                running_count = await redis_client.get(rate_limit_key)
                if running_count:
                    new_count = max(0, int(running_count) - 1)
                    if new_count > 0:
                        await redis_client.setex(rate_limit_key, 3600, new_count)
                    else:
                        await redis_client.delete(rate_limit_key)
                    logger.info(f"🚦 Rate Limit 감소 (에러): user_id={current_user.user_id}, 남은 실행: {new_count}/3")
        except Exception as redis_error:
            logger.warning(f"Rate Limit 감소 실패 (무시): {redis_error}")
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{backtest_id}/status", response_model=BacktestStatusResponse)
async def get_backtest_status(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 상태 조회"""
    # BacktestSession 테이블에서 먼저 조회
    query = select(BacktestSession).where(BacktestSession.backtest_id == backtest_id)
    result = await db.execute(query)
    backtest_session = result.scalar_one_or_none()

    if backtest_session:
        # BacktestSession이 존재하면 완료된 것으로 간주
        # 스냅샷 및 거래 데이터 조회
        from app.models.backtest import BacktestDailySnapshot, BacktestTrade
        from collections import defaultdict

        yield_points_data = []

        # 스냅샷 조회
        snapshots_query = select(BacktestDailySnapshot).where(
            BacktestDailySnapshot.backtest_id == backtest_id
        ).order_by(BacktestDailySnapshot.snapshot_date)
        snapshots_result = await db.execute(snapshots_query)
        snapshots = snapshots_result.scalars().all()

        # 거래 내역 조회 (일별 매수/매도 횟수 계산용)
        trades_query = select(BacktestTrade).where(
            BacktestTrade.backtest_id == backtest_id
        ).order_by(BacktestTrade.trade_date)
        trades_result = await db.execute(trades_query)
        trades = trades_result.scalars().all()

        # 일별 거래 횟수 집계
        daily_trade_counts = defaultdict(lambda: {"buy": 0, "sell": 0})
        for trade in trades:
            trade_date = trade.trade_date.isoformat()
            if trade.trade_type == "BUY":
                daily_trade_counts[trade_date]["buy"] += 1
            elif trade.trade_type == "SELL":
                daily_trade_counts[trade_date]["sell"] += 1

        # yieldPoints 생성
        for snap in snapshots:
            date_str = snap.snapshot_date.isoformat()
            yield_points_data.append({
                "date": date_str,
                "value": float(snap.cumulative_return),
                "portfolioValue": int(snap.portfolio_value),
                "cash": int(snap.cash_balance),
                "positionValue": int(snap.invested_amount),
                "dailyReturn": float(snap.daily_return),
                "cumulativeReturn": float(snap.cumulative_return),
                "buyCount": daily_trade_counts[date_str]["buy"],
                "sellCount": daily_trade_counts[date_str]["sell"],
            })

        return BacktestStatusResponse(
            backtest_id=str(backtest_session.backtest_id),
            status="completed",
            progress=100,
            message="백테스트 완료",
            started_at=backtest_session.start_date,
            completed_at=backtest_session.end_date,
            error_message=None,
            start_date=backtest_session.start_date.strftime("%Y-%m-%d") if backtest_session.start_date else None,
            end_date=backtest_session.end_date.strftime("%Y-%m-%d") if backtest_session.end_date else None,
            yield_points=yield_points_data if yield_points_data else None
        )

    # 없으면 SimulationSession에서 조회 (실행 중인 경우)
    query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # ⚡ Redis 제거: DB에서 직접 진행률 조회 (asyncio 충돌 방지)
    # 백테스트가 매 거래일마다 DB에 commit하므로 실시간 조회 가능

    # 실행 중인 백테스트의 실시간 yield_points 조회
    yield_points_data = []
    if session.status in ["RUNNING", "COMPLETED"]:
        # SimulationDailyValue와 SimulationTrade 조회
        from collections import defaultdict

        # 일별 데이터 조회
        daily_values_query = select(SimulationDailyValue).where(
            SimulationDailyValue.session_id == backtest_id
        ).order_by(SimulationDailyValue.date)
        daily_values_result = await db.execute(daily_values_query)
        daily_values = daily_values_result.scalars().all()

        logger.info(f"📊 실시간 yield_points 조회 - session_id: {backtest_id}, status: {session.status}, daily_values 개수: {len(daily_values)}")

        # 거래 내역 조회 (일별 매수/매도 횟수 계산용)
        trades_query = select(SimulationTrade).where(
            SimulationTrade.session_id == backtest_id
        ).order_by(SimulationTrade.trade_date)
        trades_result = await db.execute(trades_query)
        trades = trades_result.scalars().all()

        # 일별 거래 횟수 집계
        daily_trade_counts = defaultdict(lambda: {"buy": 0, "sell": 0})
        for trade in trades:
            trade_date = trade.trade_date.isoformat()
            if trade.trade_type == "BUY":
                daily_trade_counts[trade_date]["buy"] += 1
            elif trade.trade_type == "SELL":
                daily_trade_counts[trade_date]["sell"] += 1

        # yieldPoints 생성
        for dv in daily_values:
            date_str = dv.date.isoformat()
            yield_points_data.append({
                "date": date_str,
                "value": float(dv.cumulative_return) if dv.cumulative_return else 0,
                "portfolioValue": int(dv.portfolio_value) if dv.portfolio_value else 0,
                "cash": int(dv.cash) if dv.cash else 0,
                "positionValue": int(dv.position_value) if dv.position_value else 0,
                "dailyReturn": float(dv.daily_return) if dv.daily_return else 0,
                "cumulativeReturn": float(dv.cumulative_return) if dv.cumulative_return else 0,
                "buyCount": daily_trade_counts[date_str]["buy"],
                "sellCount": daily_trade_counts[date_str]["sell"],
            })

    # ⚡ DB에서 직접 실시간 진행률 조회 (매 거래일마다 commit됨)
    progress = session.progress or 0
    current_date_str = session.current_date.isoformat() if session.current_date else None
    buy_count = session.buy_count or 0
    sell_count = session.sell_count or 0
    current_return = float(session.current_return) if session.current_return else None
    current_capital = float(session.current_capital) if session.current_capital else None
    current_mdd = float(session.current_mdd) if session.current_mdd else None

    return BacktestStatusResponse(
        backtest_id=session.session_id,
        status=session.status.lower() if session.status else "pending",
        progress=progress,
        message=f"진행률: {progress}%",
        started_at=session.started_at,
        completed_at=session.completed_at,
        error_message=session.error_message,
        start_date=session.start_date.strftime("%Y-%m-%d") if session.start_date else None,
        end_date=session.end_date.strftime("%Y-%m-%d") if session.end_date else None,
        current_date=current_date_str,
        buy_count=buy_count,
        sell_count=sell_count,
        current_return=float(session.current_return) if session.current_return else None,
        current_capital=float(session.current_capital) if session.current_capital else None,
        current_mdd=float(session.current_mdd) if session.current_mdd else None,
        yield_points=yield_points_data if yield_points_data else None
    )


async def _get_new_backtest_result(db: AsyncSession, backtest_id: str, session: BacktestSession):
    """BacktestSession 테이블에서 백테스트 결과 조회"""
    from app.models.backtest import BacktestStatistics as NewBacktestStatistics, BacktestDailySnapshot, BacktestTrade as NewBacktestTrade

    # 통계 조회
    stats_query = select(NewBacktestStatistics).where(NewBacktestStatistics.backtest_id == backtest_id)
    stats_result = await db.execute(stats_query)
    stats = stats_result.scalar_one_or_none()

    if not stats:
        raise HTTPException(status_code=404, detail="백테스트 통계를 찾을 수 없습니다")

    # 거래 내역 조회
    trades_query = select(NewBacktestTrade).where(NewBacktestTrade.backtest_id == backtest_id).order_by(NewBacktestTrade.trade_date)
    trades_result = await db.execute(trades_query)
    trades = trades_result.scalars().all()

    # 일별 스냅샷 조회
    snapshots_query = select(BacktestDailySnapshot).where(BacktestDailySnapshot.backtest_id == backtest_id).order_by(BacktestDailySnapshot.snapshot_date)
    snapshots_result = await db.execute(snapshots_query)
    snapshots = snapshots_result.scalars().all()

    # BUY 거래를 종목별로 정리 (FIFO 방식)
    buy_trades_by_stock = {}
    for trade in trades:
        if trade.trade_type == "BUY":
            if trade.stock_code not in buy_trades_by_stock:
                buy_trades_by_stock[trade.stock_code] = []
            buy_trades_by_stock[trade.stock_code].append(trade)

    # 거래 내역 변환 (SELL 거래만)
    trade_list = []
    for trade in trades:
        if trade.trade_type == "SELL":
            # 해당 종목의 BUY 거래 큐에서 가장 오래된 것(첫 번째) 가져오기 (FIFO)
            buy_trades = buy_trades_by_stock.get(trade.stock_code, [])
            buy_trade = buy_trades.pop(0) if buy_trades else None

            # amount와 initial_capital이 None일 수 있으므로 안전하게 처리
            amount = float(trade.amount) if trade.amount else 0
            initial_capital = float(session.initial_capital) if session.initial_capital else 1

            # 보유 기간 계산 (영업일 기준)
            holding_days = 0
            if buy_trade:
                holding_days = (trade.trade_date - buy_trade.trade_date).days

            trade_list.append(BacktestTrade(
                stock_name=trade.stock_name,  # 이미 테이블에 저장되어 있음
                stock_code=trade.stock_code,
                buy_price=float(buy_trade.price) if buy_trade else 0,
                sell_price=float(trade.price),
                profit=float(trade.profit) if trade.profit else 0,
                profit_rate=float(trade.profit_rate) if trade.profit_rate else 0,
                holding_days=holding_days,
                buy_date=buy_trade.trade_date.isoformat() if buy_trade else "",
                sell_date=trade.trade_date.isoformat(),
                weight=float(amount / initial_capital * 100) if initial_capital > 0 else 0,
                valuation=int(amount),  # 소수점 제거
                quantity=int(trade.quantity) if trade.quantity else 0,
                reason=trade.selection_reason if trade.selection_reason else "매도"  # ✅ selection_reason 필드 사용
            ))

    # 일별 매수/매도 횟수 집계
    from collections import defaultdict
    daily_trade_counts = defaultdict(lambda: {"buy": 0, "sell": 0})

    for trade in trades:
        trade_date = trade.trade_date.isoformat()
        if trade.trade_type == "BUY":
            daily_trade_counts[trade_date]["buy"] += 1
        elif trade.trade_type == "SELL":
            daily_trade_counts[trade_date]["sell"] += 1

    # 벤치마크 누적 수익률 계산 (일일 수익률을 누적)
    benchmark_cum_returns = []
    cumulative_benchmark = 0.0
    for snap in snapshots:
        daily_benchmark = float(snap.benchmark_return) if snap.benchmark_return else 0
        # 단순 누적 (복리 고려 시: (1 + cumulative/100) * (1 + daily/100) - 1)
        cumulative_benchmark += daily_benchmark
        benchmark_cum_returns.append(cumulative_benchmark)

    # 수익률 포인트 변환 (매수/매도 횟수 + 벤치마크 데이터 포함)
    yield_points = [
        {
            "date": snap.snapshot_date.isoformat(),
            "portfolio_value": int(snap.portfolio_value),
            "cash": int(snap.cash_balance),
            "position_value": int(snap.invested_amount),
            "daily_return": float(snap.daily_return),
            "cumulative_return": float(snap.cumulative_return),
            "value": float(snap.cumulative_return),
            "daily_drawdown": float(snap.drawdown) if hasattr(snap, 'drawdown') and snap.drawdown else 0,
            "benchmark_return": float(snap.benchmark_return) if snap.benchmark_return else 0,
            "benchmark_cum_return": benchmark_cum_returns[idx],
            "buy_count": daily_trade_counts[snap.snapshot_date.isoformat()]["buy"],
            "sell_count": daily_trade_counts[snap.snapshot_date.isoformat()]["sell"]
        }
        for idx, snap in enumerate(snapshots)
    ]

    # 유니버스 종목 조회 (BacktestSession에는 strategy_id가 없으므로 거래 종목에서 추론)
    universe_stocks_list = []
    try:
        from app.models.company import Company

        universe_stock_codes = set()

        # 거래된 종목들의 industry를 조회해서 해당 industry의 모든 종목을 유니버스로 사용
        if trade_list:
            print(f"📊 [BacktestSession] 거래 종목에서 산업 추론 중...")
            traded_stock_codes = list(set([t.stock_code for t in trade_list]))
            print(f"📊 [BacktestSession] 거래된 종목: {traded_stock_codes}")

            # 거래된 종목들의 industry 조회
            traded_industries_query = select(Company.industry).where(
                Company.stock_code.in_(traded_stock_codes)
            ).distinct()
            traded_industries_result = await db.execute(traded_industries_query)
            traded_industries = [row.industry for row in traded_industries_result.all() if row.industry]

            if traded_industries:
                print(f"📊 [BacktestSession] 추론된 산업: {traded_industries}")
                # 해당 산업의 모든 종목 조회
                industry_companies_query = select(Company.stock_code).where(
                    Company.industry.in_(traded_industries)
                )
                industry_companies_result = await db.execute(industry_companies_query)
                industry_stock_codes = [row.stock_code for row in industry_companies_result.all()]
                print(f"✅ [BacktestSession] 산업별 종목 {len(industry_stock_codes)}개 발견")
                universe_stock_codes.update(industry_stock_codes)

        if universe_stock_codes:
            universe_companies_query = select(Company.stock_code, Company.company_name).where(
                Company.stock_code.in_(list(universe_stock_codes))
            )
            universe_companies_result = await db.execute(universe_companies_query)
            universe_companies_rows = universe_companies_result.all()

            universe_stocks_list = [
                UniverseStock(
                    stock_code=row.stock_code,
                    stock_name=row.company_name
                )
                for row in universe_companies_rows
            ]
            print(f"✅ [BacktestSession] 유니버스 종목 {len(universe_stocks_list)}개 로드됨")
        else:
            print(f"⚠️  [BacktestSession] 유니버스 종목을 찾을 수 없습니다")
    except Exception as e:
        print(f"⚠️  [BacktestSession] Failed to load universe stocks: {e}")
        import traceback
        traceback.print_exc()

    return BacktestResultResponse(
        id=str(session.backtest_id),
        status="completed",
        statistics=BacktestResultStatistics(
            total_return=float(stats.total_return),
            annualized_return=float(stats.annualized_return),
            max_drawdown=float(stats.max_drawdown),
            volatility=float(stats.volatility),
            sharpe_ratio=float(stats.sharpe_ratio),
            win_rate=float(stats.win_rate),
            profit_factor=float(stats.profit_loss_ratio) if stats.profit_loss_ratio else 0,
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            losing_trades=stats.losing_trades,
            initial_capital=float(stats.initial_capital),
            final_capital=float(stats.final_capital)
        ),
        trades=trade_list,
        yield_points=yield_points,
        universe_stocks=universe_stocks_list,
        summary=None,
        created_at=session.created_at,
        completed_at=session.completed_at  # completed_at 사용 (updated_at 없음)
    )


@router.get("/backtest/{backtest_id}/result", response_model=BacktestResultResponse)
async def get_backtest_result(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 결과 조회"""
    # SimulationSession을 먼저 확인 (trade_targets 정보가 있음)
    session_query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    # SimulationSession이 있으면 이쪽 로직 사용 (trade_targets 활용)
    if session:
        # SimulationSession 로직으로 처리
        pass  # 아래 기존 로직 계속 진행
    else:
        # SimulationSession이 없으면 BacktestSession 확인
        from app.models.backtest import BacktestStatistics as NewBacktestStatistics, BacktestDailySnapshot, BacktestTrade as NewBacktestTrade

        backtest_query = select(BacktestSession).where(BacktestSession.backtest_id == backtest_id)
        backtest_result = await db.execute(backtest_query)
        backtest_session = backtest_result.scalar_one_or_none()

        if backtest_session:
            # BacktestSession 결과 처리 (구 방식)
            return await _get_new_backtest_result(db, backtest_id, backtest_session)

        # 둘 다 없으면 404
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # === 아래부터 SimulationSession 로직 ===

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    if session.status != "COMPLETED":
        return BacktestResultResponse(
            id=backtest_id,
            status=session.status.lower() if session.status else "pending",
            statistics=BacktestResultStatistics(
                total_return=0,
                annualized_return=0,
                max_drawdown=0,
                volatility=0,
                sharpe_ratio=0,
                win_rate=0,
                profit_factor=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                initial_capital=float(session.initial_capital),
                final_capital=float(session.initial_capital)
            ),
            trades=[],
            yield_points=[],
            summary=None,
            created_at=session.created_at,
            completed_at=session.completed_at
        )

    # 2. 통계 조회
    stats_query = select(SimulationStatistics).where(SimulationStatistics.session_id == backtest_id)
    stats_result = await db.execute(stats_query)
    stats = stats_result.scalar_one_or_none()

    if not stats:
        raise HTTPException(status_code=404, detail="백테스트 통계를 찾을 수 없습니다")

    # 3. 거래 내역 조회 (전체 조회 - FIFO 매칭을 위해 시간순 정렬)
    trades_query = (
        select(SimulationTrade)
        .where(SimulationTrade.session_id == backtest_id)
        .order_by(SimulationTrade.trade_date.asc(), SimulationTrade.trade_id.asc())
    )
    trades_result = await db.execute(trades_query)
    trades = trades_result.scalars().all()

    # 4. 일별 수익률 조회
    daily_query = (
        select(SimulationDailyValue)
        .where(SimulationDailyValue.session_id == backtest_id)
        .order_by(SimulationDailyValue.date)
    )
    daily_result = await db.execute(daily_query)
    daily_values = daily_result.scalars().all()

    # 🐛 DEBUG: Log daily values count
    logger.info(f"🔍 Daily values query for session_id='{backtest_id}': found {len(daily_values)} records")
    if len(daily_values) == 0:
        # Try to query all sessions to see what exists
        all_sessions_query = select(SimulationDailyValue.session_id).distinct()
        all_sessions_result = await db.execute(all_sessions_query)
        all_session_ids = [row[0] for row in all_sessions_result.all()]
        logger.warning(f"⚠️ No daily values found for session_id='{backtest_id}'. All session_ids in DB: {all_session_ids[:10]}")

    # 5. 종목 코드 목록 추출 및 종목명 조회
    stock_codes = list(set([trade.stock_code for trade in trades]))
    companies_query = select(Company.stock_code, Company.company_name).where(Company.stock_code.in_(stock_codes))
    companies_result = await db.execute(companies_query)
    companies_rows = companies_result.all()

    # 종목 코드 → 종목명 매핑
    stock_name_map = {row.stock_code: row.company_name for row in companies_rows}

    # 6. 데이터 변환 - 매수/매도 거래를 매칭 (FIFO: 시간순으로 매칭)
    trade_list = []
    buy_trades_by_stock = {}  # {stock_code: [list of BUY trades]}

    # 먼저 모든 BUY 거래를 종목별로 수집 (시간순)
    for trade in trades:
        if trade.trade_type == "BUY":
            if trade.stock_code not in buy_trades_by_stock:
                buy_trades_by_stock[trade.stock_code] = []
            buy_trades_by_stock[trade.stock_code].append(trade)

    # SELL 거래를 처리하며 대응하는 BUY 거래 찾기 (FIFO)
    for trade in trades:
        if trade.trade_type == "SELL" and trade.realized_pnl is not None:
            # 해당 종목의 BUY 거래 큐에서 가장 오래된 것(첫 번째) 가져오기
            buy_trades = buy_trades_by_stock.get(trade.stock_code, [])
            buy_trade = buy_trades.pop(0) if buy_trades else None

            # amount와 initial_capital이 None일 수 있으므로 안전하게 처리
            amount = float(trade.amount) if trade.amount else 0
            initial_capital = float(session.initial_capital) if session.initial_capital else 1

            trade_list.append(BacktestTrade(
                stock_name=stock_name_map.get(trade.stock_code, trade.stock_code),
                stock_code=trade.stock_code,
                buy_price=float(buy_trade.price) if buy_trade else 0,
                sell_price=float(trade.price),
                profit=float(trade.realized_pnl),
                profit_rate=float(trade.return_pct) if trade.return_pct else 0,
                holding_days=trade.holding_days if trade.holding_days else 0,  # ✅ 보유기간 추가
                buy_date=buy_trade.trade_date.isoformat() if buy_trade else "",
                sell_date=trade.trade_date.isoformat(),
                weight=float(amount / initial_capital * 100) if initial_capital > 0 else 0,
                valuation=amount,
                quantity=int(trade.quantity) if trade.quantity else 0,
                reason=trade.reason if trade.reason else "매도"  # ✅ 매도 사유 추가
            ))

    yield_points = [
        BacktestYieldPoint(
            date=dv.date.isoformat(),
            portfolio_value=int(dv.portfolio_value) if dv.portfolio_value else 0,
            cash=int(dv.cash) if dv.cash else 0,
            position_value=int(dv.position_value) if dv.position_value else 0,
            daily_return=float(dv.daily_return) if dv.daily_return else 0,
            cumulative_return=float(dv.cumulative_return) if dv.cumulative_return else 0,
            value=float(dv.cumulative_return) if dv.cumulative_return else 0,  # 차트용 (하위 호환성)
            daily_drawdown=float(dv.daily_drawdown) if dv.daily_drawdown else 0,  # 일일 낙폭
            benchmark_return=float(dv.benchmark_return) if dv.benchmark_return else 0,  # 벤치마크 일일 수익률
            benchmark_cum_return=float(dv.benchmark_cum_return) if dv.benchmark_cum_return else 0  # 벤치마크 누적 수익률
        )
        for dv in daily_values
    ]

    # 7. 유니버스 종목 조회 (TradingRule의 trade_targets 기반)
    universe_stocks_list = []
    try:
        # TradingRule에서 trade_targets 조회
        from app.models.simulation import TradingRule
        trading_rule_query = select(TradingRule).where(TradingRule.strategy_id == session.strategy_id)
        trading_rule_result = await db.execute(trading_rule_query)
        trading_rule = trading_rule_result.scalar_one_or_none()

        universe_stock_codes = set()  # 중복 제거를 위해 set 사용

        if trading_rule and trading_rule.buy_condition:
            trade_targets = trading_rule.buy_condition.get("trade_targets", {})

            # 개별 종목 코드 추출
            selected_stocks = trade_targets.get("selected_stocks", [])

            # 선택된 유니버스 추출
            selected_universes = trade_targets.get("selected_universes", [])

            # 선택된 테마에서 종목 조회
            selected_themes = trade_targets.get("selected_themes", [])

            universe_stock_codes.update(selected_stocks)

            # 🎯 유니버스가 선택되었으면 유니버스 기반으로만 종목 조회 (테마 무시)
            if selected_universes:
                from app.services.universe_service import UniverseService
                universe_service = UniverseService(db)

                # 백테스트 시작일을 기준으로 유니버스 종목 조회
                backtest_start_date = session.start_date.strftime("%Y%m%d") if session.start_date else None
                if backtest_start_date:
                    universe_stock_codes_list = await universe_service.get_stock_codes_by_universes(
                        selected_universes,
                        trade_date=backtest_start_date
                    )
                    universe_stock_codes.update(universe_stock_codes_list)
                    print(f"📊 유니버스 필터링 결과: {len(universe_stock_codes)}개 종목 (유니버스: {selected_universes})")
                else:
                    print(f"⚠️  백테스트 시작일이 없어 유니버스 조회 불가")
            # 테마가 선택되었으면 해당 테마의 모든 종목 조회 (유니버스가 없을 때만)
            elif selected_themes:
                print(f"📊 선택된 테마: {selected_themes}")
                # Company 테이블에서 industry가 선택된 테마에 포함된 종목 조회
                theme_companies_query = select(Company.stock_code).where(
                    Company.industry.in_(selected_themes)
                )
                theme_companies_result = await db.execute(theme_companies_query)
                theme_stock_codes = [row.stock_code for row in theme_companies_result.all()]
                print(f"✅ 테마 종목 {len(theme_stock_codes)}개 발견")
                universe_stock_codes.update(theme_stock_codes)
            # 전체 종목 사용 여부 확인 (유니버스와 테마가 모두 없을 때만)
            else:
                use_all_stocks = trade_targets.get("use_all_stocks", False)
                if use_all_stocks:
                    print(f"📊 전체 종목 사용 모드")
                    all_companies_query = select(Company.stock_code)
                    all_companies_result = await db.execute(all_companies_query)
                    all_stock_codes = [row.stock_code for row in all_companies_result.all()]
                    universe_stock_codes.update(all_stock_codes)

        # Fallback: trade_targets가 없는 경우 (기존 백테스트)
        # ⚠️ 주의: 거래가 없으면 유니버스를 표시할 수 없음
        if not universe_stock_codes:
            print(f"⚠️  trade_targets 없음 - 유니버스를 표시할 수 없습니다")
            # 거래 내역에서 역추론하지 않음 - 실제 유니버스와 다를 수 있기 때문

        # 종목 코드 리스트가 있으면 Company 테이블에서 종목명 조회
        if universe_stock_codes:
            universe_companies_query = select(Company.stock_code, Company.company_name).where(
                Company.stock_code.in_(list(universe_stock_codes))
            )
            universe_companies_result = await db.execute(universe_companies_query)
            universe_companies_rows = universe_companies_result.all()

            universe_stocks_list = [
                UniverseStock(
                    stock_code=row.stock_code,
                    stock_name=row.company_name
                )
                for row in universe_companies_rows
            ]
            print(f"✅ 유니버스 종목 {len(universe_stocks_list)}개 로드됨")
        else:
            print(f"⚠️  유니버스 종목을 찾을 수 없습니다")
    except Exception as e:
        # 유니버스 조회 실패 시 빈 리스트 반환 (백테스트 결과는 정상 반환)
        print(f"Warning: Failed to load universe stocks: {e}")
        import traceback
        traceback.print_exc()

    return BacktestResultResponse(
        id=backtest_id,
        status="completed",
        statistics=BacktestResultStatistics(
            total_return=float(stats.total_return) if stats.total_return is not None else 0,
            annualized_return=float(stats.annualized_return) if stats.annualized_return is not None else 0,
            max_drawdown=float(stats.max_drawdown) if stats.max_drawdown is not None else 0,
            volatility=float(stats.volatility) if stats.volatility is not None else 0,
            sharpe_ratio=float(stats.sharpe_ratio) if stats.sharpe_ratio is not None else 0,
            win_rate=float(stats.win_rate) if stats.win_rate is not None else 0,
            profit_factor=float(stats.profit_factor) if stats.profit_factor else 0,
            total_trades=stats.total_trades or 0,
            winning_trades=stats.winning_trades or 0,
            losing_trades=stats.losing_trades or 0,
            initial_capital=int(session.initial_capital) if session.initial_capital is not None else 0,
            final_capital=int(stats.final_capital) if stats.final_capital is not None else 0
        ),
        trades=trade_list,
        yield_points=yield_points,
        universe_stocks=universe_stocks_list,
        summary=session.description if session.description else None,
        created_at=session.created_at,
        completed_at=session.completed_at
    )


@router.get("/backtest/{backtest_id}/trades")
async def get_backtest_trades(
    backtest_id: str,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 매매 내역 조회 (페이지네이션)
    프론트엔드 무한 스크롤용
    """
    # 1. 세션 확인
    session_query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # 2. 모든 거래를 시간순으로 조회 (FIFO 매칭용)
    all_trades_query = (
        select(SimulationTrade)
        .where(SimulationTrade.session_id == backtest_id)
        .order_by(SimulationTrade.trade_date.asc(), SimulationTrade.trade_id.asc())
    )
    all_trades_result = await db.execute(all_trades_query)
    all_trades = all_trades_result.scalars().all()

    # BUY 거래를 종목 코드별로 리스트로 매핑 (FIFO)
    buy_trades_by_stock = {}  # {stock_code: [list of BUY trades]}
    sell_trades_list = []  # matched SELL trades

    for trade in all_trades:
        if trade.trade_type == "BUY":
            if trade.stock_code not in buy_trades_by_stock:
                buy_trades_by_stock[trade.stock_code] = []
            buy_trades_by_stock[trade.stock_code].append(trade)
        elif trade.trade_type == "SELL" and trade.realized_pnl is not None:
            # FIFO: 가장 오래된 BUY 거래와 매칭
            buy_trades = buy_trades_by_stock.get(trade.stock_code, [])
            buy_trade = buy_trades.pop(0) if buy_trades else None
            sell_trades_list.append((trade, buy_trade))

    # 3. 페이지네이션 적용 (SELL 거래 기준)
    total_count = len(sell_trades_list)
    offset = (page - 1) * limit
    paginated_trades = sell_trades_list[offset:offset + limit]

    # 4. 종목 코드 목록 추출 및 종목명 조회
    stock_codes = list(set([sell_trade.stock_code for sell_trade, _ in paginated_trades]))
    companies_query = select(Company.stock_code, Company.company_name).where(Company.stock_code.in_(stock_codes))
    companies_result = await db.execute(companies_query)
    companies_rows = companies_result.all()

    # 종목 코드 → 종목명 매핑
    stock_name_map = {row.stock_code: row.company_name for row in companies_rows}

    # 5. 데이터 변환
    trade_list = []
    for sell_trade, buy_trade in paginated_trades:
        trade_list.append({
            "stockName": stock_name_map.get(sell_trade.stock_code, sell_trade.stock_code),
            "stockCode": sell_trade.stock_code,
            "quantity": sell_trade.quantity,  # ✅ 수량 추가
            "buyPrice": float(buy_trade.price) if buy_trade else 0.0,
            "sellPrice": float(sell_trade.price),
            "profit": float(sell_trade.realized_pnl),
            "profitRate": float(sell_trade.return_pct) if sell_trade.return_pct else 0.0,
            "holdingDays": sell_trade.holding_days if sell_trade.holding_days else 0,  # ✅ 보유기간 추가
            "buyDate": buy_trade.trade_date.isoformat() if buy_trade else "",
            "sellDate": sell_trade.trade_date.isoformat(),
            "weight": float(sell_trade.amount / session.initial_capital * 100) if session.initial_capital else 0.0,
            "valuation": float(sell_trade.amount)
        })

    return {
        "data": trade_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "total_pages": (total_count + limit - 1) // limit
        }
    }


@router.get("/backtest/{backtest_id}/settings", response_model=BacktestSettingsResponse)
async def get_backtest_settings(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 설정 조회"""
    # 1. 세션 조회
    session_query = (
        select(SimulationSession)
        .where(SimulationSession.session_id == backtest_id)
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # 2. 전략 조회
    strategy_query = select(PortfolioStrategy).where(PortfolioStrategy.strategy_id == session.strategy_id)
    strategy_result = await db.execute(strategy_query)
    strategy = strategy_result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")

    # 3. 팩터 설정 조회 (Factor 테이블 JOIN 제거)
    factors_query = (
        select(StrategyFactor)
        .where(StrategyFactor.strategy_id == session.strategy_id)
        .order_by(StrategyFactor.id)
    )
    factors_result = await db.execute(factors_query)
    factors_rows = factors_result.scalars().all()

    factors_list = [
        StrategyFactorSettings(
            factor_id=sf.factor_id,
            factor_name=sf.factor_id,  # factor_id를 factor_name으로 사용
            usage_type=sf.usage_type,
            operator=sf.operator,
            threshold_value=float(sf.threshold_value) if sf.threshold_value else None,
            weight=float(sf.weight) if sf.weight else None,
            direction=sf.direction
        )
        for sf in factors_rows
    ]

    # 4. 매매 규칙 조회
    rules_query = (
        select(TradingRule)
        .where(TradingRule.strategy_id == session.strategy_id)
        .order_by(TradingRule.rule_id)
    )
    rules_result = await db.execute(rules_query)
    rules = rules_result.scalars().all()

    trading_rules_list = [
        TradingRuleSettings(
            rule_type=rule.rule_type,
            rebalance_frequency=rule.rebalance_frequency,
            rebalance_day=rule.rebalance_day,
            position_sizing=rule.position_sizing,
            max_positions=rule.max_positions,
            min_position_weight=float(rule.min_position_weight) if rule.min_position_weight else None,
            max_position_weight=float(rule.max_position_weight) if rule.max_position_weight else None,
            stop_loss_pct=float(rule.stop_loss_pct) if rule.stop_loss_pct else None,
            take_profit_pct=float(rule.take_profit_pct) if rule.take_profit_pct else None,
            commission_rate=float(rule.commission_rate) if rule.commission_rate else None,
            tax_rate=float(rule.tax_rate) if rule.tax_rate else None,
            buy_condition=rule.buy_condition,
            sell_condition=rule.sell_condition
        )
        for rule in rules
    ]

    # 5. sector_filter 파싱 (JSON -> List[str])
    sector_filter = None
    if strategy.sector_filter:
        if isinstance(strategy.sector_filter, list):
            sector_filter = strategy.sector_filter
        elif isinstance(strategy.sector_filter, dict):
            sector_filter = list(strategy.sector_filter.keys())

    # 6. 응답 생성
    return BacktestSettingsResponse(
        session_name=session.session_name,
        start_date=session.start_date.isoformat(),
        end_date=session.end_date.isoformat(),
        initial_capital=float(session.initial_capital),
        benchmark=session.benchmark,
        strategy_name=strategy.strategy_name,
        strategy_type=strategy.strategy_type,
        strategy_description=strategy.description,
        universe_type=strategy.universe_type,
        market_cap_filter=strategy.market_cap_filter,
        sector_filter=sector_filter,
        factors=factors_list,
        trading_rules=trading_rules_list
    )


@router.get("/backtest/list")
async def list_backtests(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    로그인된 사용자의 백테스트(전략) 목록 조회
    - JWT 토큰으로 인증된 사용자의 portfolio_strategies만 조회
    - 페이지네이션 지원
    """
    try:
        # 1. 사용자의 전략 조회 (portfolio_strategies 테이블 기준)
        strategies_query = (
            select(PortfolioStrategy)
            .where(PortfolioStrategy.user_id == current_user.user_id)
            .order_by(PortfolioStrategy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        strategies_result = await db.execute(strategies_query)
        strategies = strategies_result.scalars().all()

        # 2. 각 전략에 대한 가장 최근 백테스트 세션 조회
        response_data = []
        for strategy in strategies:
            # 해당 전략의 가장 최근 완료된 백테스트 세션 조회
            session_query = (
                select(SimulationSession)
                .where(
                    and_(
                        SimulationSession.strategy_id == strategy.strategy_id,
                        SimulationSession.status == "COMPLETED"
                    )
                )
                .order_by(SimulationSession.created_at.desc())
                .limit(1)
            )
            session_result = await db.execute(session_query)
            latest_session = session_result.scalar_one_or_none()

            # BacktestSession도 확인 (새로운 백테스트)
            backtest_query = (
                select(BacktestSession)
                .where(BacktestSession.strategy_id == strategy.strategy_id)
                .order_by(BacktestSession.created_at.desc())
                .limit(1)
            )
            backtest_result = await db.execute(backtest_query)
            latest_backtest = backtest_result.scalar_one_or_none()

            # 통계 조회 (SimulationStatistics 또는 BacktestStatistics)
            cumulative_return = 0.0
            max_drawdown = 0.0
            daily_return = 0.0

            if latest_backtest:
                # BacktestStatistics에서 조회
                from app.models.backtest import BacktestStatistics as NewBacktestStatistics
                stats_query = select(NewBacktestStatistics).where(
                    NewBacktestStatistics.backtest_id == latest_backtest.backtest_id
                )
                stats_result = await db.execute(stats_query)
                stats = stats_result.scalar_one_or_none()

                if stats:
                    cumulative_return = float(stats.total_return) if stats.total_return else 0.0
                    max_drawdown = float(stats.max_drawdown) if stats.max_drawdown else 0.0
                    # 일평균 수익률 = 연환산 수익률 / 252
                    daily_return = float(stats.annualized_return / 252) if stats.annualized_return else 0.0

                response_data.append({
                    "id": latest_backtest.backtest_id,
                    "strategy_name": strategy.strategy_name,
                    "daily_return": round(daily_return, 2),
                    "cumulative_return": round(cumulative_return, 2),
                    "max_drawdown": round(max_drawdown, 2),
                    "created_at": latest_backtest.created_at.strftime("%Y.%m.%d") if latest_backtest.created_at else ""
                })
            elif latest_session:
                # SimulationStatistics에서 조회
                stats_query = select(SimulationStatistics).where(
                    SimulationStatistics.session_id == latest_session.session_id
                )
                stats_result = await db.execute(stats_query)
                stats = stats_result.scalar_one_or_none()

                if stats:
                    cumulative_return = float(stats.total_return) if stats.total_return else 0.0
                    max_drawdown = float(stats.max_drawdown) if stats.max_drawdown else 0.0
                    daily_return = float(stats.annualized_return / 252) if stats.annualized_return else 0.0

                response_data.append({
                    "id": latest_session.session_id,
                    "strategy_name": strategy.strategy_name,
                    "daily_return": round(daily_return, 2),
                    "cumulative_return": round(cumulative_return, 2),
                    "max_drawdown": round(max_drawdown, 2),
                    "created_at": latest_session.created_at.strftime("%Y.%m.%d") if latest_session.created_at else ""
                })
            else:
                # 백테스트 세션이 없는 경우 (전략만 생성됨)
                response_data.append({
                    "id": strategy.strategy_id,
                    "strategy_name": strategy.strategy_name,
                    "daily_return": 0.0,
                    "cumulative_return": 0.0,
                    "max_drawdown": 0.0,
                    "created_at": strategy.created_at.strftime("%Y.%m.%d") if strategy.created_at else ""
                })

        # 전체 개수 조회
        count_query = (
            select(func.count(PortfolioStrategy.strategy_id))
            .where(PortfolioStrategy.user_id == current_user.user_id)
        )
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()

        return {
            "data": response_data,
            "pagination": {
                "page": (offset // limit) + 1,
                "limit": limit,
                "total": total_count,
                "total_pages": (total_count + limit - 1) // limit
            }
        }

    except Exception as e:
        logger.error(f"전략 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def execute_backtest_wrapper(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: float,
    benchmark: str,
    target_themes: List[str],  # 선택된 산업/테마 목록
    target_stocks: List[str],  # 선택된 개별 종목 코드 목록
    target_universes: List[str] = None,  # 선택된 유니버스 목록
    use_all_stocks: bool = False,  # 전체 종목 사용 여부
    buy_conditions: List[dict] = None,
    buy_logic: str = "AND",
    priority_factor: str = None,
    priority_order: str = "desc",
    max_holdings: int = 20,
    per_stock_ratio: float = 5.0,
    rebalance_frequency: str = "monthly",
    commission_rate: float = 0.015,
    slippage: float = 0.1,
    target_and_loss: dict = None,
    hold_days: dict = None,
    condition_sell: dict = None,
    max_buy_value: Optional[float] = None,
    max_daily_stock: Optional[int] = None,
    user_id: str = None  # 🚀 PRODUCTION: Rate Limiting용
):
    """백테스트 비동기 실행 래퍼 (완전 비동기 - DB 커넥션 풀 지원)"""
    try:
        # ✅ 개선: 동기 함수 제거, 완전 비동기로 실행 (DB 커넥션 풀 사용 가능)
        from app.services.advanced_backtest import _run_backtest_async

        await _run_backtest_async(
            session_id,
            strategy_id,
            start_date,
            end_date,
            Decimal(str(initial_capital)),
            benchmark,
            target_themes,
            target_stocks,
            target_universes or [],
            use_all_stocks,
            buy_conditions or [],
            buy_logic,
            priority_factor,
            priority_order,
            max_holdings,
            per_stock_ratio,
            rebalance_frequency,
            commission_rate,
            slippage,
            target_and_loss,
            hold_days,
            condition_sell,
            max_buy_value,
            max_daily_stock
        )

        logger.info(f"백테스트 완료: {session_id}")

    except Exception as e:
        logger.error(f"백테스트 래퍼 오류: {e}", exc_info=True)
    finally:
        # 🚀 PRODUCTION OPTIMIZATION: Rate Limit 감소 (완료 또는 실패 시)
        if user_id:
            try:
                from app.core.cache import get_redis
                redis_client = get_redis()
                if redis_client:
                    rate_limit_key = f"backtest:running:{user_id}"
                    running_count = await redis_client.get(rate_limit_key)

                    if running_count:
                        new_count = max(0, int(running_count) - 1)
                        if new_count > 0:
                            await redis_client.setex(rate_limit_key, 3600, new_count)
                        else:
                            await redis_client.delete(rate_limit_key)
                        logger.info(f"🚦 Rate Limit 감소: user_id={user_id}, 남은 실행: {new_count}/3")
            except Exception as e:
                # Redis 에러는 무시 (이미 백테스트는 완료됨)
                logger.warning(f"Rate Limit 감소 실패 (무시): {e}")


async def update_session_status_internal(
    db: AsyncSession,
    session_id: str,
    status: str,
    error_message: Optional[str] = None
):
    """세션 상태 업데이트 (내부 헬퍼 함수)"""
    from sqlalchemy import update

    stmt = update(SimulationSession).where(
        SimulationSession.session_id == session_id
    ).values(
        status=status,
        error_message=error_message,
        started_at=datetime.now() if status == "RUNNING" else None,
        completed_at=datetime.now() if status in ["COMPLETED", "FAILED"] else None
    )

    await db.execute(stmt)
    await db.commit()


@router.get("/factors/list")
async def list_available_factors(db: AsyncSession = Depends(get_db)):
    """사용 가능한 팩터 목록 - 실제 DB 데이터"""
    try:
        # factors와 factor_categories 조인해서 가져오기
        from app.models.simulation import Factor, FactorCategory

        query = (
            select(Factor, FactorCategory)
            .join(FactorCategory, Factor.category_id == FactorCategory.category_id)
            .where(Factor.is_active == True)
            .order_by(FactorCategory.display_order, Factor.factor_id)
        )

        result = await db.execute(query)
        rows = result.all()

        logger.info(f"📊 팩터 목록 조회: {len(rows)}개")

        # 응답 데이터 구성
        factors = []
        for idx, (factor, category) in enumerate(rows, start=1):
            factors.append({
                "id": idx,  # 순차적인 ID
                "name": factor.factor_id.lower(),  # 소문자로 변환 (PER -> per)
                "display_name": factor.factor_name,
                "category": category.category_name,
                "description": factor.description or f"{factor.factor_name} 지표"
            })

        return {"factors": factors}

    except Exception as e:
        logger.warning(f"팩터 목록 DB 조회 실패 (폴백 데이터 사용): {str(e)}")
        # 에러 발생 시 하드코딩된 폴백 팩터 목록 반환
        return {
            "factors": [
                # 가치 지표 (VALUE) - 14개
                {"id": 1, "name": "per", "display_name": "PER", "category": "가치", "description": "주가를 주당순이익으로 나눈 비율. 낮을수록 저평가"},
                {"id": 2, "name": "pbr", "display_name": "PBR", "category": "가치", "description": "주가를 주당순자산으로 나눈 비율. 낮을수록 저평가"},
                {"id": 3, "name": "psr", "display_name": "PSR", "category": "가치", "description": "시가총액을 매출액으로 나눈 비율. 낮을수록 저평가"},
                {"id": 4, "name": "pcr", "display_name": "PCR", "category": "가치", "description": "시가총액을 영업현금흐름으로 나눈 비율"},
                {"id": 5, "name": "peg", "display_name": "PEG", "category": "가치", "description": "PER을 순이익증가율로 나눈 비율"},
                {"id": 6, "name": "ev_ebitda", "display_name": "EV/EBITDA", "category": "가치", "description": "기업가치를 EBITDA로 나눈 비율"},
                {"id": 7, "name": "ev_sales", "display_name": "EV/Sales", "category": "가치", "description": "기업가치를 매출액으로 나눈 비율"},
                {"id": 8, "name": "ev_fcf", "display_name": "EV/FCF", "category": "가치", "description": "기업가치를 잉여현금흐름으로 나눈 비율"},
                {"id": 9, "name": "dividend_yield", "display_name": "배당수익률", "category": "가치", "description": "주당배당금을 주가로 나눈 비율"},
                {"id": 10, "name": "earnings_yield", "display_name": "이익수익률", "category": "가치", "description": "PER의 역수. 높을수록 저평가"},
                {"id": 11, "name": "fcf_yield", "display_name": "FCF 수익률", "category": "가치", "description": "잉여현금흐름을 시가총액으로 나눈 비율"},
                {"id": 12, "name": "book_to_market", "display_name": "장부가 대비 시가", "category": "가치", "description": "장부가를 시가총액으로 나눈 비율"},
                {"id": 13, "name": "cape_ratio", "display_name": "CAPE Ratio", "category": "가치", "description": "10년 평균 실질이익 기반 PER"},
                {"id": 14, "name": "ptbv", "display_name": "PTBV", "category": "가치", "description": "주가를 유형자산 기준 순자산으로 나눈 비율"},

                # 수익성 지표 (QUALITY) - 10개
                {"id": 15, "name": "roe", "display_name": "ROE", "category": "수익성", "description": "당기순이익을 자기자본으로 나눈 비율"},
                {"id": 16, "name": "roa", "display_name": "ROA", "category": "수익성", "description": "당기순이익을 총자산으로 나눈 비율"},
                {"id": 17, "name": "roic", "display_name": "ROIC", "category": "수익성", "description": "세후영업이익을 투하자본으로 나눈 비율"},
                {"id": 18, "name": "gpm", "display_name": "매출총이익률", "category": "수익성", "description": "매출총이익을 매출액으로 나눈 비율"},
                {"id": 19, "name": "opm", "display_name": "영업이익률", "category": "수익성", "description": "영업이익을 매출액으로 나눈 비율"},
                {"id": 20, "name": "npm", "display_name": "순이익률", "category": "수익성", "description": "당기순이익을 매출액으로 나눈 비율"},
                {"id": 21, "name": "asset_turnover", "display_name": "자산회전율", "category": "수익성", "description": "매출액을 총자산으로 나눈 비율"},
                {"id": 22, "name": "inventory_turnover", "display_name": "재고자산회전율", "category": "수익성", "description": "매출원가를 재고자산으로 나눈 비율"},
                {"id": 23, "name": "quality_score", "display_name": "품질점수", "category": "수익성", "description": "Piotroski F-Score 기반 품질 평가"},
                {"id": 24, "name": "accruals_ratio", "display_name": "발생액 비율", "category": "수익성", "description": "순이익 대비 현금흐름 차이"},

                # 성장 지표 (GROWTH) - 8개
                {"id": 25, "name": "revenue_growth_1y", "display_name": "매출액증가율(1Y)", "category": "성장", "description": "전년 대비 매출액 증가율"},
                {"id": 26, "name": "revenue_growth_3y", "display_name": "매출액증가율(3Y CAGR)", "category": "성장", "description": "3년 연평균 매출액 증가율"},
                {"id": 27, "name": "earnings_growth_1y", "display_name": "순이익증가율(1Y)", "category": "성장", "description": "전년 대비 순이익 증가율"},
                {"id": 28, "name": "earnings_growth_3y", "display_name": "순이익증가율(3Y CAGR)", "category": "성장", "description": "3년 연평균 순이익 증가율"},
                {"id": 29, "name": "ocf_growth_1y", "display_name": "영업현금흐름증가율", "category": "성장", "description": "전년 대비 영업현금흐름 증가율"},
                {"id": 30, "name": "asset_growth_1y", "display_name": "자산증가율", "category": "성장", "description": "전년 대비 총자산 증가율"},
                {"id": 31, "name": "book_value_growth_1y", "display_name": "순자산증가율", "category": "성장", "description": "전년 대비 순자산 증가율"},
                {"id": 32, "name": "sustainable_growth_rate", "display_name": "지속가능성장률", "category": "성장", "description": "ROE × 유보율로 계산한 지속가능 성장률"},

                # 모멘텀 지표 (MOMENTUM) - 8개
                {"id": 33, "name": "momentum_1m", "display_name": "1개월 모멘텀", "category": "모멘텀", "description": "최근 1개월(20영업일) 수익률"},
                {"id": 34, "name": "momentum_3m", "display_name": "3개월 모멘텀", "category": "모멘텀", "description": "최근 3개월(60영업일) 수익률"},
                {"id": 35, "name": "momentum_6m", "display_name": "6개월 모멘텀", "category": "모멘텀", "description": "최근 6개월(120영업일) 수익률"},
                {"id": 36, "name": "momentum_12m", "display_name": "12개월 모멘텀", "category": "모멘텀", "description": "최근 12개월(240영업일) 수익률"},
                {"id": 37, "name": "distance_from_52w_high", "display_name": "52주 최고가 대비", "category": "모멘텀", "description": "현재가와 52주 최고가의 거리"},
                {"id": 38, "name": "distance_from_52w_low", "display_name": "52주 최저가 대비", "category": "모멘텀", "description": "현재가와 52주 최저가의 거리"},
                {"id": 39, "name": "relative_strength", "display_name": "상대강도", "category": "모멘텀", "description": "시장 대비 초과 수익률"},
                {"id": 40, "name": "volume_momentum", "display_name": "거래량 모멘텀", "category": "모멘텀", "description": "거래량 증가율"},
                {"id": 41, "name": "change_rate", "display_name": "등락률", "category": "모멘텀", "description": "전일 대비 등락률(%)"},

                # 안정성 지표 (STABILITY) - 8개
                {"id": 42, "name": "debt_to_equity", "display_name": "부채비율", "category": "안정성", "description": "부채총계를 자기자본으로 나눈 비율"},
                {"id": 43, "name": "debt_ratio", "display_name": "부채비율(%)", "category": "안정성", "description": "부채총계를 총자산으로 나눈 비율"},
                {"id": 44, "name": "current_ratio", "display_name": "유동비율", "category": "안정성", "description": "유동자산을 유동부채로 나눈 비율"},
                {"id": 45, "name": "quick_ratio", "display_name": "당좌비율", "category": "안정성", "description": "당좌자산을 유동부채로 나눈 비율"},
                {"id": 46, "name": "interest_coverage", "display_name": "이자보상배율", "category": "안정성", "description": "영업이익을 이자비용으로 나눈 비율"},
                {"id": 47, "name": "altman_z_score", "display_name": "Altman Z-Score", "category": "안정성", "description": "파산 위험도 측정 지표"},
                {"id": 48, "name": "beta", "display_name": "베타", "category": "안정성", "description": "시장 대비 변동성"},
                {"id": 49, "name": "earnings_quality", "display_name": "이익품질", "category": "안정성", "description": "현금흐름 대비 순이익 비율"},

                # 기술적 지표 (TECHNICAL) - 6개
                {"id": 50, "name": "rsi_14", "display_name": "RSI(14)", "category": "기술적분석", "description": "14일 기준 상대강도지수 (0-100)"},
                {"id": 51, "name": "bollinger_position", "display_name": "볼린저밴드 위치", "category": "기술적분석", "description": "볼린저밴드 내 현재가 위치"},
                {"id": 52, "name": "macd_signal", "display_name": "MACD 시그널", "category": "기술적분석", "description": "MACD와 시그널선 차이"},
                {"id": 53, "name": "stochastic_14", "display_name": "스토캐스틱(14)", "category": "기술적분석", "description": "14일 기준 스토캐스틱 (0-100)"},
                {"id": 54, "name": "volume_roc", "display_name": "거래량 변화율", "category": "기술적분석", "description": "거래량 변화율"},
                {"id": 55, "name": "price_position", "display_name": "가격 위치", "category": "기술적분석", "description": "52주 범위 내 현재가 위치 (0-100)"},
            ]
        }


@router.get("/sub-factors/list")
async def list_available_sub_factors():
    """사용 가능한 서브 팩터(함수) 목록"""
    return {
        "sub_factors": [
  {
    "id": 1,
    "name": "default_val",
    "display_name": "기본값",
    "arguments": [],
    "description": "입력한 팩터 값을 가공 없이 그대로 사용합니다."
  },
  {
    "id": 2,
    "name": "past_val",
    "display_name": "과거값",
    "arguments": ["1일", "2일", "3일", "5일", "1주", "1월", "1년"],
    "description": "N일/주/월/년 이전의 팩터 값을 사용합니다."
  },
  {
    "id": 3,
    "name": "moving_avg_val",
    "display_name": "이동평균",
    "arguments": ["5일", "10일", "20일", "25일",],
    "description": "특정 기간 동안의 팩터값의 평균을 계산합니다."
  },
  {
    "id": 4,
    "name": "ratio_val",
    "display_name": "비율",
    "arguments": ["내림차순", "오름차순"],
    "description": "팩터에 속한 종목에 0~100 사이의 비율을 부여합니다."
  },
  {
    "id": 5,
    "name": "rank_val",
    "display_name": "순위",
    "arguments": ["내림차순", "오름차순"],
    "description": "팩터에 속한 종목들에 등수를 부여합니다. (1 ~ 등수)"
  },
  {
    "id": 6,
    "name": "max_val_period",
    "display_name": "최고값",
    "arguments": ["5일", "10일", "20일", "25일",],
    "description": "N일 이내 팩터의 최고값을 활용합니다."
  },
  {
    "id": 7,
    "name": "min_val_period",
    "display_name": "최저값",
    "arguments": ["5일", "10일", "20일", "25일",],
    "description": "N일 이내 팩터의 최저값을 활용합니다."
  },
  {
    "id": 8,
    "name": "change_amount_period",
    "display_name": "변화량_기간",
    "arguments": ["1일", "2일", "3일", "5일", "1주", "1월", "1년"],
    "description": "N일 전 대비 변화량을 측정합니다."
  },
  {
    "id": 9,
    "name": "change_rate_period",
    "display_name": "변화율_기간",
    "arguments": ["1일", "2일", "3일", "5일", "1주", "1월", "1년"],
    "description": "N일 전 대비 변화율을 측정합니다."
  }
]
    }


@router.get("/initialize")
async def get_backtest_init_data():
    """
    백테스트 초기화 데이터 통합 조회
    - 팩터, 서브팩터, 테마 목록을 한 번에 반환
    - 3번의 HTTP 요청을 1번으로 최적화
    - asyncio.gather()로 병렬 처리하여 성능 최적화 (순차 실행 대비 3배 빠름)

    Returns:
        dict: factors, sub_factors, themes 목록을 포함한 딕셔너리
    """
    # 3개의 API를 병렬로 동시 실행 (asyncio.gather 사용)
    factors_response, sub_factors_response, themes_response = await asyncio.gather(
        list_available_factors(),
        list_available_sub_factors(),
        list_available_themes()
    )

    return {
        "factors": factors_response["factors"],
        "sub_factors": sub_factors_response["sub_factors"],
        "themes": themes_response["themes"]
    }


@router.get("/themes/list")
async def list_available_themes():
    """사용 가능한 테마 목록"""
    return {"themes": THEME_DEFINITIONS}


@router.post("/backtest/{backtest_id}/save-portfolio")
async def save_backtest_as_portfolio(
    backtest_id: str,
    request: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """
    백테스트 결과를 포트폴리오로 저장
    - SimulationSession의 is_portfolio 플래그를 True로 설정
    - 포트폴리오 이름 저장
    - 통계 정보 확인
    """
    try:
        # 1. 백테스트 세션 확인
        session_query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

        # 2. 권한 확인 (옵셔널 - 로그인한 경우만)
        if current_user and session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="이 백테스트를 저장할 권한이 없습니다"
            )

        # 3. 상태 확인 (완료된 백테스트만 저장 허용)
        if session.status != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"백테스트 상태가 {session.status}입니다. 완료된 백테스트만 포트폴리오로 저장할 수 있습니다"
            )

        # 4. 통계 정보 확인 (필수)
        stats_query = select(SimulationStatistics).where(
            SimulationStatistics.session_id == backtest_id
        )
        stats_result = await db.execute(stats_query)
        statistics = stats_result.scalar_one_or_none()

        if not statistics:
            raise HTTPException(
                status_code=400,
                detail="백테스트 통계가 없어 포트폴리오로 저장할 수 없습니다"
            )

        # 5. 포트폴리오로 저장
        portfolio_name = request.get("name", "")
        if not portfolio_name:
            # 기본 이름 생성
            portfolio_name = f"{session.session_name or '백테스트'}_포트폴리오"

        # is_portfolio 플래그 설정
        session.is_portfolio = True
        session.portfolio_name = portfolio_name
        session.saved_at = func.now()

        # 6. portfolio_strategies 테이블 업데이트 (포트폴리오 목록에 표시하기 위해)
        # simulation_sessions는 이미 strategy_id를 가지고 있으므로,
        # portfolio_strategies의 strategy_name만 업데이트
        from app.models.simulation import PortfolioStrategy

        if session.strategy_id:
            strategy_query = select(PortfolioStrategy).where(
                PortfolioStrategy.strategy_id == session.strategy_id
            )
            strategy_result = await db.execute(strategy_query)
            strategy = strategy_result.scalar_one_or_none()

            if strategy:
                # 기존 전략의 이름을 포트폴리오 이름으로 업데이트
                strategy.strategy_name = portfolio_name
                strategy.updated_at = func.now()
                logger.info(f"📊 portfolio_strategies 업데이트: {portfolio_name}")
            else:
                logger.warning(f"⚠️ strategy_id {session.strategy_id}에 해당하는 전략을 찾을 수 없습니다")

        # 7. DB 커밋
        await db.commit()

        logger.info(f"✅ 포트폴리오 저장 완료 - ID: {backtest_id}, 이름: {portfolio_name}")

        def _safe_float(value: Any, default: float = 0.0) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        return {
            "success": True,
            "message": "포트폴리오가 성공적으로 저장되었습니다",
            "portfolio_id": session.session_id,
            "portfolio_name": portfolio_name,
            "statistics": {
                "total_return": _safe_float(statistics.total_return),
                "annualized_return": _safe_float(statistics.annualized_return),
                "max_drawdown": _safe_float(statistics.max_drawdown)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트폴리오 저장 실패: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"포트폴리오 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_backtest_cache(
    cache_type: Optional[str] = "all",
    user: User = Depends(get_current_user)
):
    """
    백테스트 캐시 클리어 (일관성 보장을 위해)

    Args:
        cache_type: 클리어할 캐시 타입 ("all", "price", "financial")

    Returns:
        캐시 클리어 결과
    """
    try:
        from app.core.cache import get_cache
        cache = get_cache()

        cleared_keys = []

        if cache_type in ["all", "price"]:
            # 가격 데이터 캐시 클리어
            pattern = "price_data:*"
            keys = await cache.redis.keys(pattern)
            if keys:
                await cache.redis.delete(*keys)
                cleared_keys.extend([k.decode() if isinstance(k, bytes) else k for k in keys])
                logger.info(f"🗑️ 가격 데이터 캐시 클리어: {len(keys)}개 키")

        if cache_type in ["all", "financial"]:
            # 재무 데이터 캐시 클리어
            pattern = "financial_data:*"
            keys = await cache.redis.keys(pattern)
            if keys:
                await cache.redis.delete(*keys)
                cleared_keys.extend([k.decode() if isinstance(k, bytes) else k for k in keys])
                logger.info(f"🗑️ 재무 데이터 캐시 클리어: {len(keys)}개 키")

        if cache_type == "all":
            # 팩터 데이터 캐시 클리어
            pattern = "factor:*"
            keys = await cache.redis.keys(pattern)
            if keys:
                await cache.redis.delete(*keys)
                cleared_keys.extend([k.decode() if isinstance(k, bytes) else k for k in keys])
                logger.info(f"🗑️ 팩터 데이터 캐시 클리어: {len(keys)}개 키")

        return {
            "success": True,
            "message": f"캐시 클리어 완료: {len(cleared_keys)}개 키",
            "cache_type": cache_type,
            "cleared_count": len(cleared_keys)
        }

    except Exception as e:
        logger.error(f"캐시 클리어 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"캐시 클리어 실패: {str(e)}")


@router.websocket("/ws/backtest/{backtest_id}")
async def backtest_websocket(
    websocket: WebSocket,
    backtest_id: str
):
    """
    백테스트 실시간 진행 상황 WebSocket

    클라이언트는 백테스트 시작 후 이 엔드포인트에 연결하여
    실시간으로 차트 데이터를 받을 수 있습니다.

    메시지 타입:
    - progress: 일별 포트폴리오 가치 업데이트
    - trade: 거래 내역
    - completed: 백테스트 완료
    - error: 에러 발생
    """
    from app.services.backtest_websocket import ws_manager

    try:
        await ws_manager.connect(backtest_id, websocket)
        logger.info(f"📡 백테스트 WebSocket 연결: {backtest_id}")

        # 연결 유지 (클라이언트가 메시지를 보낼 수 있도록)
        while True:
            try:
                # 클라이언트로부터 메시지 수신 (ping/pong)
                data = await websocket.receive_text()

                # ping 메시지에 대한 응답
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                logger.info(f"📡 백테스트 WebSocket 연결 해제: {backtest_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket 에러: {e}")
                break

    finally:
        ws_manager.disconnect(backtest_id, websocket)


# ==================== 히스토리 조회 API ====================

class BacktestHistoryItem(BaseModel):
    """백테스트 히스토리 항목"""
    session_id: str = Field(..., serialization_alias="sessionId")
    session_name: Optional[str] = Field(None, serialization_alias="sessionName")
    status: str
    start_date: str = Field(..., serialization_alias="startDate")
    end_date: str = Field(..., serialization_alias="endDate")
    initial_capital: float = Field(..., serialization_alias="initialCapital")
    total_return: Optional[float] = Field(None, serialization_alias="totalReturn")
    annualized_return: Optional[float] = Field(None, serialization_alias="annualizedReturn")
    max_drawdown: Optional[float] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[float] = Field(None, serialization_alias="sharpeRatio")
    total_trades: Optional[int] = Field(None, serialization_alias="totalTrades")
    win_rate: Optional[float] = Field(None, serialization_alias="winRate")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")

    class Config:
        populate_by_name = True


class BacktestHistoryResponse(BaseModel):
    """백테스트 히스토리 응답"""
    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")
    total_count: int = Field(..., serialization_alias="totalCount")
    history: List[BacktestHistoryItem]

    class Config:
        populate_by_name = True


@router.get("/strategy/{strategy_id}/history", response_model=BacktestHistoryResponse)
async def get_strategy_backtest_history(
    strategy_id: str,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    전략의 백테스트 히스토리 조회

    동일 전략(strategy_id)으로 실행된 모든 백테스트 결과를 시간순으로 조회합니다.
    과거 결과와 비교하거나, 조건 변경에 따른 성과 차이를 분석할 수 있습니다.
    """
    # 1. 전략 정보 조회
    strategy_query = select(PortfolioStrategy).where(PortfolioStrategy.strategy_id == strategy_id)
    strategy_result = await db.execute(strategy_query)
    strategy = strategy_result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")

    # 2. 해당 전략의 백테스트 세션 수 조회
    count_query = select(func.count()).where(SimulationSession.strategy_id == strategy_id)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()

    # 3. 백테스트 세션 목록 조회 (페이지네이션, 최신순)
    offset = (page - 1) * limit
    sessions_query = (
        select(SimulationSession)
        .where(SimulationSession.strategy_id == strategy_id)
        .order_by(SimulationSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions_result = await db.execute(sessions_query)
    sessions = sessions_result.scalars().all()

    # 4. 각 세션의 통계 조회
    session_ids = [s.session_id for s in sessions]
    stats_query = select(SimulationStatistics).where(SimulationStatistics.session_id.in_(session_ids))
    stats_result = await db.execute(stats_query)
    stats_map = {s.session_id: s for s in stats_result.scalars().all()}

    # 5. 히스토리 항목 생성
    history_items = []
    for session in sessions:
        stats = stats_map.get(session.session_id)

        history_items.append(BacktestHistoryItem(
            session_id=session.session_id,
            session_name=session.session_name,
            status=session.status.lower() if session.status else "pending",
            start_date=session.start_date.isoformat() if session.start_date else "",
            end_date=session.end_date.isoformat() if session.end_date else "",
            initial_capital=float(session.initial_capital) if session.initial_capital else 0,
            total_return=float(stats.total_return) if stats and stats.total_return else None,
            annualized_return=float(stats.annualized_return) if stats and stats.annualized_return else None,
            max_drawdown=float(stats.max_drawdown) if stats and stats.max_drawdown else None,
            sharpe_ratio=float(stats.sharpe_ratio) if stats and stats.sharpe_ratio else None,
            total_trades=stats.total_trades if stats else None,
            win_rate=float(stats.win_rate) if stats and stats.win_rate else None,
            created_at=session.created_at,
            completed_at=session.completed_at
        ))

    return BacktestHistoryResponse(
        strategy_id=strategy_id,
        strategy_name=strategy.strategy_name,
        total_count=total_count,
        history=history_items
    )


@router.delete("/backtest/{backtest_id}")
async def delete_backtest(
    backtest_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    백테스트 결과 삭제

    특정 백테스트 결과만 삭제합니다. 전략은 유지됩니다.
    본인이 생성한 백테스트만 삭제할 수 있습니다.
    """
    # 1. 세션 조회 및 권한 확인
    session_query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    if str(session.user_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="본인의 백테스트만 삭제할 수 있습니다")

    # 2. 관련 데이터 삭제 (CASCADE로 자동 삭제되지만 명시적으로 처리)
    from sqlalchemy import delete
    from app.models.simulation import SimulationDailyValue, SimulationTrade, SimulationPosition, SimulationStatistics

    await db.execute(delete(SimulationDailyValue).where(SimulationDailyValue.session_id == backtest_id))
    await db.execute(delete(SimulationTrade).where(SimulationTrade.session_id == backtest_id))
    await db.execute(delete(SimulationPosition).where(SimulationPosition.session_id == backtest_id))
    await db.execute(delete(SimulationStatistics).where(SimulationStatistics.session_id == backtest_id))
    await db.execute(delete(SimulationSession).where(SimulationSession.session_id == backtest_id))

    await db.commit()

    logger.info(f"🗑️ 백테스트 삭제 완료: {backtest_id}")

    return {"message": "백테스트가 삭제되었습니다", "backtest_id": backtest_id}
