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

from app.core.dependencies import get_current_user
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
from app.models.user import User
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
    min_momentum_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        alias="minMomentumScore",
        serialization_alias="minMomentumScore",
        description="필터에 사용할 최소 모멘텀 점수"
    )
    min_fundamental_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        alias="minFundamentalScore",
        serialization_alias="minFundamentalScore",
        description="필터에 사용할 최소 펀더멘털 점수"
    )

    # 공개 설정 (선택 사항)
    is_public: Optional[bool] = False
    is_anonymous: Optional[bool] = False
    hide_strategy_details: Optional[bool] = False


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
    sharpe_ratio: float = Field(..., serialization_alias="sharpeRatio")
    win_rate: float = Field(..., serialization_alias="winRate")
    profit_factor: float = Field(..., serialization_alias="profitFactor")
    total_trades: int = Field(..., serialization_alias="totalTrades")
    winning_trades: int = Field(..., serialization_alias="winningTrades")
    losing_trades: int = Field(..., serialization_alias="losingTrades")
    initial_capital: int = Field(..., serialization_alias="initialCapital")
    final_capital: int = Field(..., serialization_alias="finalCapital")


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
    """백테스트 일별 포트폴리오 데이터"""
    model_config = ConfigDict(populate_by_name=True)

    date: str
    portfolio_value: int = Field(..., serialization_alias="portfolioValue")  # 포트폴리오 총 가치
    cash: int  # 현금 잔고
    position_value: int = Field(..., serialization_alias="positionValue")  # 보유 포지션 가치
    daily_return: float = Field(..., serialization_alias="dailyReturn")  # 일간 수익률
    cumulative_return: float = Field(..., serialization_alias="cumulativeReturn")  # 누적 수익률
    value: float  # 차트용 (cumulative_return과 동일, 하위 호환성)


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
    current_user: User = Depends(get_current_user),
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
            description=f"User: {current_user.user_id}, Target: {', '.join(request.target_stocks[:3])}{'...' if len(request.target_stocks) > 3 else ''}",
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

        # 6. 매수 조건을 파싱하여 StrategyFactor로 저장
        import re
        logger.info(f"매수 조건 파싱 시작: {len(request.buy_conditions)}개 조건")
        for condition in request.buy_conditions:
            logger.info(f"조건 파싱 중: {condition.name} = {condition.expression}")
            # expression 예: "{주가순자산률 (PBR)} >= 10" 또는 "{PER} < 30"
            # 정규식으로 팩터 이름과 연산자, 값 추출
            # 한글, 영문, 괄호 등을 포함한 팩터 이름 추출
            match = re.match(r'\{([^}]+)\}\s*([<>=!]+)\s*([0-9.]+)', condition.expression)
            if match:
                full_factor_name = match.group(1)  # e.g., "주가순자산률 (PBR)" or "PER"
                operator = match.group(2)  # e.g., "<", ">", "=="
                threshold = match.group(3)  # e.g., "30"

                # 괄호 안의 영문 코드 추출 (예: "주가순자산률 (PBR)" -> "PBR")
                code_match = re.search(r'\(([A-Z_]+)\)', full_factor_name)
                if code_match:
                    factor_name = code_match.group(1)
                else:
                    # 괄호가 없으면 전체 이름 사용 (공백 제거)
                    factor_name = full_factor_name.strip()

                logger.info(f"추출된 팩터: {factor_name}, 연산자: {operator}, 임계값: {threshold}")

                # Factor 테이블에서 factor_id 조회
                from app.models.simulation import Factor
                factor_query = select(Factor).where(Factor.factor_id == factor_name)
                factor_result = await db.execute(factor_query)
                factor = factor_result.scalar_one_or_none()

                if not factor:
                    # Factor가 없으면 생성 (기본 카테고리: value)
                    factor = Factor(
                        factor_id=factor_name,
                        category_id="value",  # 기본값: 가치 팩터
                        factor_name=factor_name,
                        calculation_type="FUNDAMENTAL",
                        description=f"Auto-created factor from user condition"
                    )
                    db.add(factor)
                    await db.flush()  # factor_id를 얻기 위해 flush

                # StrategyFactor 생성
                strategy_factor = StrategyFactor(
                    strategy_id=strategy_id,
                    factor_id=factor_name,
                    usage_type="SCREENING",  # 스크리닝용
                    operator=operator.replace("<", "LT").replace(">", "GT").replace("==", "EQ"),
                    threshold_value=threshold,
                    weight=Decimal("1.0"),
                    direction="POSITIVE"
                )
                db.add(strategy_factor)
                logger.info(f"StrategyFactor 추가됨: {factor_name}")

        # 우선순위 팩터도 추가 (정렬용)
        if request.priority_factor and request.priority_factor != "없음":
            priority_factor_query = select(Factor).where(Factor.factor_id == request.priority_factor)
            priority_factor_result = await db.execute(priority_factor_query)
            priority_factor = priority_factor_result.scalar_one_or_none()

            if not priority_factor:
                priority_factor = Factor(
                    factor_id=request.priority_factor,
                    factor_name=request.priority_factor,
                    calculation_type="FUNDAMENTAL",
                    description=f"Priority factor"
                )
                db.add(priority_factor)
                await db.flush()

            priority_strategy_factor = StrategyFactor(
                strategy_id=strategy_id,
                factor_id=request.priority_factor,
                usage_type="SCORING",  # 점수 계산용
                weight=Decimal("1.0"),
                direction="POSITIVE" if request.priority_order == "desc" else "NEGATIVE"
            )
            db.add(priority_strategy_factor)

        # 7. 세션 생성
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
        logger.info(f"Start date: {start_date}, End date: {end_date}, Initial capital: {initial_capital}")
        logger.info(f"Target stocks (테마): {request.target_stocks}")
        asyncio.create_task(
            execute_backtest_wrapper(
                session_id,
                strategy_id,
                start_date,
                end_date,
                initial_capital,
                "KOSPI",
                request.target_stocks,  # 테마 목록 전달
                request.min_momentum_score,
                request.min_fundamental_score
            )
        )

        return BacktestResponse(
            backtest_id=session_id,
            status="pending",
            message="백테스트가 시작되었습니다",
            created_at=datetime.now()
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
            portfolio_value=int(dv.portfolio_value) if dv.portfolio_value else 0,
            cash=int(dv.cash) if dv.cash else 0,
            position_value=int(dv.position_value) if dv.position_value else 0,
            daily_return=float(dv.daily_return) if dv.daily_return else 0,
            cumulative_return=float(dv.cumulative_return) if dv.cumulative_return else 0,
            value=float(dv.cumulative_return) if dv.cumulative_return else 0  # 차트용 (하위 호환성)
        )
        for dv in daily_values
    ]

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
            "buyPrice": float(buy_trade.price) if buy_trade else 0.0,
            "sellPrice": float(sell_trade.price),
            "profit": float(sell_trade.realized_pnl),
            "profitRate": float(sell_trade.return_pct) if sell_trade.return_pct else 0.0,
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
    benchmark: str,
    target_stocks: List[str],
    min_momentum_score: Optional[float] = None,
    min_fundamental_score: Optional[float] = None
):
    """백테스트 비동기 실행 래퍼 (고도화된 백테스트 용)"""
    try:
        from app.services.advanced_backtest import run_advanced_backtest

        import asyncio
        loop = asyncio.get_event_loop()

        await loop.run_in_executor(
            None,
            run_advanced_backtest,
            session_id,
            strategy_id,
            start_date,
            end_date,
            Decimal(str(initial_capital)),
            benchmark,
            target_stocks,
            min_momentum_score,
            min_fundamental_score
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
            # 예시: {"id": 1, "name": "per", "display_name": "주가수익비율", "category": "value", "description": "Price to Earnings Ratio"}
            {"id": 1, "name": "per", "display_name": "주가수익비율", "category": "value", "description": "Price to Earnings Ratio"},
            {"id": 2, "name": "pbr", "display_name": "주가순자산비율", "category": "value", "description": "Price to Book Ratio"},
            {"id": 3, "name": "roe", "display_name": "자기자본이익률", "category": "profitability", "description": "Return on Equity"},
            {"id": 4, "name": "roa", "display_name": "총자산이익률", "category": "profitability", "description": "Return on Assets"},
            {"id": 5, "name": "revenue_growth", "display_name": "매출성장률", "category": "growth", "description": "Revenue Growth Rate"},
            {"id": 6, "name": "earnings_growth", "display_name": "이익성장률", "category": "growth", "description": "Earnings Growth Rate"},
            {"id": 7, "name": "debt_ratio", "display_name": "부채비율", "category": "stability", "description": "Debt to Equity Ratio"},
            {"id": 8, "name": "current_ratio", "display_name": "유동비율", "category": "stability", "description": "Current Ratio"},
            {"id": 9, "name": "momentum_1m", "display_name": "1개월 모멘텀", "category": "momentum", "description": "1 Month Price Momentum"},
            {"id": 10, "name": "momentum_3m", "display_name": "3개월 모멘텀", "category": "momentum", "description": "3 Month Price Momentum"},
            {"id": 11, "name": "momentum_6m", "display_name": "6개월 모멘텀", "category": "momentum", "description": "6 Month Price Momentum"},
            {"id": 12, "name": "momentum_12m", "display_name": "12개월 모멘텀", "category": "momentum", "description": "12 Month Price Momentum"},
            {"id": 13, "name": "volatility", "display_name": "변동성", "category": "risk", "description": "Price Volatility"},
            {"id": 14, "name": "trading_volume", "display_name": "거래량", "category": "liquidity", "description": "Trading Volume"},
            {"id": 15, "name": "market_cap", "display_name": "시가총액", "category": "size", "description": "Market Capitalization"},
            {"id": 16, "name": "div_yield", "display_name": "배당수익률", "category": "value", "description": "Dividend Yield"},
            {"id": 17, "name": "ev_ebitda", "display_name": "EV/EBITDA", "category": "value", "description": "Enterprise Value to EBITDA"},
            {"id": 18, "name": "gp_a", "display_name": "매출총이익률", "category": "quality", "description": "Gross Profitability"},
            {"id": 19, "name": "beta", "display_name": "베타", "category": "risk", "description": "Market Beta"},
            {"id": 20, "name": "rsi", "display_name": "RSI", "category": "technical", "description": "Relative Strength Index"}
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
    return {
        "themes": [
            # 예시: {"id": 1, "name": "construction", "display_name": "건설"}
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
            {"id": 29, "name": "it_service", "display_name": "IT서비스"},
        ]
    }
