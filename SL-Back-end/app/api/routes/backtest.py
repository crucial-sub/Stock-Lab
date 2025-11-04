"""
백테스트 API 라우터
- 백테스트 실행
- 결과 조회
- 상태 확인
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
import uuid
import logging
import asyncio

from app.core.database import get_db
from app.models.simulation import (
    SimulationSession,
    PortfolioStrategy,
    StrategyFactor,
    TradingRule,
    SimulationStatistics,
    SimulationDailyValue,
    SimulationTrade
)
from app.models.company import Company
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class BuyCondition(BaseModel):
    """매수 조건"""
    name: str  # 조건식 이름 e.g. "A"
    expression: str  # 조건식 e.g. "{PER} > 10"


class TargetAndLoss(BaseModel):
    """목표가/손절가"""
    target_gain: Optional[float] = None
    stop_loss: Optional[float] = None


class HoldDays(BaseModel):
    """보유 기간"""
    min_hold_days: int
    max_hold_days: int
    sell_cost_basis: str


class SellConditions(BaseModel):
    """매도 조건"""
    name: str
    expression: str
    sell_logic: str
    sell_cost_basis: str


class BacktestRequest(BaseModel):
    """백테스트 실행 요청 - 프론트엔드 스키마에 맞춤"""
    # 기본 설정
    user_id: str
    strategy_name: str
    is_day_or_month: str  # "daily" or "monthly"
    start_date: str  # YYYYMMDD
    end_date: str  # YYYYMMDD
    initial_investment: float  # 만원 단위
    commission_rate: float  # %

    # 매수 조건
    buy_conditions: List[BuyCondition]
    buy_logic: str
    priority_factor: str
    priority_order: str  # "asc" or "desc"
    per_stock_ratio: float  # %
    max_holdings: int
    max_buy_value: Optional[float] = None  # 만원 단위
    max_daily_stock: Optional[int] = None
    buy_cost_basis: str

    # 매도 조건
    target_and_loss: Optional[TargetAndLoss] = None
    hold_days: Optional[HoldDays] = None
    sell_conditions: Optional[SellConditions] = None

    # 매매 대상
    target_stocks: List[str]  # 테마 이름 목록


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    backtestId: str  # Frontend 형식에 맞춤 (camelCase)
    status: str
    message: str
    createdAt: datetime  # Frontend 형식에 맞춤 (camelCase)


class BacktestStatusResponse(BaseModel):
    """백테스트 상태 응답"""
    backtest_id: str
    status: str
    progress: int
    message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class BacktestResultStatistics(BaseModel):
    """백테스트 결과 통계"""
    model_config = ConfigDict(populate_by_name=True)

    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: float = Field(..., serialization_alias="maxDrawdown")
    volatility: float
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
    model_config = ConfigDict(populate_by_name=True)

    stock_name: str = Field(..., serialization_alias="stockName")
    stock_code: str = Field(..., serialization_alias="stockCode")
    buy_price: float = Field(..., serialization_alias="buyPrice")
    sell_price: float = Field(..., serialization_alias="sellPrice")
    profit: float
    profit_rate: float = Field(..., serialization_alias="profitRate")
    buy_date: str = Field(..., serialization_alias="buyDate")
    sell_date: str = Field(..., serialization_alias="sellDate")
    weight: float
    valuation: float


class BacktestYieldPoint(BaseModel):
    """백테스트 수익률 포인트"""
    date: str
    value: float


class BacktestResultResponse(BaseModel):
    """백테스트 결과 응답"""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: str
    statistics: BacktestResultStatistics
    trades: List[BacktestTrade]
    yield_points: List[BacktestYieldPoint] = Field(..., serialization_alias="yieldPoints")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")


@router.post("/backtest/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 실행
    - 비동기로 백그라운드 실행
    - 세션 ID 즉시 반환
    """
    try:
        # 1. 세션 ID 생성
        session_id = str(uuid.uuid4())

        # 2. 날짜 파싱 (YYYYMMDD -> date)
        from datetime import datetime as dt
        start_date = dt.strptime(request.start_date, "%Y%m%d").date()
        end_date = dt.strptime(request.end_date, "%Y%m%d").date()

        # 3. 투자 금액 변환 (만원 -> 원)
        initial_capital = Decimal(str(request.initial_investment * 10000))

        # 4. 전략 생성
        strategy_id = str(uuid.uuid4())
        strategy = PortfolioStrategy(
            strategy_id=strategy_id,
            strategy_name=request.strategy_name,
            description=f"User: {request.user_id}, Target: {', '.join(request.target_stocks[:3])}{'...' if len(request.target_stocks) > 3 else ''}",
            strategy_type="FACTOR_BASED",
            universe_type="THEME",  # 테마 기반 선택
            initial_capital=initial_capital
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
                "conditions": [{"name": c.name, "expression": c.expression} for c in request.buy_conditions],
                "logic": request.buy_logic,
                "priority_factor": request.priority_factor,
                "priority_order": request.priority_order,
                "per_stock_ratio": request.per_stock_ratio,
                "max_buy_value": request.max_buy_value,
                "max_daily_stock": request.max_daily_stock,
                "buy_cost_basis": request.buy_cost_basis
            },
            sell_condition={
                "target_and_loss": request.target_and_loss.dict() if request.target_and_loss else None,
                "hold_days": request.hold_days.dict() if request.hold_days else None,
                "sell_conditions": request.sell_conditions.dict() if request.sell_conditions else None
            }
        )
        db.add(trading_rule)

        # 6. 세션 생성
        session = SimulationSession(
            session_id=session_id,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            benchmark="KOSPI",
            status="PENDING",
            progress=0,
            created_at=datetime.now()
        )
        db.add(session)

        await db.commit()

        # 7. 백그라운드에서 백테스트 실행
        logger.info(f"백테스트 시작 - Session: {session_id}, Strategy: {request.strategy_name}")
        asyncio.create_task(
            execute_backtest_wrapper(
                session_id,
                strategy_id,
                start_date,
                end_date,
                initial_capital,
                "KOSPI"
            )
        )

        return BacktestResponse(
            backtestId=session_id,
            status="pending",
            message="백테스트가 시작되었습니다",
            createdAt=datetime.now()
        )

    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{backtest_id}/status", response_model=BacktestStatusResponse)
async def get_backtest_status(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 상태 조회"""
    query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    return BacktestStatusResponse(
        backtest_id=session.session_id,
        status=session.status.lower() if session.status else "pending",
        progress=session.progress or 0,
        message=f"진행률: {session.progress}%",
        started_at=session.started_at,
        completed_at=session.completed_at,
        error_message=session.error_message
    )


@router.get("/backtest/{backtest_id}/result", response_model=BacktestResultResponse)
async def get_backtest_result(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 결과 조회"""
    # 1. 세션 확인
    session_query = select(SimulationSession).where(SimulationSession.session_id == backtest_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

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
                final_capital=float(session.initial_capital)
            ),
            trades=[],
            yield_points=[],
            created_at=session.created_at,
            completed_at=session.completed_at
        )

    # 2. 통계 조회
    stats_query = select(SimulationStatistics).where(SimulationStatistics.session_id == backtest_id)
    stats_result = await db.execute(stats_query)
    stats = stats_result.scalar_one_or_none()

    if not stats:
        raise HTTPException(status_code=404, detail="백테스트 통계를 찾을 수 없습니다")

    # 3. 거래 내역 조회 (최대 100개)
    trades_query = (
        select(SimulationTrade)
        .where(SimulationTrade.session_id == backtest_id)
        .order_by(SimulationTrade.trade_date.desc())
        .limit(100)
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

    # 5. 종목 코드 목록 추출 및 종목명 조회
    stock_codes = list(set([trade.stock_code for trade in trades]))
    companies_query = select(Company).where(Company.stock_code.in_(stock_codes))
    companies_result = await db.execute(companies_query)
    companies = companies_result.scalars().all()

    # 종목 코드 → 종목명 매핑
    stock_name_map = {company.stock_code: company.company_name for company in companies}

    # 6. 데이터 변환 - 매수/매도 거래를 매칭
    trade_list = []
    buy_trades_by_stock = {}

    # 먼저 모든 BUY 거래를 수집
    for trade in trades:
        if trade.trade_type == "BUY":
            buy_trades_by_stock[trade.stock_code] = trade

    # SELL 거래를 처리하며 대응하는 BUY 거래 찾기
    for trade in trades:
        if trade.trade_type == "SELL" and trade.realized_pnl is not None:
            buy_trade = buy_trades_by_stock.get(trade.stock_code)

            trade_list.append(BacktestTrade(
                stock_name=stock_name_map.get(trade.stock_code, trade.stock_code),
                stock_code=trade.stock_code,
                buy_price=float(buy_trade.price) if buy_trade else 0,
                sell_price=float(trade.price),
                profit=float(trade.realized_pnl),
                profit_rate=float(trade.return_pct) if trade.return_pct else 0,
                buy_date=buy_trade.trade_date.isoformat() if buy_trade else "",
                sell_date=trade.trade_date.isoformat(),
                weight=float(trade.amount / session.initial_capital * 100) if session.initial_capital else 0,
                valuation=float(trade.amount)
            ))

    yield_points = [
        BacktestYieldPoint(
            date=dv.date.isoformat(),
            value=float(dv.cumulative_return) if dv.cumulative_return else 0
        )
        for dv in daily_values
    ]

    return BacktestResultResponse(
        id=backtest_id,
        status="completed",
        statistics=BacktestResultStatistics(
            total_return=float(stats.total_return),
            annualized_return=float(stats.annualized_return),
            max_drawdown=float(stats.max_drawdown),
            volatility=float(stats.volatility),
            sharpe_ratio=float(stats.sharpe_ratio),
            win_rate=float(stats.win_rate),
            profit_factor=float(stats.profit_factor) if stats.profit_factor else 0,
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            losing_trades=stats.losing_trades,
            initial_capital=float(session.initial_capital),
            final_capital=float(stats.final_capital)
        ),
        trades=trade_list,
        yield_points=yield_points,
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

    # 2. 모든 BUY 거래를 먼저 조회 (매칭용)
    buy_trades_query = select(SimulationTrade).where(
        SimulationTrade.session_id == backtest_id,
        SimulationTrade.trade_type == "BUY"
    )
    buy_trades_result = await db.execute(buy_trades_query)
    all_buy_trades = buy_trades_result.scalars().all()

    # BUY 거래를 종목 코드별로 매핑
    buy_trades_by_stock = {}
    for trade in all_buy_trades:
        buy_trades_by_stock[trade.stock_code] = trade

    # 3. 거래 내역 조회 (페이지네이션)
    offset = (page - 1) * limit
    trades_query = (
        select(SimulationTrade)
        .where(SimulationTrade.session_id == backtest_id)
        .order_by(SimulationTrade.trade_date.desc())
        .limit(limit)
        .offset(offset)
    )
    trades_result = await db.execute(trades_query)
    trades = trades_result.scalars().all()

    # 4. 총 거래 수 조회
    from sqlalchemy import func
    count_query = select(func.count()).select_from(SimulationTrade).where(
        SimulationTrade.session_id == backtest_id
    )
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # 5. 종목 코드 목록 추출 및 종목명 조회
    stock_codes = list(set([trade.stock_code for trade in trades]))
    companies_query = select(Company).where(Company.stock_code.in_(stock_codes))
    companies_result = await db.execute(companies_query)
    companies = companies_result.scalars().all()

    # 종목 코드 → 종목명 매핑
    stock_name_map = {company.stock_code: company.company_name for company in companies}

    # 6. 데이터 변환 - 매수/매도 거래를 매칭
    trade_list = []

    # SELL 거래를 처리하며 대응하는 BUY 거래 찾기
    for trade in trades:
        if trade.trade_type == "SELL" and trade.realized_pnl is not None:
            buy_trade = buy_trades_by_stock.get(trade.stock_code)

            trade_list.append({
                "stockName": stock_name_map.get(trade.stock_code, trade.stock_code),
                "stockCode": trade.stock_code,
                "buyPrice": float(buy_trade.price) if buy_trade else 0.0,
                "sellPrice": float(trade.price),
                "profit": float(trade.realized_pnl),
                "profitRate": float(trade.return_pct) if trade.return_pct else 0.0,
                "buyDate": buy_trade.trade_date.isoformat() if buy_trade else "",
                "sellDate": trade.trade_date.isoformat(),
                "weight": float(trade.amount / session.initial_capital * 100) if session.initial_capital else 0.0,
                "valuation": float(trade.amount)
            })

    return {
        "data": trade_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "totalPages": (total_count + limit - 1) // limit
        }
    }


@router.get("/backtest/list")
async def list_backtests(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 목록 조회"""
    query = (
        select(SimulationSession)
        .order_by(SimulationSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return [
        {
            "backtest_id": s.session_id,
            "status": s.status.lower() if s.status else "pending",
            "progress": s.progress or 0,
            "start_date": s.start_date.isoformat(),
            "end_date": s.end_date.isoformat(),
            "created_at": s.created_at,
            "completed_at": s.completed_at
        }
        for s in sessions
    ]


async def execute_backtest_wrapper(
    session_id: str,
    strategy_id: str,
    start_date: date,
    end_date: date,
    initial_capital: float,
    benchmark: str
):
    """백테스트 비동기 실행 래퍼 (동기 버전 사용)"""
    try:
        # 동기 백테스트 실행 (greenlet 이슈 회피)
        from app.services.simple_backtest import run_simple_backtest

        # 동기 함수를 별도 스레드에서 실행
        import asyncio
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            run_simple_backtest,
            session_id,
            strategy_id,
            start_date,
            end_date,
            Decimal(str(initial_capital)),
            benchmark
        )

        logger.info(f"백테스트 완료: {session_id}")

    except Exception as e:
        logger.error(f"백테스트 래퍼 오류: {e}")


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
async def list_available_factors():
    """사용 가능한 팩터 목록"""
    return {
        "factors": [
            {"id": "PER", "name": "주가수익비율", "category": "value", "description": "Price to Earnings Ratio"},
            {"id": "PBR", "name": "주가순자산비율", "category": "value", "description": "Price to Book Ratio"},
            {"id": "ROE", "name": "자기자본이익률", "category": "profitability", "description": "Return on Equity"},
            {"id": "ROA", "name": "총자산이익률", "category": "profitability", "description": "Return on Assets"},
            {"id": "REVENUE_GROWTH", "name": "매출성장률", "category": "growth", "description": "Revenue Growth Rate"},
            {"id": "EARNINGS_GROWTH", "name": "이익성장률", "category": "growth", "description": "Earnings Growth Rate"},
            {"id": "DEBT_RATIO", "name": "부채비율", "category": "stability", "description": "Debt to Equity Ratio"},
            {"id": "CURRENT_RATIO", "name": "유동비율", "category": "stability", "description": "Current Ratio"},
            {"id": "MOMENTUM_1M", "name": "1개월 모멘텀", "category": "momentum", "description": "1 Month Price Momentum"},
            {"id": "MOMENTUM_3M", "name": "3개월 모멘텀", "category": "momentum", "description": "3 Month Price Momentum"},
            {"id": "MOMENTUM_6M", "name": "6개월 모멘텀", "category": "momentum", "description": "6 Month Price Momentum"},
            {"id": "MOMENTUM_12M", "name": "12개월 모멘텀", "category": "momentum", "description": "12 Month Price Momentum"},
            {"id": "VOLATILITY", "name": "변동성", "category": "risk", "description": "Price Volatility"},
            {"id": "TRADING_VOLUME", "name": "거래량", "category": "liquidity", "description": "Trading Volume"},
            {"id": "MARKET_CAP", "name": "시가총액", "category": "size", "description": "Market Capitalization"},
            {"id": "DIV_YIELD", "name": "배당수익률", "category": "value", "description": "Dividend Yield"},
            {"id": "EV_EBITDA", "name": "EV/EBITDA", "category": "value", "description": "Enterprise Value to EBITDA"},
            {"id": "GP_A", "name": "매출총이익률", "category": "quality", "description": "Gross Profitability"},
            {"id": "BETA", "name": "베타", "category": "risk", "description": "Market Beta"},
            {"id": "RSI", "name": "RSI", "category": "technical", "description": "Relative Strength Index"}
        ]
    }


@router.get("/sub-factors/list")
async def list_available_sub_factors():
    """사용 가능한 함수 목록"""
    return {
        "sub_factors": [
            {"id": "AND", "name": "AND 조건", "description": "모든 조건이 참일 때"},
            {"id": "OR", "name": "OR 조건", "description": "하나 이상의 조건이 참일 때"},
            {"id": "NOT", "name": "NOT 조건", "description": "조건이 거짓일 때"},
            {"id": "CROSS_UP", "name": "상향 돌파", "description": "값이 기준선을 상향 돌파할 때"},
            {"id": "CROSS_DOWN", "name": "하향 돌파", "description": "값이 기준선을 하향 돌파할 때"},
            {"id": "RANK", "name": "순위", "description": "지정된 범위 내 순위"},
            {"id": "PERCENTILE", "name": "백분위", "description": "백분위 순위"},
            {"id": "Z_SCORE", "name": "Z-Score", "description": "표준화 점수"},
            {"id": "MOVING_AVG", "name": "이동평균", "description": "N일 이동평균"},
            {"id": "COMPARE", "name": "비교", "description": "두 값을 비교"}
        ]
    }


@router.get("/themes/list")
async def list_available_themes():
    """사용 가능한 테마 목록"""
    return {
        "sectors": [
            {"id": "construction", "name": "건설"},
            {"id": "metal", "name": "금속"},
            {"id": "finance", "name": "금융"},
            {"id": "machinery", "name": "기계 / 장비"},
            {"id": "other-finance", "name": "기타 금융"},
            {"id": "other-manufacturing", "name": "기타 제조"},
            {"id": "other", "name": "기타"},
            {"id": "agriculture", "name": "농업 / 임업 / 어업"},
            {"id": "insurance", "name": "보험"},
            {"id": "real-estate", "name": "부동산"},
            {"id": "non-metal", "name": "비금속"},
            {"id": "textile", "name": "섬유 / 의류"},
            {"id": "entertainment", "name": "오락 / 문화"},
            {"id": "transport", "name": "운송 / 창고"},
            {"id": "transport-equipment", "name": "운송장비 / 부품"},
            {"id": "distribution", "name": "유통"},
            {"id": "bank", "name": "은행"},
            {"id": "food", "name": "음식료 / 담배"},
            {"id": "medical", "name": "의료 / 정밀기기"},
            {"id": "service", "name": "일반 서비스"},
            {"id": "utility", "name": "전기 / 가스 / 수도"},
            {"id": "electronics", "name": "전기 / 전자"},
            {"id": "pharma", "name": "제약"},
            {"id": "paper", "name": "종이 / 목재"},
            {"id": "securities", "name": "증권"},
            {"id": "publishing", "name": "출판 / 매체 복제"},
            {"id": "telecom", "name": "통신"},
            {"id": "chemical", "name": "화학"},
            {"id": "it-service", "name": "IT서비스"},
        ]
    }

