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
class BacktestCondition(BaseModel):
    """백테스트 조건"""
    factor: str
    operator: str  # GT, LT, EQ, TOP_N, BOTTOM_N
    value: float


class BacktestRequest(BaseModel):
    """백테스트 실행 요청"""
    buy_conditions: List[BacktestCondition]
    sell_conditions: List[BacktestCondition]
    start_date: date = Field(default=date(2020, 1, 1))
    end_date: date = Field(default=date(2024, 12, 31))
    initial_capital: float = Field(default=100000000, ge=1000000)  # 최소 100만원
    rebalance_frequency: str = Field(default="MONTHLY")  # DAILY, WEEKLY, MONTHLY, QUARTERLY
    max_positions: int = Field(default=20, ge=1, le=100)
    position_sizing: str = Field(default="EQUAL_WEIGHT")  # EQUAL_WEIGHT, MARKET_CAP, RISK_PARITY
    benchmark: str = Field(default="KOSPI")


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    backtest_id: str
    status: str
    message: str
    created_at: datetime


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
    total_return: float
    annualized_return: float
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    initial_capital: float
    final_capital: float


class BacktestTrade(BaseModel):
    """백테스트 거래 내역"""
    stock_name: str
    stock_code: str
    buy_price: float
    sell_price: float
    profit: float
    profit_rate: float
    buy_date: str
    sell_date: str
    weight: float
    valuation: float


class BacktestYieldPoint(BaseModel):
    """백테스트 수익률 포인트"""
    date: str
    value: float


class BacktestResultResponse(BaseModel):
    """백테스트 결과 응답"""
    id: str
    status: str
    statistics: BacktestResultStatistics
    trades: List[BacktestTrade]
    yield_points: List[BacktestYieldPoint]
    created_at: datetime
    completed_at: Optional[datetime]


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

        # 2. 전략 생성 (임시)
        strategy_id = str(uuid.uuid4())
        strategy = PortfolioStrategy(
            strategy_id=strategy_id,
            strategy_name=f"Backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="API로 생성된 백테스트 전략",
            strategy_type="FACTOR_BASED",
            universe_type="ALL",
            initial_capital=Decimal(str(request.initial_capital))
        )
        db.add(strategy)

        # 3. 매수 조건을 전략 팩터로 변환
        for idx, condition in enumerate(request.buy_conditions):
            factor = StrategyFactor(
                strategy_id=strategy_id,
                factor_id=condition.factor,
                usage_type="SCREENING" if condition.operator in ["GT", "LT", "EQ"] else "RANKING",
                operator=condition.operator,
                threshold_value=Decimal(str(condition.value)),
                weight=Decimal("1.0")
            )
            db.add(factor)

        # 4. 거래 규칙 생성
        trading_rule = TradingRule(
            strategy_id=strategy_id,
            rule_type="REBALANCE",
            # condition_type 필드 제거 - 모델에 없음
            rebalance_frequency=request.rebalance_frequency,
            max_positions=request.max_positions,
            position_sizing=request.position_sizing,
            stop_loss_pct=Decimal("10"),  # 기본 10% 손절
            commission_rate=Decimal("0.00015"),  # 0.015% 수수료
            tax_rate=Decimal("0.0023"),  # 0.23% 세금
            # 매수/매도 조건을 JSON으로 저장
            buy_condition=[{"factor": c.factor, "operator": c.operator, "value": c.value} for c in request.buy_conditions],
            sell_condition=[{"factor": c.factor, "operator": c.operator, "value": c.value} for c in request.sell_conditions]
        )
        db.add(trading_rule)

        # 5. 세션 생성
        session = SimulationSession(
            session_id=session_id,
            strategy_id=strategy_id,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=Decimal(str(request.initial_capital)),
            benchmark=request.benchmark,
            status="PENDING",
            progress=0,
            created_at=datetime.now()
        )
        db.add(session)

        await db.commit()

        # 6. 백그라운드에서 백테스트 실행 (asyncio.create_task 사용)
        asyncio.create_task(
            execute_backtest_wrapper(
                session_id,
                strategy_id,
                request.start_date,
                request.end_date,
                request.initial_capital,
                request.benchmark
            )
        )

        return BacktestResponse(
            backtest_id=session_id,
            status="pending",
            message="백테스트가 시작되었습니다",
            created_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
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
                initial_capital=float(session.initial_capital),
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
                "stock_name": stock_name_map.get(trade.stock_code, trade.stock_code),
                "stock_code": trade.stock_code,
                "buy_price": float(buy_trade.price) if buy_trade else 0.0,
                "sell_price": float(trade.price),
                "profit": float(trade.realized_pnl),
                "profit_rate": float(trade.return_pct) if trade.return_pct else 0.0,
                "buy_date": buy_trade.trade_date.isoformat() if buy_trade else "",
                "sell_date": trade.trade_date.isoformat(),
                "weight": float(trade.amount / session.initial_capital * 100) if session.initial_capital else 0.0,
                "valuation": float(trade.amount)
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


@router.get("/sub_factors/list")
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