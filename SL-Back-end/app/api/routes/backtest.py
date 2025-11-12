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
from uuid import UUID
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
    buy_date: str = Field(..., serialization_alias="buyDate")
    sell_date: str = Field(..., serialization_alias="sellDate")
    weight: float = Field(..., serialization_alias="weight")
    valuation: float = Field(..., serialization_alias="valuation")
    quantity: int = Field(..., serialization_alias="quantity")


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
    buy_count: int = Field(default=0, serialization_alias="buyCount")  # 당일 매수 횟수
    sell_count: int = Field(default=0, serialization_alias="sellCount")  # 당일 매도 횟수


class BacktestResultResponse(BaseModel):
    """백테스트 결과 응답"""
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
        logger.info(f"🔍 받은 날짜 - start_date: {request.start_date}, end_date: {request.end_date}")
        start_date = dt.strptime(request.start_date, "%Y%m%d").date()
        end_date = dt.strptime(request.end_date, "%Y%m%d").date()
        logger.info(f"🔍 파싱된 날짜 - start_date: {start_date}, end_date: {end_date}")

        # 3. 투자 금액 변환 (만원 -> 원)
        initial_capital = Decimal(str(request.initial_investment * 10000))

        # 4. 전략 생성
        strategy_id = str(uuid.uuid4())

        # 선택된 매매 대상 문자열 생성
        targets_str = "전체 종목" if request.trade_targets.use_all_stocks else f"{', '.join(request.trade_targets.selected_themes[:3])}{'...' if len(request.trade_targets.selected_themes) > 3 else ''}"

        strategy = PortfolioStrategy(
            strategy_id=strategy_id,
            strategy_name=request.strategy_name,
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
                "buy_price_offset": request.buy_price_offset
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
        logger.info(f"매수 조건 파싱 시작: {len(request.buy_conditions)}개 조건")
        for condition in request.buy_conditions:
            # BuyCondition 모델은 이미 분리된 필드를 가지고 있음
            # exp_left_side: 조건식 좌변 (e.g., "이동평균({PER},{20일})")
            # inequality: 부등호 (e.g., ">")
            # exp_right_side: 조건식 우변 (e.g., 10)
            expression_str = f"{condition.exp_left_side} {condition.inequality} {condition.exp_right_side}"
            logger.info(f"조건 파싱 중: {condition.name} = {expression_str}")

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

                logger.info(f"추출된 팩터: {factor_name}, 연산자: {operator}, 임계값: {threshold}")

                # Factor 테이블에서 factor_id 조회 (대소문자 구분 없이)
                from app.models.simulation import Factor
                from sqlalchemy import func
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
                logger.info(f"StrategyFactor 추가됨: {factor.factor_id} (입력값: {factor_name})")

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

        # 7. 세션 생성 (admin 사용자 UUID 사용)
        admin_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')  # admin 사용자

        session = SimulationSession(
            session_id=session_id,
            strategy_id=strategy_id,
            user_id=admin_user_id,  # admin 사용자 ID 추가
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
        logger.info(f"Trade targets: {request.trade_targets.model_dump()}")

        # 매매 대상 결정: use_all_stocks이면 빈 리스트, 아니면 선택된 테마/종목
        selected_theme_codes = [] if request.trade_targets.use_all_stocks else request.trade_targets.selected_themes
        target_themes = [
            THEME_CODE_TO_INDUSTRY.get(code, code) for code in selected_theme_codes
        ]
        target_stocks = [] if request.trade_targets.use_all_stocks else request.trade_targets.selected_stocks

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
                request.trade_targets.use_all_stocks,  # 전체 종목 사용 여부
                [c.model_dump() for c in request.buy_conditions],  # 매수 조건
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
                request.max_daily_stock
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

    return BacktestStatusResponse(
        backtest_id=session.session_id,
        status=session.status.lower() if session.status else "pending",
        progress=session.progress or 0,
        message=f"진행률: {session.progress}%",
        started_at=session.started_at,
        completed_at=session.completed_at,
        error_message=session.error_message,
        start_date=session.start_date.strftime("%Y-%m-%d") if session.start_date else None,
        end_date=session.end_date.strftime("%Y-%m-%d") if session.end_date else None,
        current_date=session.current_date.isoformat() if session.current_date else None,
        buy_count=session.buy_count or 0,
        sell_count=session.sell_count or 0,
        current_return=float(session.current_return) if session.current_return else None,
        current_capital=float(session.current_capital) if session.current_capital else None,
        current_mdd=float(session.current_mdd) if session.current_mdd else None,
        yield_points=None
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

            trade_list.append(BacktestTrade(
                stock_name=trade.stock_name,  # 이미 테이블에 저장되어 있음
                stock_code=trade.stock_code,
                buy_price=float(buy_trade.price) if buy_trade else 0,
                sell_price=float(trade.price),
                profit=float(trade.profit) if trade.profit else 0,
                profit_rate=float(trade.profit_rate) if trade.profit_rate else 0,
                buy_date=buy_trade.trade_date.isoformat() if buy_trade else "",
                sell_date=trade.trade_date.isoformat(),
                weight=float(amount / initial_capital * 100) if initial_capital > 0 else 0,
                valuation=int(amount),  # 소수점 제거
                quantity=int(trade.quantity) if trade.quantity else 0
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

    # 수익률 포인트 변환 (매수/매도 횟수 포함)
    yield_points = [
        {
            "date": snap.snapshot_date.isoformat(),
            "portfolio_value": int(snap.portfolio_value),
            "cash": int(snap.cash_balance),
            "position_value": int(snap.invested_amount),
            "daily_return": float(snap.daily_return),
            "cumulative_return": float(snap.cumulative_return),
            "value": float(snap.cumulative_return),
            "buy_count": daily_trade_counts[snap.snapshot_date.isoformat()]["buy"],
            "sell_count": daily_trade_counts[snap.snapshot_date.isoformat()]["sell"]
        }
        for snap in snapshots
    ]

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
        created_at=session.created_at,
        completed_at=session.completed_at  # completed_at 사용 (updated_at 없음)
    )


@router.get("/backtest/{backtest_id}/result", response_model=BacktestResultResponse)
async def get_backtest_result(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 결과 조회"""
    # BacktestSession (새로운 백테스트)에서 먼저 확인
    from app.models.backtest import BacktestStatistics as NewBacktestStatistics, BacktestDailySnapshot, BacktestTrade as NewBacktestTrade

    backtest_query = select(BacktestSession).where(BacktestSession.backtest_id == backtest_id)
    backtest_result = await db.execute(backtest_query)
    backtest_session = backtest_result.scalar_one_or_none()

    if backtest_session:
        # 새로운 백테스트 결과 처리
        return await _get_new_backtest_result(db, backtest_id, backtest_session)

    # 1. 기존 SimulationSession 확인
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
                buy_date=buy_trade.trade_date.isoformat() if buy_trade else "",
                sell_date=trade.trade_date.isoformat(),
                weight=float(amount / initial_capital * 100) if initial_capital > 0 else 0,
                valuation=amount,
                quantity=int(trade.quantity) if trade.quantity else 0
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
    target_themes: List[str],  # 선택된 산업/테마 목록
    target_stocks: List[str],  # 선택된 개별 종목 코드 목록
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
    max_daily_stock: Optional[int] = None
):
    """백테스트 비동기 실행 래퍼 (고도화된 백테스트 용)"""
    try:
        from app.services.advanced_backtest import run_advanced_backtest
        from functools import partial

        import asyncio
        loop = asyncio.get_event_loop()

        # partial을 사용하여 모든 인자를 전달
        func = partial(
            run_advanced_backtest,
            session_id,
            strategy_id,
            start_date,
            end_date,
            Decimal(str(initial_capital)),
            benchmark,
            target_themes,
            target_stocks,
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

        await loop.run_in_executor(None, func)

        logger.info(f"백테스트 완료: {session_id}")

    except Exception as e:
        logger.error(f"백테스트 래퍼 오류: {e}", exc_info=True)


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

                # 안정성 지표 (STABILITY) - 8개
                {"id": 41, "name": "debt_to_equity", "display_name": "부채비율", "category": "안정성", "description": "부채총계를 자기자본으로 나눈 비율"},
                {"id": 42, "name": "debt_ratio", "display_name": "부채비율(%)", "category": "안정성", "description": "부채총계를 총자산으로 나눈 비율"},
                {"id": 43, "name": "current_ratio", "display_name": "유동비율", "category": "안정성", "description": "유동자산을 유동부채로 나눈 비율"},
                {"id": 44, "name": "quick_ratio", "display_name": "당좌비율", "category": "안정성", "description": "당좌자산을 유동부채로 나눈 비율"},
                {"id": 45, "name": "interest_coverage", "display_name": "이자보상배율", "category": "안정성", "description": "영업이익을 이자비용으로 나눈 비율"},
                {"id": 46, "name": "altman_z_score", "display_name": "Altman Z-Score", "category": "안정성", "description": "파산 위험도 측정 지표"},
                {"id": 47, "name": "beta", "display_name": "베타", "category": "안정성", "description": "시장 대비 변동성"},
                {"id": 48, "name": "earnings_quality", "display_name": "이익품질", "category": "안정성", "description": "현금흐름 대비 순이익 비율"},

                # 기술적 지표 (TECHNICAL) - 6개
                {"id": 49, "name": "rsi_14", "display_name": "RSI(14)", "category": "기술적분석", "description": "14일 기준 상대강도지수 (0-100)"},
                {"id": 50, "name": "bollinger_position", "display_name": "볼린저밴드 위치", "category": "기술적분석", "description": "볼린저밴드 내 현재가 위치"},
                {"id": 51, "name": "macd_signal", "display_name": "MACD 시그널", "category": "기술적분석", "description": "MACD와 시그널선 차이"},
                {"id": 52, "name": "stochastic_14", "display_name": "스토캐스틱(14)", "category": "기술적분석", "description": "14일 기준 스토캐스틱 (0-100)"},
                {"id": 53, "name": "volume_roc", "display_name": "거래량 변화율", "category": "기술적분석", "description": "거래량 변화율"},
                {"id": 54, "name": "price_position", "display_name": "가격 위치", "category": "기술적분석", "description": "52주 범위 내 현재가 위치 (0-100)"},
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
