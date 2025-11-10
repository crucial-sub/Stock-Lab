"""
GenPort 스타일 백테스트 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal

from app.core.database import get_db
from app.services.backtest import GenPortBacktestEngine
from app.schemas.backtest_genport import (
    BacktestResultGenPort,
    BacktestCreateRequest,
    BacktestListResponse,
    BacktestListItem,
    FactorListResponse,
    FactorInfo
)
from app.models.backtest_genport import BacktestSession

router = APIRouter()


@router.get("/factors", response_model=FactorListResponse)
async def get_available_factors():
    """
    사용 가능한 팩터 목록 조회

    백테스트 조건 설정 시 사용할 수 있는 모든 팩터의 목록을 반환합니다.
    """

    factors = [
        # 가치 팩터
        FactorInfo(
            code="PER",
            name="PER (주가수익비율)",
            category="VALUE",
            description="시가총액 / 당기순이익. 낮을수록 저평가",
            data_source="price + financial",
            recommended_operator="<",
            typical_range="5-30"
        ),
        FactorInfo(
            code="PBR",
            name="PBR (주가순자산비율)",
            category="VALUE",
            description="시가총액 / 자본총계. 낮을수록 저평가",
            data_source="price + financial",
            recommended_operator="<",
            typical_range="0.5-3"
        ),
        FactorInfo(
            code="DIV_YIELD",
            name="배당수익률",
            category="VALUE",
            description="연간 배당금 / 현재가. 높을수록 좋음",
            data_source="financial",
            recommended_operator=">",
            typical_range="1-5%"
        ),

        # 수익성 팩터
        FactorInfo(
            code="ROE",
            name="ROE (자기자본이익률)",
            category="PROFITABILITY",
            description="당기순이익 / 자본총계 × 100. 높을수록 좋음",
            data_source="financial",
            recommended_operator=">",
            typical_range="5-20%"
        ),
        FactorInfo(
            code="ROA",
            name="ROA (총자산이익률)",
            category="PROFITABILITY",
            description="당기순이익 / 총자산 × 100. 높을수록 좋음",
            data_source="financial",
            recommended_operator=">",
            typical_range="3-15%"
        ),

        # 성장성 팩터
        FactorInfo(
            code="REVENUE_GROWTH",
            name="매출 성장률",
            category="GROWTH",
            description="YoY 매출액 증가율. 높을수록 좋음",
            data_source="financial",
            recommended_operator=">",
            typical_range="5-30%"
        ),
        FactorInfo(
            code="EARNINGS_GROWTH",
            name="이익 성장률",
            category="GROWTH",
            description="YoY 당기순이익 증가율. 높을수록 좋음",
            data_source="financial",
            recommended_operator=">",
            typical_range="10-50%"
        ),

        # 모멘텀 팩터
        FactorInfo(
            code="MOMENTUM_1M",
            name="1개월 모멘텀",
            category="MOMENTUM",
            description="최근 1개월(20일) 수익률",
            data_source="price",
            recommended_operator=">",
            typical_range="-10 ~ 10%"
        ),
        FactorInfo(
            code="MOMENTUM_3M",
            name="3개월 모멘텀",
            category="MOMENTUM",
            description="최근 3개월(60일) 수익률",
            data_source="price",
            recommended_operator=">",
            typical_range="-20 ~ 20%"
        ),
        FactorInfo(
            code="MOMENTUM_6M",
            name="6개월 모멘텀",
            category="MOMENTUM",
            description="최근 6개월(120일) 수익률",
            data_source="price",
            recommended_operator=">",
            typical_range="-30 ~ 30%"
        ),
        FactorInfo(
            code="MOMENTUM_12M",
            name="12개월 모멘텀",
            category="MOMENTUM",
            description="최근 12개월(240일) 수익률",
            data_source="price",
            recommended_operator=">",
            typical_range="-50 ~ 50%"
        ),

        # 변동성 팩터
        FactorInfo(
            code="VOLATILITY",
            name="변동성",
            category="VOLATILITY",
            description="60일 연환산 변동성. 낮을수록 안정적",
            data_source="price",
            recommended_operator="<",
            typical_range="10-50%"
        ),

        # 유동성 팩터
        FactorInfo(
            code="AVG_TRADING_VALUE",
            name="평균 거래대금",
            category="LIQUIDITY",
            description="20일 평균 거래대금. 높을수록 유동적",
            data_source="price",
            recommended_operator=">",
            typical_range="10억-1000억원"
        ),
        FactorInfo(
            code="TURNOVER_RATE",
            name="회전율",
            category="LIQUIDITY",
            description="거래량 / 상장주식수 × 100",
            data_source="price",
            recommended_operator=">",
            typical_range="0.1-5%"
        ),
    ]

    return FactorListResponse(
        factors=factors,
        total=len(factors)
    )


@router.post("/backtest", response_model=BacktestResultGenPort)
async def create_backtest(
    request: BacktestCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 생성 및 실행

    사용자가 설정한 조건으로 백테스트를 실행하고 결과를 반환합니다.
    """

    # 백테스트 ID 생성
    backtest_id = uuid4()

    # 백테스트 엔진 초기화
    engine = GenPortBacktestEngine(db)

    # 백테스트 실행
    try:
        result = await engine.run_backtest(
            backtest_id=backtest_id,
            buy_conditions=[c.dict() for c in request.buy_conditions],
            sell_conditions=[c.dict() for c in request.sell_conditions],
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            rebalance_frequency=request.rebalance_frequency,
            max_positions=request.max_positions,
            position_sizing=request.position_sizing,
            benchmark=request.benchmark,
            commission_rate=request.commission_rate,
            slippage=request.slippage
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"백테스트 실행 중 오류 발생: {str(e)}"
        )


@router.get("/backtest", response_model=BacktestListResponse)
async def list_backtests(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="상태 필터 (COMPLETED/FAILED)"),
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 목록 조회

    과거에 실행한 백테스트 목록을 페이지네이션하여 반환합니다.
    """

    from sqlalchemy import select, func, desc
    from app.models.backtest_genport import BacktestSession, BacktestStatistics

    # 기본 쿼리
    query = select(BacktestSession)

    # 상태 필터
    if status:
        query = query.where(BacktestSession.status == status)

    # 총 개수 조회
    count_query = select(func.count()).select_from(BacktestSession)
    if status:
        count_query = count_query.where(BacktestSession.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 페이지네이션
    offset = (page - 1) * page_size
    query = query.order_by(desc(BacktestSession.created_at)).offset(offset).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    # 각 세션의 통계 조회
    items = []
    for session in sessions:
        # 통계 조회
        stat_query = select(BacktestStatistics).where(
            BacktestStatistics.backtest_id == session.backtest_id
        )
        stat_result = await db.execute(stat_query)
        stats = stat_result.scalar_one_or_none()

        items.append(BacktestListItem(
            backtest_id=str(session.backtest_id),
            backtest_name=session.backtest_name,
            created_at=session.created_at,
            status=session.status,
            total_return=stats.total_return if stats else None,
            max_drawdown=stats.max_drawdown if stats else None,
            sharpe_ratio=stats.sharpe_ratio if stats else None,
            start_date=session.start_date,
            end_date=session.end_date
        ))

    return BacktestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/backtest/{backtest_id}", response_model=BacktestResultGenPort)
async def get_backtest(
    backtest_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 상세 조회

    특정 백테스트의 전체 결과를 조회합니다.
    """

    from app.models.backtest_genport import (
        BacktestSession, BacktestStatistics, BacktestCondition,
        BacktestDailySnapshot, BacktestTrade, BacktestHolding
    )
    from app.schemas.backtest_genport import (
        BacktestSettings, BacktestCondition as ConditionSchema,
        BacktestStatistics as StatsSchema, DailyPerformance,
        TradeRecord, PortfolioHolding, MonthlyPerformance, YearlyPerformance
    )
    import pandas as pd
    from collections import defaultdict

    # 세션 조회
    session_query = select(BacktestSession).where(
        BacktestSession.backtest_id == backtest_id
    )
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # 통계 조회
    stats_query = select(BacktestStatistics).where(
        BacktestStatistics.backtest_id == backtest_id
    )
    stats_result = await db.execute(stats_query)
    statistics = stats_result.scalar_one_or_none()

    if not statistics:
        raise HTTPException(status_code=404, detail="백테스트 통계를 찾을 수 없습니다")

    # 조건 조회
    conditions_query = select(BacktestCondition).where(
        BacktestCondition.backtest_id == backtest_id
    )
    conditions_result = await db.execute(conditions_query)
    conditions = conditions_result.scalars().all()

    buy_conditions = []
    sell_conditions = []
    for c in conditions:
        condition_data = ConditionSchema(
            factor=c.factor,
            operator=c.operator,
            value=float(c.value),
            description=c.description
        )
        if c.condition_type == "BUY":
            buy_conditions.append(condition_data)
        else:
            sell_conditions.append(condition_data)

    # 일별 스냅샷 조회
    snapshots_query = select(BacktestDailySnapshot).where(
        BacktestDailySnapshot.backtest_id == backtest_id
    ).order_by(BacktestDailySnapshot.snapshot_date)
    snapshots_result = await db.execute(snapshots_query)
    snapshots = snapshots_result.scalars().all()

    daily_performance = [
        DailyPerformance(
            date=s.snapshot_date,
            portfolio_value=s.portfolio_value,
            cash_balance=s.cash_balance,
            invested_amount=s.invested_amount,
            daily_return=s.daily_return,
            cumulative_return=s.cumulative_return,
            drawdown=s.drawdown,
            benchmark_return=s.benchmark_return,
            trade_count=s.trade_count
        )
        for s in snapshots
    ]

    # 월별 성과 집계
    monthly_performance = []
    if daily_performance:
        df = pd.DataFrame([{
            'date': d.date,
            'cumulative_return': float(d.cumulative_return),
            'trade_count': d.trade_count
        } for d in daily_performance])
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month

        for (year, month), group in df.groupby(['year', 'month']):
            first_return = group.iloc[0]['cumulative_return']
            last_return = group.iloc[-1]['cumulative_return']
            month_return = last_return - first_return

            monthly_performance.append(MonthlyPerformance(
                year=int(year),
                month=int(month),
                return_rate=Decimal(str(month_return)),
                benchmark_return=None,
                win_rate=Decimal("0"),
                trade_count=group['trade_count'].sum(),
                avg_hold_days=0
            ))

    # 연도별 성과 집계
    yearly_performance = []
    if daily_performance:
        for year, year_group in df.groupby('year'):
            first_return = year_group.iloc[0]['cumulative_return']
            last_return = year_group.iloc[-1]['cumulative_return']
            year_return = last_return - first_return

            yearly_performance.append(YearlyPerformance(
                year=int(year),
                return_rate=Decimal(str(year_return)),
                benchmark_return=None,
                max_drawdown=Decimal("0"),
                sharpe_ratio=Decimal("0"),
                trades=year_group['trade_count'].sum()
            ))

    # 거래 내역 조회
    trades_query = select(BacktestTrade).where(
        BacktestTrade.backtest_id == backtest_id
    ).order_by(BacktestTrade.trade_date)
    trades_result = await db.execute(trades_query)
    trades = trades_result.scalars().all()

    trade_records = [
        TradeRecord(
            trade_id=str(t.trade_id),
            trade_date=t.trade_date,
            trade_type=t.trade_type,
            stock_code=t.stock_code,
            stock_name=t.stock_name,
            quantity=t.quantity,
            price=t.price,
            amount=t.amount,
            commission=t.commission,
            tax=t.tax,
            profit=t.profit,
            profit_rate=t.profit_rate,
            hold_days=t.hold_days,
            factors=t.factors or {},
            selection_reason=t.selection_reason
        )
        for t in trades
    ]

    # 보유 종목 조회
    holdings_query = select(BacktestHolding).where(
        BacktestHolding.backtest_id == backtest_id
    )
    holdings_result = await db.execute(holdings_query)
    holdings = holdings_result.scalars().all()

    current_holdings = [
        PortfolioHolding(
            stock_code=h.stock_code,
            stock_name=h.stock_name,
            quantity=h.quantity,
            avg_price=h.avg_price,
            current_price=h.current_price,
            value=h.value,
            profit=h.profit,
            profit_rate=h.profit_rate,
            weight=h.weight,
            buy_date=h.buy_date,
            hold_days=h.hold_days,
            factors=h.factors or {}
        )
        for h in holdings
    ]

    # 차트 데이터 생성
    chart_data = {}
    if daily_performance:
        chart_data = {
            'dates': [d.date.isoformat() for d in daily_performance],
            'portfolio_values': [float(d.portfolio_value) for d in daily_performance],
            'cash_balances': [float(d.cash_balance) for d in daily_performance],
            'cumulative_returns': [float(d.cumulative_return) for d in daily_performance],
            'drawdowns': [float(d.drawdown) for d in daily_performance]
        }

    # 결과 조합
    result = BacktestResultGenPort(
        backtest_id=str(session.backtest_id),
        backtest_name=session.backtest_name,
        status=session.status,
        created_at=session.created_at,
        completed_at=session.completed_at,
        settings=BacktestSettings(
            rebalance_frequency=session.rebalance_frequency,
            max_positions=session.max_positions,
            position_sizing=session.position_sizing,
            benchmark=session.benchmark,
            commission_rate=float(session.commission_rate),
            tax_rate=float(session.tax_rate),
            slippage=float(session.slippage)
        ),
        buy_conditions=buy_conditions,
        sell_conditions=sell_conditions,
        statistics=StatsSchema(
            total_return=statistics.total_return,
            annualized_return=statistics.annualized_return,
            benchmark_return=statistics.benchmark_return,
            excess_return=statistics.excess_return,
            max_drawdown=statistics.max_drawdown,
            volatility=statistics.volatility,
            downside_volatility=statistics.downside_volatility,
            sharpe_ratio=statistics.sharpe_ratio,
            sortino_ratio=statistics.sortino_ratio,
            calmar_ratio=statistics.calmar_ratio,
            total_trades=statistics.total_trades,
            winning_trades=statistics.winning_trades,
            losing_trades=statistics.losing_trades,
            win_rate=statistics.win_rate,
            avg_win=statistics.avg_win,
            avg_loss=statistics.avg_loss,
            profit_loss_ratio=statistics.profit_loss_ratio,
            initial_capital=statistics.initial_capital,
            final_capital=statistics.final_capital,
            peak_capital=statistics.peak_capital,
            start_date=statistics.start_date,
            end_date=statistics.end_date,
            trading_days=statistics.trading_days
        ),
        current_holdings=current_holdings,
        daily_performance=daily_performance,
        monthly_performance=monthly_performance,
        yearly_performance=yearly_performance,
        trades=trade_records,
        rebalance_dates=[],  # 별도 테이블이 없어서 빈 리스트
        chart_data=chart_data
    )

    return result


@router.delete("/backtest/{backtest_id}")
async def delete_backtest(
    backtest_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    백테스트 삭제

    특정 백테스트와 관련된 모든 데이터를 삭제합니다.
    """

    from app.models.backtest_genport import BacktestSession

    # 세션 조회
    query = select(BacktestSession).where(
        BacktestSession.backtest_id == backtest_id
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    # CASCADE 삭제 (관련 테이블 자동 삭제)
    await db.delete(session)
    await db.commit()

    return {"message": "백테스트가 삭제되었습니다", "backtest_id": str(backtest_id)}


@router.get("/settings/defaults")
async def get_default_settings():
    """
    기본 백테스트 설정 조회

    백테스트 생성 시 사용할 기본값들을 반환합니다.
    """

    return {
        "initial_capital": 100000000,  # 1억원
        "rebalance_frequency": "MONTHLY",
        "max_positions": 20,
        "position_sizing": "EQUAL_WEIGHT",
        "benchmark": "KOSPI",
        "commission_rate": 0.00015,  # 0.015%
        "slippage": 0.001,  # 0.1%
        "rebalance_frequencies": [
            {"value": "DAILY", "label": "일별"},
            {"value": "WEEKLY", "label": "주별 (월요일)"},
            {"value": "MONTHLY", "label": "월별 (첫 거래일)"},
            {"value": "QUARTERLY", "label": "분기별"}
        ],
        "position_sizing_methods": [
            {"value": "EQUAL_WEIGHT", "label": "동일 가중"},
            {"value": "MARKET_CAP", "label": "시가총액 가중"},
            {"value": "RISK_PARITY", "label": "리스크 패리티"}
        ],
        "benchmarks": [
            {"value": "KOSPI", "label": "KOSPI"},
            {"value": "KOSDAQ", "label": "KOSDAQ"},
            {"value": "KOSPI200", "label": "KOSPI200"}
        ],
        "operators": [
            {"value": ">", "label": "크다 (>)"},
            {"value": "<", "label": "작다 (<)"},
            {"value": ">=", "label": "크거나 같다 (≥)"},
            {"value": "<=", "label": "작거나 같다 (≤)"}
        ],
        "sell_condition_types": [
            {"value": "STOP_LOSS", "label": "손절", "description": "손실률 기준 자동 매도"},
            {"value": "TAKE_PROFIT", "label": "익절", "description": "수익률 기준 자동 매도"},
            {"value": "HOLD_DAYS", "label": "보유기간", "description": "보유일수 초과 시 자동 매도"}
        ]
    }
