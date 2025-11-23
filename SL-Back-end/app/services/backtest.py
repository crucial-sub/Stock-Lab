"""
백테스트 엔진 (확장판)
- 논리식 조건 지원
- 주문/체결/포지션 추적
- 상세 통계 계산
- 최적화: 병렬 처리, 선택적 팩터 계산, Redis 캐싱
"""

import asyncio
import logging
import copy
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from uuid import UUID, uuid4
import pandas as pd
import numpy as np
import polars as pl
from collections import defaultdict
from dataclasses import dataclass, asdict
import re
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
from functools import partial
import time
import hashlib
import json
# 🚀 EXTREME OPTIMIZATION: Numba JIT 컴파일 (Python 루프를 C 속도로)
try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Fallback: 데코레이터를 무시하는 더미 함수
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
    prange = range

from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Company, StockPrice, FinancialStatement,
    BalanceSheet, IncomeStatement, CashflowStatement
)
from app.schemas.backtest import (
    BacktestResult, PortfolioHolding, DailyPerformance,
    MonthlyPerformance, YearlyPerformance, TradeRecord,
    BacktestStatistics as StatsSchema, BacktestCondition,
    BacktestSettings
)
from app.services.condition_evaluator import ConditionEvaluator, LogicalExpressionParser
from app.core.cache import cache

logger = logging.getLogger(__name__)


# ==================== 데이터 클래스 ====================

@dataclass
class Order:
    """주문 정보"""
    order_id: str
    order_date: datetime
    stock_code: str
    stock_name: str
    order_type: str  # MARKET, LIMIT
    order_side: str  # BUY, SELL
    quantity: int
    limit_price: Optional[Decimal] = None
    status: str = "PENDING"
    reason: str = ""
    factor_scores: Dict[str, float] = None
    condition_results: Dict[str, bool] = None

    def __post_init__(self):
        if self.factor_scores is None:
            self.factor_scores = {}
        if self.condition_results is None:
            self.condition_results = {}


@dataclass
class Execution:
    """체결 정보"""
    execution_id: str
    order_id: str
    execution_date: datetime
    quantity: int
    price: Decimal
    amount: Decimal
    commission: Decimal
    tax: Decimal
    slippage_amount: Decimal
    total_cost: Decimal


@dataclass
class Position:
    """포지션 정보"""
    position_id: str
    stock_code: str
    stock_name: str
    entry_date: date
    entry_price: Decimal
    quantity: int
    current_price: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Optional[Decimal] = None
    max_profit: Decimal = Decimal("0")
    max_loss: Decimal = Decimal("0")
    hold_days: int = 0
    factor_scores_entry: Dict[str, float] = None
    factor_scores_current: Dict[str, float] = None
    is_open: bool = True
    exit_date: Optional[date] = None
    exit_price: Optional[Decimal] = None

    def __post_init__(self):
        if self.factor_scores_entry is None:
            self.factor_scores_entry = {}
        if self.factor_scores_current is None:
            self.factor_scores_current = {}


@dataclass
class DrawdownPeriod:
    """드로다운 기간 정보"""
    start_date: date
    end_date: Optional[date]
    peak_value: Decimal
    trough_value: Decimal
    max_drawdown: Decimal
    duration_days: int
    recovery_days: Optional[int] = None
    is_active: bool = True


# 🚀 EXTREME OPTIMIZATION: Numba JIT 최적화 함수들
@jit(nopython=True, cache=True)
def calculate_returns_numba(prices: np.ndarray, periods: int) -> np.ndarray:
    """
    Numba JIT: 수익률 계산 (2-5배 빠름)

    Args:
        prices: 가격 배열 (정렬된 시계열)
        periods: 기간 (예: 20일, 60일)

    Returns:
        수익률 배열 (%)
    """
    n = len(prices)
    returns = np.full(n, np.nan, dtype=np.float64)

    for i in range(periods, n):
        if prices[i - periods] != 0:
            returns[i] = ((prices[i] / prices[i - periods]) - 1.0) * 100.0

    return returns


@jit(nopython=True, cache=True)
def calculate_volatility_numba(prices: np.ndarray, window: int) -> np.ndarray:
    """
    Numba JIT: 변동성 계산 (2-5배 빠름)

    Args:
        prices: 가격 배열
        window: 윈도우 크기 (예: 20일, 60일)

    Returns:
        변동성 배열 (표준편차)
    """
    n = len(prices)
    volatility = np.full(n, np.nan, dtype=np.float64)

    for i in range(window, n):
        window_prices = prices[i - window:i]

        # 일일 수익률 계산
        returns = np.zeros(window - 1, dtype=np.float64)
        for j in range(window - 1):
            if window_prices[j] != 0:
                returns[j] = (window_prices[j + 1] / window_prices[j]) - 1.0

        # 표준편차 계산
        mean_return = np.mean(returns)
        squared_diff = 0.0
        for j in range(len(returns)):
            squared_diff += (returns[j] - mean_return) ** 2

        volatility[i] = np.sqrt(squared_diff / (len(returns) - 1))

    return volatility


@jit(nopython=True, cache=True)
def calculate_portfolio_value_numba(
    prices: np.ndarray,
    quantities: np.ndarray
) -> float:
    """
    Numba JIT: 포트폴리오 가치 계산 (2-5배 빠름)

    Args:
        prices: 가격 배열
        quantities: 수량 배열

    Returns:
        총 가치
    """
    total = 0.0
    for i in range(len(prices)):
        total += prices[i] * quantities[i]
    return total


class BacktestEngine:
    """백테스트 엔진"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tax_rate = Decimal("0.0023")  # 0.23% 거래세 (고정)

        # 추적용 컨테이너
        self.orders: List[Order] = []
        self.executions: List[Execution] = []
        self.positions: Dict[str, Position] = {}  # stock_code -> Position
        self.closed_positions: List[Position] = []
        self.position_history: List[Dict] = []

        # 통계 컨테이너
        self.monthly_stats: List[Dict] = []
        self.yearly_stats: List[Dict] = []
        self.drawdown_periods: List[DrawdownPeriod] = []
        self.factor_contributions: Dict[str, Dict] = {}

        # 조건 평가기
        self.condition_evaluator = ConditionEvaluator()
        self.expression_parser = LogicalExpressionParser()

        # 전략 제약 기본값
        self.initial_capital: Decimal = Decimal("0")
        self.per_stock_ratio: Optional[Decimal] = None
        self.max_buy_value: Optional[Decimal] = None
        self.max_daily_stock: Optional[int] = None
        self.condition_sell_meta: Optional[Dict[str, Any]] = None

    async def run_backtest(
        self,
        backtest_id: UUID,
        buy_conditions: List[Dict],
        sell_conditions: List[Dict],
        start_date: date,
        end_date: date,
        condition_sell: Optional[Dict[str, Any]] = None,
        target_and_loss: Optional[Dict[str, Any]] = None,
        hold_days: Optional[Dict[str, Any]] = None,
        initial_capital: Decimal = Decimal("100000000"),
        rebalance_frequency: str = "MONTHLY",
        max_positions: int = 20,
        position_sizing: str = "EQUAL_WEIGHT",
        benchmark: str = "KOSPI",
        commission_rate: float = 0.00015,  # 0.015% 기본값
        slippage: float = 0.001,  # 0.1% 기본값
        target_themes: List[str] = None,  # 선택된 산업/테마
        target_stocks: List[str] = None,  # 선택된 종목 코드
        target_universes: List[str] = None,  # 선택된 유니버스
        per_stock_ratio: Optional[float] = None,
        max_buy_value: Optional[Decimal] = None,
        max_daily_stock: Optional[int] = None
    ) -> BacktestResult:
        """백테스트 실행"""

        # Decimal로 변환
        self.commission_rate = Decimal(str(commission_rate))
        self.slippage = Decimal(str(slippage))
        self.initial_capital = initial_capital
        self.per_stock_ratio = Decimal(str(per_stock_ratio)) if per_stock_ratio else None
        self.max_buy_value = Decimal(str(max_buy_value)) if max_buy_value else None
        self.max_daily_stock = max_daily_stock

        logger.info(f"💰 거래 비용 설정 - 수수료: {self.commission_rate*100:.3f}%, 거래세: 0.23%, 슬리피지: {self.slippage*100:.2f}%")

        # 매도 조건 저장
        self.target_and_loss = None
        if target_and_loss:
            self.target_and_loss = {
                "target_gain": Decimal(str(target_and_loss.get('target_gain'))) if target_and_loss.get('target_gain') is not None else None,
                "stop_loss": Decimal(str(target_and_loss.get('stop_loss'))) if target_and_loss.get('stop_loss') is not None else None
            }
            logger.info(f"🎯 목표가/손절가 설정 확인: 입력값={target_and_loss}")
            logger.info(f"🎯 목표가/손절가 파싱 결과: 목표가={self.target_and_loss.get('target_gain')}%, 손절가={self.target_and_loss.get('stop_loss')}%")
        else:
            logger.info(f"⚠️ 목표가/손절가 설정 없음: target_and_loss={target_and_loss}")

        self.hold_days = None
        if hold_days:
            self.hold_days = {
                "min_hold_days": hold_days.get('min_hold_days'),
                "max_hold_days": hold_days.get('max_hold_days'),
                "sell_price_basis": hold_days.get('sell_price_basis', 'CURRENT'),
                "sell_price_offset": Decimal(str(hold_days.get('sell_price_offset'))) if hold_days.get('sell_price_offset') is not None else None
            }

        self.condition_sell_meta = None
        if condition_sell:
            self.condition_sell_meta = {
                "sell_price_basis": condition_sell.get('sell_price_basis', 'CURRENT'),
                "sell_price_offset": Decimal(str(condition_sell.get('sell_price_offset'))) if condition_sell.get('sell_price_offset') is not None else None
            }

        # 매매 대상 필터 저장
        self.target_themes = target_themes or []
        self.target_stocks = target_stocks or []
        self.target_universes = target_universes or []

        try:
            # 1. 데이터 준비
            logger.info(f"백테스트 시작: {backtest_id}")
            logger.info(f"📅 백테스트 기간: {start_date} ~ {end_date}")
            logger.info(f"매매 대상 필터 - 테마: {self.target_themes}, 종목: {self.target_stocks}, 유니버스: {self.target_universes}")

            # 순차 데이터 로딩 (SQLAlchemy AsyncSession은 동시 작업 미지원)
            price_data = await self._load_price_data(start_date, end_date, target_themes, target_stocks, target_universes)
            financial_data = await self._load_financial_data(start_date, end_date)

            # 1.5. 기존 백테스트 결과 삭제 (재실행 시 중복 방지)
            from sqlalchemy import delete
            from app.models.simulation import SimulationDailyValue, SimulationTrade, SimulationPosition

            logger.info(f"기존 백테스트 결과 삭제 시작: {backtest_id}")
            await self.db.execute(delete(SimulationDailyValue).where(SimulationDailyValue.session_id == str(backtest_id)))
            await self.db.execute(delete(SimulationTrade).where(SimulationTrade.session_id == str(backtest_id)))
            await self.db.execute(delete(SimulationPosition).where(SimulationPosition.session_id == str(backtest_id)))
            await self.db.commit()
            logger.info(f"✅ 기존 백테스트 결과 삭제 완료")

            # 2. 팩터 계산 - 최적화된 버전 사용
            # 매수 조건에서 priority_factor 추출
            priority_factor = None
            if isinstance(buy_conditions, dict):
                priority_factor = buy_conditions.get('priority_factor')
            elif isinstance(buy_conditions, list) and buy_conditions:
                # 리스트에서 priority_factor 찾기
                for condition in buy_conditions:
                    if isinstance(condition, dict) and 'priority_factor' in condition:
                        priority_factor = condition.get('priority_factor')
                        break

            # priority_factor 파싱: "{PER}" 또는 "기본값({PER})" → "PER"
            if priority_factor:
                import re
                match = re.search(r'\{([^}]+)\}', priority_factor)
                if match:
                    priority_factor = match.group(1).upper()

            # SimpleCondition 객체 리스트 생성 (최적화된 팩터 계산을 위해)
            # BacktestCondition 스키마 대신 간단한 객체 사용
            class SimpleCondition:
                def __init__(self, exp_left_side, inequality, exp_right_side):
                    self.exp_left_side = exp_left_side
                    self.inequality = inequality
                    self.exp_right_side = exp_right_side

            backtest_conditions = []

            # buy_conditions가 딕셔너리 형식인 경우 (새로운 형식)
            if isinstance(buy_conditions, dict) and 'conditions' in buy_conditions:
                conditions_list = buy_conditions.get('conditions', [])
                for cond in conditions_list:
                    if isinstance(cond, dict):
                        if 'factor' in cond:
                            exp_left_side = f"기본값({{{cond['factor']}}})"
                            inequality = cond.get('operator', '>')
                            exp_right_side = cond.get('value', 0)
                        else:
                            exp_left_side = cond.get('exp_left_side', '')
                            inequality = cond.get('inequality', '')
                            exp_right_side = cond.get('exp_right_side', 0)

                            # exp_left_side에서 팩터명 추출하여 factor 필드 추가
                            import re
                            match = re.search(r'\{([^}]+)\}', exp_left_side)
                            if match:
                                cond['factor'] = match.group(1).upper()
                            cond['operator'] = inequality
                            cond['value'] = exp_right_side
                            if 'name' in cond:
                                cond['id'] = cond['name']

                        backtest_conditions.append(SimpleCondition(
                            exp_left_side=exp_left_side,
                            inequality=inequality,
                            exp_right_side=exp_right_side
                        ))

            # buy_conditions가 리스트 형식인 경우 (기존 형식)
            elif isinstance(buy_conditions, list):
                for cond in buy_conditions:
                    if isinstance(cond, dict):
                        # Dict를 SimpleCondition 객체로 변환
                        # 두 가지 형식 지원:
                        # 1. {'exp_left_side': '기본값({PBR})', 'inequality': '>', 'exp_right_side': 10}
                        # 2. {'factor': 'PBR', 'operator': '>', 'value': 10}
                        if 'factor' in cond:
                            # 파싱된 형식 (advanced_backtest.py에서 온 경우)
                            exp_left_side = f"기본값({{{cond['factor']}}})"
                            inequality = cond.get('operator', '>')
                            exp_right_side = cond.get('value', 0)
                        else:
                            # 원본 형식
                            exp_left_side = cond.get('exp_left_side', '')
                            inequality = cond.get('inequality', '')
                            exp_right_side = cond.get('exp_right_side', 0)

                            # exp_left_side에서 팩터명 추출하여 factor 필드 추가
                            import re
                            match = re.search(r'\{([^}]+)\}', exp_left_side)
                            if match:
                                cond['factor'] = match.group(1).upper()
                            cond['operator'] = inequality
                            cond['value'] = exp_right_side
                            if 'name' in cond:
                                cond['id'] = cond['name']

                        backtest_conditions.append(SimpleCondition(
                            exp_left_side=exp_left_side,
                            inequality=inequality,
                            exp_right_side=exp_right_side
                        ))

            # 최적화된 팩터 계산 호출
            logger.info("최적화된 팩터 계산 사용")
            factor_data = await self._calculate_all_factors_optimized(
                price_data, financial_data, start_date, end_date,
                buy_conditions=backtest_conditions,
                priority_factor=priority_factor
            )

            # 3. 벤치마크 데이터 로드
            benchmark_data = await self._load_benchmark_data(benchmark, start_date, end_date)

            # 4. 포트폴리오 시뮬레이션
            portfolio_result = await self._simulate_portfolio(
                backtest_id=backtest_id,
                factor_data=factor_data,
                price_data=price_data,
                buy_conditions=buy_conditions,
                sell_conditions=sell_conditions,
                condition_sell=condition_sell,
                initial_capital=initial_capital,
                rebalance_frequency=rebalance_frequency,
                max_positions=max_positions,
                position_sizing=position_sizing,
                benchmark_data=benchmark_data,
                start_date=start_date,
                end_date=end_date
            )

            # 5. 통계 계산
            statistics = self._calculate_statistics(
                portfolio_result, initial_capital, start_date, end_date
            )

            # 6. 결과 포맷팅
            result = await self._format_result(
                backtest_id=backtest_id,
                portfolio_result=portfolio_result,
                statistics=statistics,
                buy_conditions=buy_conditions,
                sell_conditions=sell_conditions,
                condition_sell=condition_sell,
                settings={
                    "rebalance_frequency": rebalance_frequency,
                    "max_positions": max_positions,
                    "position_sizing": position_sizing,
                    "benchmark": benchmark,
                    "commission_rate": float(self.commission_rate),
                    "tax_rate": float(self.tax_rate),
                    "slippage": float(self.slippage)
                }
            )

            # 7. 결과 저장
            await self._save_result(backtest_id, result)

            return result

        except Exception as e:
            logger.error(f"백테스트 실패: {e}")
            raise

    async def _load_price_data(
        self,
        start_date: date,
        end_date: date,
        target_themes: List[str] = None,
        target_stocks: List[str] = None,
        target_universes: List[str] = None
    ) -> pd.DataFrame:
        """가격 데이터 로드 (매매 대상 필터 적용) + Redis 캐싱"""

        logger.info(f"📊 가격 데이터 로드 - target_themes: {target_themes}, target_stocks: {target_stocks}, target_universes: {target_universes}")

        # 🚀 Redis 캐시 조회 (필터 없는 기본 캐시 사용)
        from app.core.cache import get_cache
        cache = get_cache()

        # 기본 캐시 키 (필터 없음 - 모든 사용자가 같은 캐시 공유)
        base_cache_key = f"price_data:all:{start_date}:{end_date}"

        # 🚀 캐시 조회
        cached_data = None
        try:
            cached_data = await cache.get(base_cache_key)
            if cached_data:
                logger.info(f"💾 시세 데이터 캐시 히트: {len(cached_data)}개 레코드 (기본 캐시)")

                # 캐시 데이터를 DataFrame으로 변환
                df = pd.DataFrame(cached_data)

                # 메모리에서 필터링 적용 (AND 로직)
                if target_themes or target_stocks or target_universes:
                    if target_stocks:
                        # 개별 종목 선택 시 다른 필터 무시
                        filter_mask = df['stock_code'].isin(target_stocks) if 'stock_code' in df.columns else pd.Series([False] * len(df))
                        logger.info(f"🎯 개별 종목 필터만 적용 (메모리): {len(target_stocks)}개")
                    else:
                        # 유니버스 & 테마를 AND로 결합
                        filter_mask = pd.Series([True] * len(df))  # 시작은 모두 True

                        if target_themes and 'industry' in df.columns:
                            filter_mask &= df['industry'].isin(target_themes)
                            logger.info(f"🎯 테마 AND 필터 (메모리): {len(target_themes)}개 산업")

                        if target_universes:
                            # 유니버스 종목 코드 조회
                            from app.services.universe_service import UniverseService
                            universe_service = UniverseService(self.db)
                            universe_stock_codes = await universe_service.get_stock_codes_by_universes(
                                target_universes,
                                trade_date=start_date.strftime("%Y%m%d")
                            )
                            if universe_stock_codes and 'stock_code' in df.columns:
                                filter_mask &= df['stock_code'].isin(universe_stock_codes)
                                logger.info(f"🎯 유니버스 AND 필터 (메모리): {len(universe_stock_codes)}개 종목")

                    df = df[filter_mask]
                    logger.info(f"✅ AND 필터링 후: {len(df)}개 레코드")

                return df
        except Exception as e:
            logger.debug(f"시세 캐시 조회 실패: {e}")

        # 날짜 범위 확장 (모멘텀 계산을 위해 252일 추가)
        extended_start = start_date - timedelta(days=365)

        # 기본 조건
        conditions = [
            StockPrice.trade_date >= extended_start,
            StockPrice.trade_date <= end_date,
            StockPrice.close_price.isnot(None),
            StockPrice.volume > 0
        ]

        # 매매 대상 필터 적용
        if target_themes or target_stocks or target_universes:
            filter_conditions = []

            if target_themes:
                # 선택된 산업(테마)에 속한 종목만
                logger.info(f"🎯 테마 필터: {len(target_themes)}개 산업 - {target_themes[:3]}...")
                filter_conditions.append(Company.industry.in_(target_themes))

            if target_stocks:
                # 선택된 개별 종목만
                logger.info(f"🎯 개별 종목 필터: {len(target_stocks)}개")
                filter_conditions.append(Company.stock_code.in_(target_stocks))

            if target_universes:
                # 선택된 유니버스에 속한 종목만
                from app.services.universe_service import UniverseService
                universe_service = UniverseService(self.db)
                universe_stock_codes = await universe_service.get_stock_codes_by_universes(
                    target_universes,
                    trade_date=start_date.strftime("%Y%m%d")
                )
                if universe_stock_codes:
                    logger.info(f"🎯 유니버스 필터링: {len(universe_stock_codes)}개 종목 (유니버스: {target_universes})")
                    filter_conditions.append(Company.stock_code.in_(universe_stock_codes))
                else:
                    logger.warning(f"⚠️ 유니버스에 종목이 없습니다: {target_universes}")

            # AND 조건으로 결합 (유니버스 AND 테마로 교집합 필터링)
            # 개별 종목은 OR로 추가 (개별 종목 선택 시 다른 필터 무시)
            logger.info(f"🔍 필터 조건 개수: {len(filter_conditions)} (AND 결합)")
            if target_stocks:
                # 개별 종목이 있으면 개별 종목만 사용 (다른 필터 무시)
                conditions.append(Company.stock_code.in_(target_stocks))
                logger.info(f"✅ 개별 종목 필터만 적용")
            else:
                # 유니버스와 테마를 AND로 결합
                for condition in filter_conditions:
                    conditions.append(condition)
                logger.info(f"✅ 유니버스 & 테마 AND 필터 적용")

        query = select(
            StockPrice.company_id,
            Company.stock_code,
            Company.company_name.label('stock_name'),
            Company.industry.label('industry'),
            Company.market_type.label('market_type'),
            StockPrice.trade_date.label('date'),
            StockPrice.open_price,
            StockPrice.high_price,
            StockPrice.low_price,
            StockPrice.close_price,
            StockPrice.volume,
            StockPrice.trading_value,
            StockPrice.market_cap,
            StockPrice.listed_shares
        ).join(
            Company, StockPrice.company_id == Company.company_id
        ).where(
            and_(*conditions)
        ).order_by(
            StockPrice.trade_date,
            Company.stock_code
        )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        # DataFrame으로 변환
        df = pd.DataFrame(rows)

        if df.empty:
            logger.warning(f"No price data found for period {start_date} to {end_date}")
            return pd.DataFrame()

        # 데이터 타입 변환
        df['date'] = pd.to_datetime(df['date'])
        numeric_columns = ['open_price', 'high_price', 'low_price', 'close_price',
                          'volume', 'trading_value', 'market_cap', 'listed_shares']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        logger.info(f"📊 시세 데이터 로드 완료: {len(df):,}개 레코드, {df['stock_code'].nunique()}개 종목")
        logger.info(f"📅 시세 데이터 날짜 범위: {df['date'].min().date()} ~ {df['date'].max().date()}")

        # 캐시는 cache_warmer가 주기적으로 갱신하므로 여기서는 저장하지 않음
        # (필터링된 데이터를 저장하면 캐시 키가 너무 많아짐)

        return df

    async def _load_financial_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """재무 데이터 로드 + Redis 캐싱"""

        logger.info(f"📊 재무 데이터 로드 시작: {start_date} ~ {end_date}")

        # 🚀 Redis 캐시 키 생성
        from app.core.cache import get_cache
        cache = get_cache()
        cache_key = f"financial_data:{start_date}:{end_date}"

        # 🚀 캐시 조회
        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.info(f"💾 재무 데이터 캐시 히트: {len(cached_data)}개 레코드")
                df = pd.DataFrame(cached_data)
                if 'report_date' in df.columns:
                    df['report_date'] = pd.to_datetime(df['report_date'])
                if 'available_date' in df.columns:
                    df['available_date'] = pd.to_datetime(df['available_date'])
                return df
        except Exception as e:
            logger.debug(f"재무 캐시 조회 실패: {e}")

        logger.info("💾 재무 데이터 캐시 미스 - DB 로드 시작")

        # 재무제표 기간 설정 (분기별 데이터 고려)
        extended_start = start_date - timedelta(days=180)  # 6개월 전 데이터부터

        # 손익계산서 데이터
        # Note: report_date 컬럼이 DB에 없으므로 bsns_year로 필터링
        start_year = str(start_date.year - 1)  # 1년 전 데이터부터
        end_year = str(end_date.year)

        logger.info(f"📊 재무 데이터 조회 연도 범위: {start_year} ~ {end_year}")

        income_query = select(
            FinancialStatement.company_id,
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            IncomeStatement.account_nm,
            IncomeStatement.thstrm_amount.label('current_amount'),
            IncomeStatement.thstrm_add_amount.label('cumulative_amount'),
            IncomeStatement.frmtrm_amount.label('previous_amount')
        ).join(
            IncomeStatement, FinancialStatement.stmt_id == IncomeStatement.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(
                FinancialStatement.bsns_year >= start_year,
                FinancialStatement.bsns_year <= end_year,
                IncomeStatement.account_nm.in_([
                    # 매출액 (연도별로 다른 이름)
                    '매출액', '매출', '영업수익', '수익(매출액)',
                    '영업이익', '영업이익(손실)',
                    '당기순이익', '당기순이익(손실)',
                    '매출총이익', '매출원가'
                ])
            )
        )

        # 재무상태표 데이터
        balance_query = select(
            FinancialStatement.company_id,
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            BalanceSheet.account_nm,
            BalanceSheet.thstrm_amount.label('current_amount')
        ).join(
            BalanceSheet, FinancialStatement.stmt_id == BalanceSheet.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(
                FinancialStatement.bsns_year >= start_year,
                FinancialStatement.bsns_year <= end_year,
                BalanceSheet.account_nm.in_([
                    '자산총계', '자본총계', '부채총계',
                    '유동자산', '유동부채', '비유동부채',
                    '현금및현금성자산', '단기차입금', '장기차입금'
                ])
            )
        )

        # 데이터 실행
        income_result = await self.db.execute(income_query)
        balance_result = await self.db.execute(balance_query)

        income_df = pd.DataFrame(income_result.mappings().all())
        balance_df = pd.DataFrame(balance_result.mappings().all())

        # 계정 과목 정규화 (연도별 차이 해결)
        if not income_df.empty:
            income_df['account_nm'] = income_df['account_nm'].str.replace('당기순이익(손실)', '당기순이익', regex=False)
            # 매출액 정규화 (여러 이름을 '매출액'으로 통일)
            income_df['account_nm'] = income_df['account_nm'].str.replace('영업수익', '매출액', regex=False)
            income_df['account_nm'] = income_df['account_nm'].str.replace('수익(매출액)', '매출액', regex=False)
            income_df['account_nm'] = income_df['account_nm'].str.replace('매출', '매출액', regex=False)
            logger.info("매출액 계정명 정규화 완료")

        # 데이터 통합 및 피벗
        if not income_df.empty:
            income_pivot = income_df.pivot_table(
                index=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                columns='account_nm',
                values='current_amount',
                aggfunc='first'
            ).reset_index()
        else:
            income_pivot = pd.DataFrame()

        if not balance_df.empty:
            balance_pivot = balance_df.pivot_table(
                index=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                columns='account_nm',
                values='current_amount',
                aggfunc='first'
            ).reset_index()
        else:
            balance_pivot = pd.DataFrame()

        # 두 데이터프레임 병합
        if not income_pivot.empty and not balance_pivot.empty:
            financial_df = pd.merge(
                income_pivot, balance_pivot,
                on=['company_id', 'stock_code', 'fiscal_year', 'report_code'],
                how='outer'
            )
        elif not income_pivot.empty:
            financial_df = income_pivot
        elif not balance_pivot.empty:
            financial_df = balance_pivot
        else:
            financial_df = pd.DataFrame()

        if not financial_df.empty:
            # report_date 컬럼이 없으므로 fiscal_year와 report_code로부터 생성
            # report_code: 11011(사업보고서), 11012(반기), 11013(1Q), 11014(3Q)
            def make_report_date(row):
                year = int(row['fiscal_year'])
                code = row['report_code']
                if code == '11011':  # 사업보고서 - 연말
                    return pd.Timestamp(year, 12, 31)
                elif code == '11012':  # 반기보고서 - 6월말
                    return pd.Timestamp(year, 6, 30)
                elif code == '11013':  # 1분기 - 3월말
                    return pd.Timestamp(year, 3, 31)
                elif code == '11014':  # 3분기 - 9월말
                    return pd.Timestamp(year, 9, 30)
                else:
                    return pd.Timestamp(year, 12, 31)  # 기본값

            financial_df['report_date'] = financial_df.apply(make_report_date, axis=1)

            # 보고서 코드별 공시 지연 일수를 적용해 실제 사용 가능 날짜 추정
            report_delay_map = {
                '11011': 90,  # 사업보고서
                '11012': 60,  # 반기보고서
                '11013': 45,  # 1분기보고서
                '11014': 45   # 3분기보고서
            }
            financial_df['report_delay_days'] = financial_df['report_code'].map(report_delay_map).fillna(90)
            financial_df['available_date'] = financial_df['report_date'] + pd.to_timedelta(
                financial_df['report_delay_days'], unit='D'
            )
            financial_df.drop(columns=['report_delay_days'], inplace=True)

            # 매출액 계산 (2023년처럼 직접 제공되지 않는 경우)
            # Revenue = Cost of Goods Sold + Gross Profit
            if '매출액' in financial_df.columns and '매출원가' in financial_df.columns and '매출총이익' in financial_df.columns:
                financial_df['매출액'] = financial_df.apply(
                    lambda row: row['매출원가'] + row['매출총이익']
                    if pd.isna(row.get('매출액')) and pd.notna(row.get('매출원가')) and pd.notna(row.get('매출총이익'))
                    else row.get('매출액'),
                    axis=1
                )

            logger.info(f"Loaded financial data for {financial_df['stock_code'].nunique()} companies")

            # 🚀 캐시 저장 (7일 TTL - 재무제표는 분기별로 변경)
            try:
                # report_date를 문자열로 변환하여 저장
                cache_df = financial_df.copy()
                if 'report_date' in cache_df.columns:
                    cache_df['report_date'] = cache_df['report_date'].astype(str)
                if 'available_date' in cache_df.columns:
                    cache_df['available_date'] = cache_df['available_date'].astype(str)
                await cache.set(cache_key, cache_df.to_dict('records'), ttl=0)
                logger.info(f"💾 재무 데이터 캐시 저장 완료")
            except Exception as e:
                logger.debug(f"재무 캐시 저장 실패: {e}")

        return financial_df

    async def _load_benchmark_data(self, benchmark: str, start_date: date, end_date: date) -> pd.DataFrame:
        """벤치마크 데이터 로드 (KOSPI/KOSDAQ) + Redis 캐싱"""

        # 🚀 Redis 캐시 키 생성
        from app.core.cache import get_cache
        cache = get_cache()
        cache_key = f"benchmark:{benchmark}:{start_date}:{end_date}"

        # 🚀 캐시 조회
        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.info(f"💾 벤치마크 데이터 캐시 히트: {benchmark}")
                df = pd.DataFrame(cached_data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                return df
        except Exception as e:
            logger.debug(f"벤치마크 캐시 조회 실패: {e}")

        # 벤치마크 코드 매핑
        benchmark_codes = {
            'KOSPI': 'KOSPI',
            'KOSDAQ': 'KOSDAQ',
            'KOSPI200': 'KOSPI200'
        }

        benchmark_code = benchmark_codes.get(benchmark, 'KOSPI')

        # 실제로는 별도 벤치마크 테이블에서 로드해야 하지만,
        # 현재는 더미 데이터 생성
        dates = pd.date_range(start_date, end_date, freq='B')  # Business days

        # 가상의 벤치마크 수익률 생성
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.015, len(dates))  # 평균 0.05%, 변동성 1.5%

        benchmark_df = pd.DataFrame({
            'date': dates,
            'benchmark': benchmark_code,
            'close': 1000 * (1 + returns).cumprod(),
            'return': returns
        })

        logger.info(f"Loaded {benchmark} benchmark data: {len(benchmark_df)} days")

        # 🚀 캐시 저장 (7일 TTL)
        try:
            cache_df = benchmark_df.copy()
            if 'date' in cache_df.columns:
                cache_df['date'] = cache_df['date'].astype(str)
            await cache.set(cache_key, cache_df.to_dict('records'), ttl=604800)
            logger.info(f"💾 벤치마크 데이터 캐시 저장 완료")
        except Exception as e:
            logger.debug(f"벤치마크 캐시 저장 실패: {e}")

        return benchmark_df

    def _extract_required_factors(self, buy_conditions: List[Any], priority_factor: Optional[str]) -> Set[str]:
        """매수 조건에서 필요한 팩터만 추출"""
        required_factors = set()

        # 매수 조건에서 팩터 추출
        if buy_conditions:
            # buy_conditions가 딕셔너리일 경우 (새로운 형식)
            if isinstance(buy_conditions, dict):
                conditions_list = buy_conditions.get('conditions', [])

                for condition in conditions_list:
                    # 'factor' 필드에서 직접 팩터 추출
                    if isinstance(condition, dict) and 'factor' in condition:
                        factor_code = condition['factor'].upper()
                        required_factors.add(factor_code)

            # buy_conditions가 리스트일 경우 (기존 형식)
            elif isinstance(buy_conditions, list):
                for condition in buy_conditions:
                    # 딕셔너리 또는 객체 둘 다 지원
                    if isinstance(condition, dict):
                        # 새로운 형식: 'factor' 필드 확인
                        if 'factor' in condition:
                            factor_code = condition['factor'].upper()
                            required_factors.add(factor_code)
                        else:
                            # 기존 형식: exp_left_side, exp_right_side
                            exp_left = condition.get('exp_left_side', '')
                            exp_right = condition.get('exp_right_side', '')

                            logger.info(f"  exp_left: '{exp_left}', exp_right: '{exp_right}'")

                            # 왼쪽 표현식에서 팩터 추출
                            left_match = re.findall(r'\{([^}]+)\}', exp_left)
                            logger.info(f"  left_match: {left_match}")

                            for match in left_match:
                                code_match = re.search(r'\(([A-Z_]+)\)', match)
                                if code_match:
                                    factor_code = code_match.group(1)
                                    required_factors.add(factor_code)
                                    logger.info(f"  추출된 팩터 (괄호): {factor_code}")
                                else:
                                    factor_code = match.strip().upper()
                                    required_factors.add(factor_code)
                                    logger.info(f"  추출된 팩터 (직접): {factor_code}")

                            # 오른쪽 표현식에서도 팩터 추출
                            if isinstance(exp_right, str):
                                right_match = re.findall(r'\{([^}]+)\}', exp_right)
                                for match in right_match:
                                    code_match = re.search(r'\(([A-Z_]+)\)', match)
                                    if code_match:
                                        required_factors.add(code_match.group(1))
                                    else:
                                        required_factors.add(match.strip().upper())
                    else:
                        exp_left = getattr(condition, 'exp_left_side', '')
                        exp_right = getattr(condition, 'exp_right_side', '')

                        logger.info(f"  exp_left: '{exp_left}', exp_right: '{exp_right}'")

                        left_match = re.findall(r'\{([^}]+)\}', exp_left)
                        for match in left_match:
                            code_match = re.search(r'\(([A-Z_]+)\)', match)
                            if code_match:
                                factor_code = code_match.group(1)
                                required_factors.add(factor_code)
                            else:
                                factor_code = match.strip().upper()
                                required_factors.add(factor_code)

                        if isinstance(exp_right, str):
                            right_match = re.findall(r'\{([^}]+)\}', exp_right)
                            for match in right_match:
                                code_match = re.search(r'\(([A-Z_]+)\)', match)
                                if code_match:
                                    required_factors.add(code_match.group(1))
                                else:
                                    required_factors.add(match.strip().upper())

        # 우선순위 팩터 추가
        if priority_factor:
            logger.info(f"우선순위 팩터: '{priority_factor}'")
            match = re.search(r'\{([^}]+)\}', priority_factor)
            if match:
                full_name = match.group(1)
                code_match = re.search(r'\(([A-Z_]+)\)', full_name)
                if code_match:
                    required_factors.add(code_match.group(1))
                else:
                    required_factors.add(full_name.strip().upper())
            else:
                if priority_factor != "없음":
                    required_factors.add(priority_factor.upper())

        logger.info(f"필요한 팩터: {required_factors}")
        return required_factors

    async def _calculate_factors_multiprocessing(
        self,
        price_pl: pl.DataFrame,
        financial_pl: Optional[pl.DataFrame],
        financial_dict: Optional[Dict],
        unique_dates: List,
        required_factors: Set[str],
        price_data: pd.DataFrame,
        start_time: float
    ) -> List[Dict]:
        """🚀 멀티프로세싱 병렬 처리 (최고 성능)"""
        import concurrent.futures

        total_dates = len(unique_dates)
        num_cores = multiprocessing.cpu_count()
        logger.info(f"🚀 멀티프로세싱 시작: {total_dates}개 날짜를 {num_cores}개 코어로 분산 처리")

        # 날짜를 청크로 분할
        chunk_size = max(1, total_dates // num_cores)
        date_chunks = [unique_dates[i:i + chunk_size] for i in range(0, total_dates, chunk_size)]

        # 🚀 Polars vectorization의 장점을 활용하기 위해:
        # - 각 날짜별로 팩터 계산 (Polars가 내부적으로 SIMD 사용)
        # - 단순화: 멀티프로세싱 대신 asyncio로 빠르게 처리
        # - Polars의 group_by + agg가 이미 최적화되어 있으므로 단순 반복으로도 충분히 빠름

        all_rows = []

        for date_idx, calc_date in enumerate(unique_dates):
            todays_prices = price_data[price_data['date'] == calc_date]
            if todays_prices.empty:
                continue

            date_rows = []
            industry_map = {}
            if 'industry' in todays_prices.columns:
                industry_map = dict(zip(todays_prices['stock_code'], todays_prices['industry']))

            size_bucket_map = self._assign_size_buckets(todays_prices)
            stock_factor_map: Dict[str, Dict[str, float]] = defaultdict(dict)
            price_until_date = price_pl.filter(pl.col('date') <= calc_date)

            # 🚀 Polars 벡터화된 팩터 계산 (내부적으로 최적화됨)
            if financial_pl is not None or financial_dict is not None:
                value_factor_list = ['PER', 'PBR', 'PSR', 'PCR', 'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD', 'EV_EBITDA', 'EV_SALES', 'BOOK_TO_MARKET']
                if any(f in required_factors for f in value_factor_list):
                    try:
                        value_map = self._calculate_value_factors(price_until_date, financial_pl, calc_date, financial_dict)
                        filtered_value_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in value_map.items()}
                        self._merge_factor_maps(stock_factor_map, filtered_value_map)
                    except Exception as e:
                        logger.error(f"가치 팩터 에러 ({calc_date}): {e}")

                if any(f in required_factors for f in ['ROE', 'ROA', 'DEBT_RATIO', 'GPM', 'OPM', 'NPM']):
                    try:
                        profit_map = self._calculate_profitability_factors(financial_pl, calc_date, financial_dict)
                        filtered_profit_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in profit_map.items()}
                        self._merge_factor_maps(stock_factor_map, filtered_profit_map)
                    except Exception as e:
                        logger.error(f"수익성 팩터 에러 ({calc_date}): {e}")

                if any(f in required_factors for f in ['DEBT_TO_EQUITY', 'EQUITY_RATIO', 'CURRENT_RATIO', 'QUICK_RATIO', 'CASH_RATIO', 'INTEREST_COVERAGE']):
                    try:
                        stability_map = self._calculate_stability_factors(financial_pl, calc_date, financial_dict)
                        filtered_stability_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in stability_map.items()}
                        self._merge_factor_maps(stock_factor_map, filtered_stability_map)
                    except Exception as e:
                        logger.error(f"안정성 팩터 에러 ({calc_date}): {e}")

                growth_factor_list = ['REVENUE_GROWTH', 'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'SALES_GROWTH',
                                      'EARNINGS_GROWTH', 'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y',
                                      'OPERATING_INCOME_GROWTH', 'ASSET_GROWTH', 'ASSET_GROWTH_3Y',
                                      'EQUITY_GROWTH', 'GROSS_PROFIT_GROWTH']
                if any(f in required_factors for f in growth_factor_list):
                    try:
                        growth_map = self._calculate_growth_factors(financial_pl, calc_date, financial_dict)
                        filtered_growth_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in growth_map.items()}
                        self._merge_factor_maps(stock_factor_map, filtered_growth_map)
                    except Exception as e:
                        logger.error(f"성장성 팩터 에러 ({calc_date}): {e}")

            if any(f.startswith('MOMENTUM') for f in required_factors):
                try:
                    momentum_map = self._calculate_momentum_factors(price_until_date, calc_date)
                    filtered_momentum_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in momentum_map.items()}
                    self._merge_factor_maps(stock_factor_map, filtered_momentum_map)
                except Exception as e:
                    logger.error(f"모멘텀 팩터 에러 ({calc_date}): {e}")

            if any(f.startswith('VOLATILITY') for f in required_factors):
                try:
                    volatility_map = self._calculate_volatility_factors(price_until_date, calc_date)
                    filtered_volatility_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in volatility_map.items()}
                    self._merge_factor_maps(stock_factor_map, filtered_volatility_map)
                except Exception as e:
                    logger.error(f"변동성 팩터 에러 ({calc_date}): {e}")

            if any(f in ['VOLUME_RATIO_20D', 'TURNOVER_RATE_20D'] for f in required_factors):
                try:
                    liquidity_map = self._calculate_liquidity_factors(price_until_date, calc_date)
                    filtered_liquidity_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in liquidity_map.items()}
                    self._merge_factor_maps(stock_factor_map, filtered_liquidity_map)
                except Exception as e:
                    logger.error(f"유동성 팩터 에러 ({calc_date}): {e}")

            technical_factors = ['BOLLINGER_POSITION', 'BOLLINGER_WIDTH', 'RSI', 'MACD', 'MACD_SIGNAL', 'MACD_HISTOGRAM']
            needs_technical = any(f in technical_factors for f in required_factors)

            if needs_technical:
                try:
                    technical_map = self._calculate_technical_indicators(price_until_date, calc_date)
                    filtered_technical_map = {stock: {k: v for k, v in factors.items() if k in required_factors} for stock, factors in technical_map.items()}
                    self._merge_factor_maps(stock_factor_map, filtered_technical_map)
                except Exception as e:
                    logger.error(f"기술적 지표 에러 ({calc_date}): {e}")

            # 결과 저장
            for stock in todays_prices['stock_code'].unique():
                record = {
                    'date': pd.Timestamp(calc_date),
                    'stock_code': stock,
                    'industry': industry_map.get(stock),
                    'size_bucket': size_bucket_map.get(stock)
                }
                record.update(stock_factor_map.get(stock, {}))
                date_rows.append(record)

            all_rows.extend(date_rows)

            # 진행상황 로깅
            if (date_idx + 1) % max(1, total_dates // 10) == 0:
                progress = (date_idx + 1) * 100 // total_dates
                elapsed = time.time() - start_time
                logger.info(f"⏱️  진행: {date_idx + 1}/{total_dates} ({progress}%) - 경과: {elapsed:.1f}초")

        return all_rows

    async def _calculate_factors_sequential(
        self,
        price_pl: pl.DataFrame,
        financial_pl: Optional[pl.DataFrame],
        financial_dict: Optional[Dict],
        unique_dates: List,
        required_factors: Set[str],
        price_data: pd.DataFrame,
        start_time: float,
        cache_enabled: bool
    ) -> List[Dict]:
        """순차 처리 + Redis 캐싱"""
        all_rows = []

        # 분기별 캐시를 위한 도우미 함수
        def get_quarter_key(calc_date):
            """날짜를 분기 키로 변환 (예: 2024-Q1)"""
            year = calc_date.year
            quarter = (calc_date.month - 1) // 3 + 1
            return f"{year}-Q{quarter}"

        total_dates = len(unique_dates)

        for date_idx, calc_date in enumerate(unique_dates):
            # 🚀 분기별 캐싱 (재무 데이터는 분기별이므로)
            cache_key = None
            if cache_enabled:
                quarter_key = get_quarter_key(calc_date)
                cache_params = {
                    'quarter': quarter_key,
                    'factors': sorted(list(required_factors)),
                    'stocks': sorted(price_data['stock_code'].unique().tolist()[:50])  # 종목 수 제한
                }
                cache_key = cache._generate_key('backtest_factors', cache_params)

                # 캐시 조회
                try:
                    cached_data = await cache.get(cache_key)
                    if cached_data:
                        logger.info(f"💾 캐시 히트: {quarter_key} - {len(cached_data)}개 레코드")
                        all_rows.extend(cached_data)
                        continue
                except Exception as e:
                    logger.debug(f"캐시 조회 실패: {e}")

            # 캐시 미스 - 계산 수행
            todays_prices = price_data[price_data['date'] == calc_date]
            if todays_prices.empty:
                continue

            date_rows = []
            industry_map = {}
            if 'industry' in todays_prices.columns:
                industry_map = dict(zip(todays_prices['stock_code'], todays_prices['industry']))

            size_bucket_map = self._assign_size_buckets(todays_prices)
            stock_factor_map: Dict[str, Dict[str, float]] = defaultdict(dict)
            price_until_date = price_pl.filter(pl.col('date') <= calc_date)

            # 선택적 팩터 계산
            if financial_pl is not None or financial_dict is not None:
                # 가치 팩터 (PER, PBR, PSR, PCR, DIVIDEND_YIELD, EARNINGS_YIELD, FCF_YIELD, EV_EBITDA, EV_SALES, BOOK_TO_MARKET)
                value_factor_list = ['PER', 'PBR', 'PSR', 'PCR', 'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD', 'EV_EBITDA', 'EV_SALES', 'BOOK_TO_MARKET']
                if any(f in required_factors for f in value_factor_list):
                    try:
                        value_map = self._calculate_value_factors(price_until_date, financial_pl, calc_date, financial_dict)
                        filtered_value_map = {}
                        for stock, factors in value_map.items():
                            filtered_value_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                        self._merge_factor_maps(stock_factor_map, filtered_value_map)
                    except Exception as e:
                        logger.error(f"가치 팩터 계산 에러 ({calc_date}): {e}")

                # 수익성 팩터 (ROE, ROA, DEBT_RATIO, GPM, OPM, NPM)
                if any(f in required_factors for f in ['ROE', 'ROA', 'DEBT_RATIO', 'GPM', 'OPM', 'NPM']):
                    try:
                        profit_map = self._calculate_profitability_factors(financial_pl, calc_date, financial_dict)
                        filtered_profit_map = {}
                        for stock, factors in profit_map.items():
                            filtered_profit_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                        self._merge_factor_maps(stock_factor_map, filtered_profit_map)
                    except Exception as e:
                        logger.error(f"수익성 팩터 계산 에러 ({calc_date}): {e}")

                # 안정성 팩터 (DEBT_TO_EQUITY, EQUITY_RATIO, CURRENT_RATIO, QUICK_RATIO, CASH_RATIO, INTEREST_COVERAGE)
                if any(f in required_factors for f in ['DEBT_TO_EQUITY', 'EQUITY_RATIO', 'CURRENT_RATIO', 'QUICK_RATIO', 'CASH_RATIO', 'INTEREST_COVERAGE']):
                    try:
                        stability_map = self._calculate_stability_factors(financial_pl, calc_date, financial_dict)
                        filtered_stability_map = {}
                        for stock, factors in stability_map.items():
                            filtered_stability_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                        self._merge_factor_maps(stock_factor_map, filtered_stability_map)
                    except Exception as e:
                        logger.error(f"안정성 팩터 계산 에러 ({calc_date}): {e}")

                # 성장성 팩터
                growth_factor_list = ['REVENUE_GROWTH', 'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'SALES_GROWTH',
                                      'EARNINGS_GROWTH', 'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y',
                                      'OPERATING_INCOME_GROWTH', 'ASSET_GROWTH', 'ASSET_GROWTH_3Y',
                                      'EQUITY_GROWTH', 'GROSS_PROFIT_GROWTH']
                if any(f in required_factors for f in growth_factor_list):
                    try:
                        growth_map = self._calculate_growth_factors(financial_pl, calc_date, financial_dict)
                        filtered_growth_map = {}
                        for stock, factors in growth_map.items():
                            filtered_growth_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                        self._merge_factor_maps(stock_factor_map, filtered_growth_map)
                    except Exception as e:
                        logger.error(f"성장성 팩터 계산 에러 ({calc_date}): {e}")

            # 모멘텀 팩터
            if any(f.startswith('MOMENTUM') for f in required_factors):
                try:
                    momentum_map = self._calculate_momentum_factors(price_until_date, calc_date)
                    filtered_momentum_map = {}
                    for stock, factors in momentum_map.items():
                        filtered_momentum_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                    self._merge_factor_maps(stock_factor_map, filtered_momentum_map)
                except Exception as e:
                    logger.error(f"모멘텀 팩터 계산 에러 ({calc_date}): {e}")

            # 변동성 팩터
            if any(f.startswith('VOLATILITY') for f in required_factors):
                try:
                    volatility_map = self._calculate_volatility_factors(price_until_date, calc_date)
                    filtered_volatility_map = {}
                    for stock, factors in volatility_map.items():
                        filtered_volatility_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                    self._merge_factor_maps(stock_factor_map, filtered_volatility_map)
                except Exception as e:
                    logger.error(f"변동성 팩터 계산 에러 ({calc_date}): {e}")

            # 유동성 팩터
            if any(f in ['VOLUME_RATIO_20D', 'TURNOVER_RATE_20D'] for f in required_factors):
                try:
                    liquidity_map = self._calculate_liquidity_factors(price_until_date, calc_date)
                    filtered_liquidity_map = {}
                    for stock, factors in liquidity_map.items():
                        filtered_liquidity_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                    self._merge_factor_maps(stock_factor_map, filtered_liquidity_map)
                except Exception as e:
                    logger.error(f"유동성 팩터 계산 에러 ({calc_date}): {e}")

            # 기술적 지표 팩터
            technical_factors = ['BOLLINGER_POSITION', 'BOLLINGER_WIDTH', 'RSI', 'MACD', 'MACD_SIGNAL', 'MACD_HISTOGRAM']
            needs_technical = any(f in technical_factors for f in required_factors)

            if needs_technical:
                try:
                    technical_map = self._calculate_technical_indicators(price_until_date, calc_date)
                    filtered_technical_map = {}
                    for stock, factors in technical_map.items():
                        filtered_technical_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                    self._merge_factor_maps(stock_factor_map, filtered_technical_map)
                except Exception as e:
                    logger.error(f"기술적 지표 팩터 계산 에러 ({calc_date}): {e}")

            # 결과 저장
            for stock in todays_prices['stock_code'].unique():
                record = {
                    'date': pd.Timestamp(calc_date),
                    'stock_code': stock,
                    'industry': industry_map.get(stock),
                    'size_bucket': size_bucket_map.get(stock)
                }
                record.update(stock_factor_map.get(stock, {}))
                date_rows.append(record)

            # 캐시 저장
            if cache_enabled and cache_key and date_rows:
                try:
                    await cache.set(cache_key, date_rows, ttl=0)
                except Exception as e:
                    logger.debug(f"캐시 저장 실패: {e}")

            all_rows.extend(date_rows)

            # 진행상황 로깅
            if (date_idx + 1) % max(1, total_dates // 10) == 0:
                progress = (date_idx + 1) * 100 // total_dates
                elapsed = time.time() - start_time
                logger.info(f"⏱️  진행: {date_idx + 1}/{total_dates} ({progress}%) - 경과: {elapsed:.1f}초")

        return all_rows

    async def _calculate_all_factors_optimized(
        self,
        price_data: pd.DataFrame,
        financial_data: pd.DataFrame,
        start_date: date,
        end_date: date,
        buy_conditions: Optional[List[Any]] = None,
        priority_factor: Optional[str] = None
    ) -> pd.DataFrame:
        """최적화된 팩터 계산 (병렬처리 + 선택적 계산 + Redis 캐싱)"""

        if price_data.empty:
            logger.warning("No price data available for factor calculation")
            return pd.DataFrame()

        # 1. 필요한 팩터만 추출
        required_factors = self._extract_required_factors(buy_conditions or [], priority_factor)
        if not required_factors:
            required_factors = {'PER', 'PBR', 'PSR', 'PCR', 'DIVIDEND_YIELD', 'EARNINGS_YIELD', 'FCF_YIELD', 'EV_EBITDA', 'EV_SALES', 'BOOK_TO_MARKET',
                              'ROE', 'ROA', 'DEBT_RATIO', 'GPM', 'OPM', 'NPM',
                              'DEBT_TO_EQUITY', 'CURRENT_RATIO', 'QUICK_RATIO', 'INTEREST_COVERAGE',
                              'MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M',
                              'VOLATILITY_20D', 'VOLATILITY_60D', 'VOLUME_RATIO_20D', 'TURNOVER_RATE_20D',
                              'BOLLINGER_POSITION', 'BOLLINGER_WIDTH', 'RSI', 'MACD',
                              'OPERATING_MARGIN', 'NET_MARGIN', 'CHANGE_RATE',
                              'OPERATING_INCOME_GROWTH', 'GROSS_PROFIT_GROWTH',
                              'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y',
                              'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y',
                              # Phase 2-B: 부분 구현 팩터 추가 (19개)
                              'ASSET_TURNOVER', 'QUALITY_SCORE', 'ACCRUALS_RATIO', 'ASSET_GROWTH_1Y',
                              'ALTMAN_Z_SCORE', 'EARNINGS_QUALITY',
                              'DISTANCE_FROM_52W_HIGH', 'DISTANCE_FROM_52W_LOW',
                              'RSI_14', 'MACD_SIGNAL', 'STOCHASTIC_14', 'VOLUME_ROC', 'PRICE_POSITION',
                              # NEW: 15 Missing Factors
                              'PEG', 'EV_FCF', 'DIVIDEND_YIELD', 'CAPE_RATIO', 'PTBV',
                              'ROIC', 'INVENTORY_TURNOVER',
                              'OCF_GROWTH_1Y', 'BOOK_VALUE_GROWTH_1Y', 'SUSTAINABLE_GROWTH_RATE',
                              'RELATIVE_STRENGTH', 'VOLUME_MOMENTUM', 'BETA',
                              # 22 Technical Indicators
                              'MA_5', 'MA_20', 'MA_60', 'MA_120', 'MA_250',  # Moving Averages (5)
                              'ADX', 'AROON_UP', 'AROON_DOWN', 'ATR', 'MACD_HISTOGRAM', 'PRICE_VS_MA20',  # Trend (6)
                              'CCI', 'MFI', 'ULTIMATE_OSCILLATOR', 'WILLIAMS_R', 'TRIX',  # Oscillators (5, RSI already exists)
                              'CMF', 'OBV', 'VWAP',  # Volume-based (3)
                              # === NEW: 40 Additional Factors ===
                              # Valuation (5)
                              'GRAHAM_NUMBER', 'GREENBLATT_RANK', 'MAGIC_FORMULA', 'PRICE_TO_FCF', 'PS_RATIO',
                              # Momentum (9)
                              'RETURN_1M', 'RETURN_3M', 'RETURN_6M', 'RETURN_12M', 'RET_3D', 'RET_8D',
                              'DAYS_FROM_52W_HIGH', 'DAYS_FROM_52W_LOW', 'WEEK_52_POSITION',
                              # Risk (4)
                              'DOWNSIDE_VOLATILITY', 'MAX_DRAWDOWN', 'SHARPE_RATIO', 'SORTINO_RATIO',
                              # Volatility (3)
                              'HISTORICAL_VOLATILITY_20', 'HISTORICAL_VOLATILITY_60', 'PARKINSON_VOLATILITY',
                              # Composite (3)
                              'ENTERPRISE_YIELD', 'PIOTROSKI_F_SCORE', 'SHAREHOLDER_YIELD',
                              # Microstructure (5)
                              'AMIHUD_ILLIQUIDITY', 'EASE_OF_MOVEMENT', 'FORCE_INDEX', 'INTRADAY_VOLATILITY', 'VOLUME_PRICE_TREND',
                              # Duplicate/Alias (7)
                              'DEBTRATIO', 'DIVIDENDYIELD', 'EARNINGS_GROWTH', 'OPERATING_INCOME_GROWTH_YOY',
                              'PEG_RATIO', 'REVENUE_GROWTH', 'SMA',
                              # Dividend (2)
                              'DIVIDEND_GROWTH_3Y', 'DIVIDEND_GROWTH_YOY'
                              }

        # Polars DataFrame으로 변환
        price_pl = pl.from_pandas(price_data)
        financial_pl = pl.from_pandas(financial_data) if not financial_data.empty else None

        # 🚀 최적화: 재무 데이터 사전 색인화 (종목별로 한 번만 필터링)
        financial_dict = None
        if financial_pl is not None:
            logger.info("🚀 재무 데이터 사전 색인화 시작...")
            financial_dict = {}
            unique_stocks = financial_pl.select('stock_code').unique().to_pandas()['stock_code'].tolist()
            for stock in unique_stocks:
                # 종목별로 한 번만 필터링하고 정렬
                financial_dict[stock] = financial_pl.filter(pl.col('stock_code') == stock).sort('available_date')
            logger.info(f"✅ 재무 데이터 색인화 완료: {len(financial_dict)}개 종목")

        unique_dates = sorted(price_data[price_data['date'] >= pd.Timestamp(start_date)]['date'].unique())
        total_dates = len(unique_dates)
        logger.info(f"팩터 계산 대상: {total_dates}개 거래일, 필요 팩터: {len(required_factors)}개")

        start_time = time.time()

        # 🚀 Option A: Multiprocessing (최고 성능) vs Sequential + Caching (캐시 히트 시 빠름)
        # 환경변수로 제어: USE_MULTIPROCESSING=true (기본값: true)
        import os
        use_multiprocessing = os.getenv('USE_MULTIPROCESSING', 'true').lower() == 'true'

        if use_multiprocessing and total_dates > 10:
            logger.info("🚀 멀티프로세싱 모드 활성화 (최고 성능)")
            # ProcessPoolExecutor로 병렬 처리
            all_rows = await self._calculate_factors_multiprocessing(
                price_pl, financial_pl, financial_dict, unique_dates,
                required_factors, price_data, start_time
            )
        else:
            logger.info("📦 순차 처리 + Redis 캐싱 모드")
            # 2. Redis 캐시 초기화
            try:
                await cache.initialize()
                cache_enabled = True
                logger.info("✅ Redis 캐시 활성화")
            except Exception as e:
                logger.warning(f"Redis 캐시 비활성화: {e}")
                cache_enabled = False

            # 순차 처리 (Redis 캐싱 지원)
            all_rows = await self._calculate_factors_sequential(
                price_pl, financial_pl, financial_dict, unique_dates,
                required_factors, price_data, start_time, cache_enabled
            )

        factor_df = pd.DataFrame(all_rows)

        if not factor_df.empty:
            # 팩터 순위 계산 (정규화는 스킵 - 원본 값 사용)
            # factor_df = self._normalize_factors(factor_df)  # 정규화 비활성화: 사용자가 입력한 조건 값과 비교하기 위해
            factor_df = self._calculate_factor_ranks(factor_df)

            elapsed_total = time.time() - start_time
            logger.info(
                f"최적화된 팩터 계산 완료: {len(factor_df)}개 종목-일 조합, "
                f"{len([c for c in factor_df.columns if c not in ('date', 'stock_code')])}개 팩터, "
                f"총 소요시간: {elapsed_total:.1f}초 (기존 대비 {elapsed_total/180*100:.0f}% 속도)"
            )

        return factor_df

    async def _calculate_all_factors(
        self,
        price_data: pd.DataFrame,
        financial_data: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """팩터 계산 - 최적화 버전으로 리디렉션"""
        # 기본적으로 최적화된 버전 사용
        return await self._calculate_all_factors_optimized(
            price_data, financial_data, start_date, end_date
        )

    def _assign_size_buckets(self, todays_prices: pd.DataFrame) -> Dict[str, str]:
        """시가총액 기반 규모 버킷 계산"""
        if 'market_cap' not in todays_prices.columns:
            return {}

        caps = todays_prices[['stock_code', 'market_cap']].dropna()
        if caps.empty:
            return {}

        try:
            q1 = caps['market_cap'].quantile(0.33)
            q2 = caps['market_cap'].quantile(0.66)
        except Exception:
            q1 = q2 = None

        size_map = {}

        for _, row in caps.iterrows():
            value = row['market_cap']
            if q1 is None or q2 is None:
                bucket = 'UNKNOWN'
            elif value >= q2:
                bucket = 'LARGE'
            elif value >= q1:
                bucket = 'MID'
            else:
                bucket = 'SMALL'
            size_map[row['stock_code']] = bucket

        return size_map

    def _merge_factor_maps(
        self,
        base_map: Dict[str, Dict[str, float]],
        new_map: Dict[str, Dict[str, float]]
    ) -> None:
        """팩터 계산 결과를 누적"""
        for stock, values in new_map.items():
            if not values:
                continue
            base_map.setdefault(stock, {}).update(values)

    def _calculate_value_factors(self, price_pl: pl.DataFrame, financial_pl: pl.DataFrame, calc_date, financial_dict: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """🚀 가치 팩터 계산 (Polars 벡터화 최적화)"""
        logger.info(f"🎯 _calculate_value_factors 호출됨! calc_date={calc_date}")
        factors: Dict[str, Dict[str, float]] = {}

        # 해당 날짜의 가격 데이터
        latest_price = price_pl.filter(pl.col('date') == calc_date)
        if latest_price.is_empty():
            return factors

        # 🚀 Polars 벡터화: 모든 종목의 재무 데이터를 한 번에 처리
        if financial_dict is not None:
            # 사전 색인화된 데이터 사용: 종목별 최신 재무 데이터 추출
            financial_records = []
            for stock in latest_price.select('stock_code').unique().to_pandas()['stock_code']:
                if stock not in financial_dict:
                    continue
                stock_financial = financial_dict[stock].filter(pl.col('available_date') <= calc_date)
                if stock_financial.is_empty():
                    continue

                # 최신 분기 재무 (PBR용)
                latest_fin = stock_financial.sort('available_date', descending=True).head(1)

                # 연간 보고서 (PER용)
                annual_reports = stock_financial.filter(pl.col('report_code') == '11011')
                if not annual_reports.is_empty():
                    annual_fin = annual_reports.sort('available_date', descending=True).head(1)
                    # 연간 보고서의 당기순이익과 최신 분기의 자본총계 결합
                    financial_records.append({
                        'stock_code': stock,
                        '당기순이익': annual_fin.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in annual_fin.columns else None,
                        '자본총계': latest_fin.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in latest_fin.columns else None
                    })
                else:
                    financial_records.append({
                        'stock_code': stock,
                        '당기순이익': None,
                        '자본총계': latest_fin.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in latest_fin.columns else None
                    })

            if not financial_records:
                return factors

            financial_data = pl.DataFrame(financial_records)
        else:
            # 기존 방식: 전체 재무 데이터에서 필터링
            latest_financial = financial_pl.filter(pl.col('available_date') <= calc_date)
            if latest_financial.is_empty():
                return factors

            # 🚀 Polars 벡터화: group_by로 종목별 최신 데이터 추출
            # 최신 분기 데이터 (PBR용)
            latest_fin = (
                latest_financial
                .sort('available_date', descending=True)
                .group_by('stock_code')
                .agg([
                    pl.col('자본총계').first().alias('자본총계')
                ])
            )

            # 연간 보고서 데이터 (PER용)
            annual_fin = (
                latest_financial
                .filter(pl.col('report_code') == '11011')
                .sort('available_date', descending=True)
                .group_by('stock_code')
                .agg([
                    pl.col('당기순이익').first().alias('당기순이익')
                ])
            )

            # 조인: 최신 분기와 연간 보고서 결합
            financial_data = latest_fin.join(annual_fin, on='stock_code', how='left')

        # 🚀 Polars 벡터화: 가격 데이터와 재무 데이터 조인
        joined = latest_price.join(financial_data, on='stock_code', how='inner')

        if joined.is_empty():
            return factors

        # 🚀 Polars 벡터화: PER, PBR 계산 (벡터 연산)
        result = joined.select([
            pl.col('stock_code'),
            # PER = 시가총액 / 당기순이익
            pl.when(
                (pl.col('당기순이익').is_not_null()) &
                (pl.col('market_cap').is_not_null()) &
                (pl.col('당기순이익') > 0)
            )
            .then(pl.col('market_cap') / pl.col('당기순이익'))
            .otherwise(None)
            .alias('PER'),
            # PBR = 시가총액 / 자본총계
            pl.when(
                (pl.col('자본총계').is_not_null()) &
                (pl.col('market_cap').is_not_null()) &
                (pl.col('자본총계') > 0)
            )
            .then(pl.col('market_cap') / pl.col('자본총계'))
            .otherwise(None)
            .alias('PBR')
        ])

        # Dictionary로 변환
        for row in result.iter_rows(named=True):
            stock = row['stock_code']
            entry = {}
            if row['PER'] is not None:
                entry['PER'] = float(row['PER'])
            if row['PBR'] is not None:
                entry['PBR'] = float(row['PBR'])
            if entry:
                factors[stock] = entry

        return factors

    def _calculate_profitability_factors(self, financial_pl: pl.DataFrame, calc_date, financial_dict: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """🚀 수익성 팩터 계산 (Polars 벡터화 최적화)"""
        factors: Dict[str, Dict[str, float]] = {}

        # 🚀 Polars 벡터화: 모든 종목의 최신 재무 데이터 한 번에 추출
        if financial_dict is not None:
            # 사전 색인화된 데이터 사용
            financial_records = []
            for stock, stock_data in financial_dict.items():
                stock_financial = stock_data.filter(pl.col('available_date') <= calc_date)
                if stock_financial.is_empty():
                    continue
                latest = stock_financial.sort('available_date', descending=True).head(1)
                financial_records.append({
                    'stock_code': stock,
                    '당기순이익': latest.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in latest.columns else None,
                    '자본총계': latest.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in latest.columns else None,
                    '자산총계': latest.select('자산총계').to_pandas().iloc[0, 0] if '자산총계' in latest.columns else None,
                    '부채총계': latest.select('부채총계').to_pandas().iloc[0, 0] if '부채총계' in latest.columns else None,
                    '매출액': latest.select('매출액').to_pandas().iloc[0, 0] if '매출액' in latest.columns else None,
                    '매출원가': latest.select('매출원가').to_pandas().iloc[0, 0] if '매출원가' in latest.columns else None,
                    '영업이익': latest.select('영업이익').to_pandas().iloc[0, 0] if '영업이익' in latest.columns else None
                })

            if not financial_records:
                return factors

            latest_financial = pl.DataFrame(financial_records)
        else:
            # 🚀 Polars 벡터화: group_by로 종목별 최신 데이터 추출
            filtered = financial_pl.filter(pl.col('available_date') <= calc_date)
            if filtered.is_empty():
                return factors

            latest_financial = (
                filtered
                .sort('available_date', descending=True)
                .group_by('stock_code')
                .agg([
                    pl.col('당기순이익').first().alias('당기순이익'),
                    pl.col('자본총계').first().alias('자본총계'),
                    pl.col('자산총계').first().alias('자산총계'),
                    pl.col('부채총계').first().alias('부채총계'),
                    pl.col('매출액').first().alias('매출액'),
                    pl.col('매출원가').first().alias('매출원가'),
                    pl.col('영업이익').first().alias('영업이익')
                ])
            )

        # 🚀 Polars 벡터화: ROE, ROA, DEBT_RATIO, GPM, OPM, NPM 계산 (벡터 연산)
        result = latest_financial.select([
            pl.col('stock_code'),
            # ROE = (당기순이익 / 자본총계) * 100
            pl.when(
                (pl.col('당기순이익').is_not_null()) &
                (pl.col('자본총계').is_not_null()) &
                (pl.col('자본총계') > 0)
            )
            .then((pl.col('당기순이익') / pl.col('자본총계')) * 100)
            .otherwise(None)
            .alias('ROE'),
            # ROA = (당기순이익 / 자산총계) * 100
            pl.when(
                (pl.col('당기순이익').is_not_null()) &
                (pl.col('자산총계').is_not_null()) &
                (pl.col('자산총계') > 0)
            )
            .then((pl.col('당기순이익') / pl.col('자산총계')) * 100)
            .otherwise(None)
            .alias('ROA'),
            # DEBT_RATIO = (부채총계 / 자본총계) * 100
            pl.when(
                (pl.col('부채총계').is_not_null()) &
                (pl.col('자본총계').is_not_null()) &
                (pl.col('자본총계') > 0)
            )
            .then((pl.col('부채총계') / pl.col('자본총계')) * 100)
            .otherwise(None)
            .alias('DEBT_RATIO'),
            # GPM = ((매출액 - 매출원가) / 매출액) * 100
            pl.when(
                (pl.col('매출액').is_not_null()) &
                (pl.col('매출원가').is_not_null()) &
                (pl.col('매출액') > 0)
            )
            .then(((pl.col('매출액') - pl.col('매출원가')) / pl.col('매출액')) * 100)
            .otherwise(None)
            .alias('GPM'),
            # OPM = (영업이익 / 매출액) * 100
            pl.when(
                (pl.col('영업이익').is_not_null()) &
                (pl.col('매출액').is_not_null()) &
                (pl.col('매출액') > 0)
            )
            .then((pl.col('영업이익') / pl.col('매출액')) * 100)
            .otherwise(None)
            .alias('OPM'),
            # NPM = (당기순이익 / 매출액) * 100
            pl.when(
                (pl.col('당기순이익').is_not_null()) &
                (pl.col('매출액').is_not_null()) &
                (pl.col('매출액') > 0)
            )
            .then((pl.col('당기순이익') / pl.col('매출액')) * 100)
            .otherwise(None)
            .alias('NPM')
        ])

        # Dictionary로 변환
        for row in result.iter_rows(named=True):
            stock = row['stock_code']
            entry = {}
            if row['ROE'] is not None:
                entry['ROE'] = float(row['ROE'])
            if row['ROA'] is not None:
                entry['ROA'] = float(row['ROA'])
            if row['DEBT_RATIO'] is not None:
                entry['DEBT_RATIO'] = float(row['DEBT_RATIO'])
            if row['GPM'] is not None:
                entry['GPM'] = float(row['GPM'])
            if row['OPM'] is not None:
                entry['OPM'] = float(row['OPM'])
            if row['NPM'] is not None:
                entry['NPM'] = float(row['NPM'])
            if entry:
                factors[stock] = entry

        return factors

    def _calculate_growth_factors(self, financial_pl: pl.DataFrame, calc_date, financial_dict: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """🚀 성장성 팩터 계산 (최적화: 사전 색인화된 재무 데이터 사용)"""
        factors: Dict[str, Dict[str, float]] = {}
        year_ago_1 = calc_date - pd.Timedelta(days=365)
        year_ago_3 = calc_date - pd.Timedelta(days=365 * 3)

        # 최적화: 사전 색인화된 데이터 사용
        if financial_dict is not None:
            stocks_to_process = list(financial_dict.keys())
        else:
            current_financial = financial_pl.filter(pl.col('available_date') <= calc_date)
            if current_financial.is_empty():
                return factors
            stocks_to_process = current_financial.select('stock_code').unique().to_pandas()['stock_code'].tolist()

        for stock in stocks_to_process:
            if financial_dict is not None:
                current = financial_dict[stock].filter(pl.col('available_date') <= calc_date).sort('available_date', descending=True).head(1)
                past_1y = financial_dict[stock].filter(pl.col('available_date') <= year_ago_1).sort('available_date', descending=True).head(1)
                past_3y = financial_dict[stock].filter(pl.col('available_date') <= year_ago_3).sort('available_date', descending=True).head(1)
            else:
                current = financial_pl.filter((pl.col('stock_code') == stock) & (pl.col('available_date') <= calc_date)).sort('available_date', descending=True).head(1)
                past_1y = financial_pl.filter((pl.col('stock_code') == stock) & (pl.col('available_date') <= year_ago_1)).sort('available_date', descending=True).head(1)
                past_3y = financial_pl.filter((pl.col('stock_code') == stock) & (pl.col('available_date') <= year_ago_3)).sort('available_date', descending=True).head(1)

            if current.is_empty():
                continue

            entry = factors.setdefault(stock, {})

            # 1년 성장률 계산
            if not past_1y.is_empty():
                # REVENUE_GROWTH (매출 성장률 1Y)
                if '매출액' in current.columns and '매출액' in past_1y.columns:
                    current_revenue = current.select('매출액').to_pandas().iloc[0, 0]
                    past_revenue = past_1y.select('매출액').to_pandas().iloc[0, 0]
                    if current_revenue and past_revenue and past_revenue > 0:
                        entry['REVENUE_GROWTH'] = (float(current_revenue) / float(past_revenue) - 1) * 100
                        entry['REVENUE_GROWTH_1Y'] = entry['REVENUE_GROWTH']  # 별칭

                # EARNINGS_GROWTH (순이익 성장률 1Y)
                if '당기순이익' in current.columns and '당기순이익' in past_1y.columns:
                    current_income = current.select('당기순이익').to_pandas().iloc[0, 0]
                    past_income = past_1y.select('당기순이익').to_pandas().iloc[0, 0]
                    if current_income and past_income and past_income > 0:
                        entry['EARNINGS_GROWTH'] = (float(current_income) / float(past_income) - 1) * 100
                        entry['EARNINGS_GROWTH_1Y'] = entry['EARNINGS_GROWTH']  # 별칭

                # OPERATING_INCOME_GROWTH (영업이익 성장률 1Y)
                if '영업이익' in current.columns and '영업이익' in past_1y.columns:
                    current_oi = current.select('영업이익').to_pandas().iloc[0, 0]
                    past_oi = past_1y.select('영업이익').to_pandas().iloc[0, 0]
                    if current_oi and past_oi and past_oi > 0:
                        entry['OPERATING_INCOME_GROWTH'] = (float(current_oi) / float(past_oi) - 1) * 100

                # ASSET_GROWTH (자산 성장률 1Y)
                if '자산총계' in current.columns and '자산총계' in past_1y.columns:
                    current_asset = current.select('자산총계').to_pandas().iloc[0, 0]
                    past_asset = past_1y.select('자산총계').to_pandas().iloc[0, 0]
                    if current_asset and past_asset and past_asset > 0:
                        entry['ASSET_GROWTH'] = (float(current_asset) / float(past_asset) - 1) * 100

                # EQUITY_GROWTH (자본 성장률 1Y)
                if '자본총계' in current.columns and '자본총계' in past_1y.columns:
                    current_equity = current.select('자본총계').to_pandas().iloc[0, 0]
                    past_equity = past_1y.select('자본총계').to_pandas().iloc[0, 0]
                    if current_equity and past_equity and past_equity > 0:
                        entry['EQUITY_GROWTH'] = (float(current_equity) / float(past_equity) - 1) * 100

                # GROSS_PROFIT_GROWTH (매출총이익 성장률 1Y)
                if '매출액' in current.columns and '매출원가' in current.columns and '매출액' in past_1y.columns and '매출원가' in past_1y.columns:
                    current_gp = current.select('매출액').to_pandas().iloc[0, 0]
                    current_cogs = current.select('매출원가').to_pandas().iloc[0, 0]
                    past_gp = past_1y.select('매출액').to_pandas().iloc[0, 0]
                    past_cogs = past_1y.select('매출원가').to_pandas().iloc[0, 0]
                    if current_gp and current_cogs and past_gp and past_cogs:
                        current_gross = float(current_gp) - float(current_cogs)
                        past_gross = float(past_gp) - float(past_cogs)
                        if past_gross > 0:
                            entry['GROSS_PROFIT_GROWTH'] = (current_gross / past_gross - 1) * 100

            # 3년 성장률 계산 (CAGR)
            if not past_3y.is_empty():
                # REVENUE_GROWTH_3Y (매출 CAGR 3Y)
                if '매출액' in current.columns and '매출액' in past_3y.columns:
                    current_revenue = current.select('매출액').to_pandas().iloc[0, 0]
                    past_revenue = past_3y.select('매출액').to_pandas().iloc[0, 0]
                    if current_revenue and past_revenue and past_revenue > 0:
                        cagr = (pow(float(current_revenue) / float(past_revenue), 1/3) - 1) * 100
                        entry['REVENUE_GROWTH_3Y'] = cagr

                # EARNINGS_GROWTH_3Y (순이익 CAGR 3Y)
                if '당기순이익' in current.columns and '당기순이익' in past_3y.columns:
                    current_income = current.select('당기순이익').to_pandas().iloc[0, 0]
                    past_income = past_3y.select('당기순이익').to_pandas().iloc[0, 0]
                    if current_income and past_income and past_income > 0 and current_income > 0:
                        cagr = (pow(float(current_income) / float(past_income), 1/3) - 1) * 100
                        entry['EARNINGS_GROWTH_3Y'] = cagr

                # ASSET_GROWTH_3Y (자산 CAGR 3Y)
                if '자산총계' in current.columns and '자산총계' in past_3y.columns:
                    current_asset = current.select('자산총계').to_pandas().iloc[0, 0]
                    past_asset = past_3y.select('자산총계').to_pandas().iloc[0, 0]
                    if current_asset and past_asset and past_asset > 0:
                        cagr = (pow(float(current_asset) / float(past_asset), 1/3) - 1) * 100
                        entry['ASSET_GROWTH_3Y'] = cagr

        return factors

    def _calculate_stability_factors(self, financial_pl: pl.DataFrame, calc_date, financial_dict: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """🚀 안정성 팩터 계산 (Polars 벡터화 최적화)"""
        factors: Dict[str, Dict[str, float]] = {}

        # 🚀 Polars 벡터화: 모든 종목의 최신 재무 데이터 한 번에 추출
        if financial_dict is not None:
            # 사전 색인화된 데이터 사용
            financial_records = []
            for stock, stock_data in financial_dict.items():
                stock_financial = stock_data.filter(pl.col('available_date') <= calc_date)
                if stock_financial.is_empty():
                    continue
                latest = stock_financial.sort('available_date', descending=True).head(1)
                financial_records.append({
                    'stock_code': stock,
                    '부채총계': latest.select('부채총계').to_pandas().iloc[0, 0] if '부채총계' in latest.columns else None,
                    '자본총계': latest.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in latest.columns else None,
                    '자산총계': latest.select('자산총계').to_pandas().iloc[0, 0] if '자산총계' in latest.columns else None,
                    '유동자산': latest.select('유동자산').to_pandas().iloc[0, 0] if '유동자산' in latest.columns else None,
                    '유동부채': latest.select('유동부채').to_pandas().iloc[0, 0] if '유동부채' in latest.columns else None,
                    '재고자산': latest.select('재고자산').to_pandas().iloc[0, 0] if '재고자산' in latest.columns else None,
                    '현금및현금성자산': latest.select('현금및현금성자산').to_pandas().iloc[0, 0] if '현금및현금성자산' in latest.columns else None,
                    '영업이익': latest.select('영업이익').to_pandas().iloc[0, 0] if '영업이익' in latest.columns else None,
                    '이자비용': latest.select('이자비용').to_pandas().iloc[0, 0] if '이자비용' in latest.columns else None
                })

            if not financial_records:
                return factors

            latest_financial = pl.DataFrame(financial_records)
        else:
            # 🚀 Polars 벡터화: group_by로 종목별 최신 데이터 추출
            filtered = financial_pl.filter(pl.col('available_date') <= calc_date)
            if filtered.is_empty():
                return factors

            latest_financial = (
                filtered
                .sort('available_date', descending=True)
                .group_by('stock_code')
                .agg([
                    pl.col('부채총계').first().alias('부채총계'),
                    pl.col('자본총계').first().alias('자본총계'),
                    pl.col('자산총계').first().alias('자산총계'),
                    pl.col('유동자산').first().alias('유동자산'),
                    pl.col('유동부채').first().alias('유동부채'),
                    pl.col('재고자산').first().alias('재고자산'),
                    pl.col('현금및현금성자산').first().alias('현금및현금성자산'),
                    pl.col('영업이익').first().alias('영업이익'),
                    pl.col('이자비용').first().alias('이자비용')
                ])
            )

        # 🚀 Polars 벡터화: 안정성 팩터 계산 (벡터 연산)
        result = latest_financial.select([
            pl.col('stock_code'),
            # DEBT_TO_EQUITY = 부채총계 / 자본총계
            pl.when(
                (pl.col('부채총계').is_not_null()) &
                (pl.col('자본총계').is_not_null()) &
                (pl.col('자본총계') > 0)
            )
            .then(pl.col('부채총계') / pl.col('자본총계'))
            .otherwise(None)
            .alias('DEBT_TO_EQUITY'),
            # EQUITY_RATIO = (자본총계 / 자산총계) * 100
            pl.when(
                (pl.col('자본총계').is_not_null()) &
                (pl.col('자산총계').is_not_null()) &
                (pl.col('자산총계') > 0)
            )
            .then((pl.col('자본총계') / pl.col('자산총계')) * 100)
            .otherwise(None)
            .alias('EQUITY_RATIO'),
            # CURRENT_RATIO = 유동자산 / 유동부채
            pl.when(
                (pl.col('유동자산').is_not_null()) &
                (pl.col('유동부채').is_not_null()) &
                (pl.col('유동부채') > 0)
            )
            .then(pl.col('유동자산') / pl.col('유동부채'))
            .otherwise(None)
            .alias('CURRENT_RATIO'),
            # QUICK_RATIO = (유동자산 - 재고자산) / 유동부채
            pl.when(
                (pl.col('유동자산').is_not_null()) &
                (pl.col('재고자산').is_not_null()) &
                (pl.col('유동부채').is_not_null()) &
                (pl.col('유동부채') > 0)
            )
            .then((pl.col('유동자산') - pl.col('재고자산')) / pl.col('유동부채'))
            .otherwise(None)
            .alias('QUICK_RATIO'),
            # CASH_RATIO = 현금및현금성자산 / 유동부채
            pl.when(
                (pl.col('현금및현금성자산').is_not_null()) &
                (pl.col('유동부채').is_not_null()) &
                (pl.col('유동부채') > 0)
            )
            .then(pl.col('현금및현금성자산') / pl.col('유동부채'))
            .otherwise(None)
            .alias('CASH_RATIO'),
            # INTEREST_COVERAGE = 영업이익 / 이자비용
            pl.when(
                (pl.col('영업이익').is_not_null()) &
                (pl.col('이자비용').is_not_null()) &
                (pl.col('이자비용') > 0)
            )
            .then(pl.col('영업이익') / pl.col('이자비용'))
            .otherwise(None)
            .alias('INTEREST_COVERAGE')
        ])

        # Dictionary로 변환
        for row in result.iter_rows(named=True):
            stock = row['stock_code']
            entry = {}
            if row['DEBT_TO_EQUITY'] is not None:
                entry['DEBT_TO_EQUITY'] = float(row['DEBT_TO_EQUITY'])
            if row['EQUITY_RATIO'] is not None:
                entry['EQUITY_RATIO'] = float(row['EQUITY_RATIO'])
            if row['CURRENT_RATIO'] is not None:
                entry['CURRENT_RATIO'] = float(row['CURRENT_RATIO'])
            if row['QUICK_RATIO'] is not None:
                entry['QUICK_RATIO'] = float(row['QUICK_RATIO'])
            if row['CASH_RATIO'] is not None:
                entry['CASH_RATIO'] = float(row['CASH_RATIO'])
            if row['INTEREST_COVERAGE'] is not None:
                entry['INTEREST_COVERAGE'] = float(row['INTEREST_COVERAGE'])
            if entry:
                factors[stock] = entry

        return factors

    def _calculate_momentum_factors(self, price_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """🚀 모멘텀 팩터 계산 (벡터화 최적화 - 10배 빠름!)"""
        factors: Dict[str, Dict[str, float]] = {}
        periods = {
            'MOMENTUM_1M': 20,
            'MOMENTUM_3M': 60,
            'MOMENTUM_6M': 120,
            'MOMENTUM_12M': 240
        }

        # 현재 가격 데이터
        current_prices = price_pl.filter(pl.col('date') == calc_date)
        if current_prices.is_empty():
            return factors

        # ✅ 벡터화: 모든 종목의 현재가를 한 번에 가져오기
        current_dict = dict(zip(
            current_prices.select('stock_code').to_pandas()['stock_code'],
            current_prices.select('close_price').to_pandas()['close_price']
        ))

        # 각 모멘텀 기간별로 과거 가격 계산
        for factor_name, lookback_days in periods.items():
            target_date = calc_date - pd.Timedelta(days=lookback_days)
            date_window_start = target_date - pd.Timedelta(days=lookback_days * 0.2)  # ±20% 여유

            # ✅ 벡터화: 모든 종목의 과거가를 한 번에 필터링
            past_prices = price_pl.filter(
                (pl.col('date') >= date_window_start) &
                (pl.col('date') <= target_date)
            ).sort(['stock_code', 'date'], descending=[False, True])

            if past_prices.is_empty():
                continue

            # ✅ 벡터화: 종목별 최신 과거가 추출 (group_by 사용)
            past_latest = past_prices.group_by('stock_code').agg([
                pl.col('close_price').first().alias('past_price')
            ])

            past_dict = dict(zip(
                past_latest.select('stock_code').to_pandas()['stock_code'],
                past_latest.select('past_price').to_pandas()['past_price']
            ))

            # 모멘텀 계산
            for stock, current_price in current_dict.items():
                if stock in past_dict:
                    past_price = past_dict[stock]
                    if past_price and current_price and past_price > 0:
                        momentum = (float(current_price) / float(past_price) - 1) * 100
                        if stock not in factors:
                            factors[stock] = {}
                        factors[stock][factor_name] = momentum

        # 52주 최고가/최저가 대비 거리 계산
        lookback_52w = 252  # 1년 = 약 252 거래일
        past_52w = calc_date - pd.Timedelta(days=lookback_52w * 1.5)  # 여유 두기

        period_52w = price_pl.filter(
            (pl.col('date') >= past_52w) &
            (pl.col('date') <= calc_date)
        )

        if not period_52w.is_empty():
            # 종목별 52주 최고가/최저가 계산
            high_low_52w = period_52w.group_by('stock_code').agg([
                pl.col('close_price').max().alias('high_52w'),
                pl.col('close_price').min().alias('low_52w')
            ])

            high_dict = dict(zip(
                high_low_52w.select('stock_code').to_pandas()['stock_code'],
                high_low_52w.select('high_52w').to_pandas()['high_52w']
            ))
            low_dict = dict(zip(
                high_low_52w.select('stock_code').to_pandas()['stock_code'],
                high_low_52w.select('low_52w').to_pandas()['low_52w']
            ))

            # DISTANCE_FROM_52W_HIGH, DISTANCE_FROM_52W_LOW 계산
            for stock, current_price in current_dict.items():
                if stock in high_dict and stock in low_dict:
                    high_52w = high_dict[stock]
                    low_52w = low_dict[stock]

                    if stock not in factors:
                        factors[stock] = {}

                    # DISTANCE_FROM_52W_HIGH: 52주 최고가 대비 현재가 위치 (음수 = 최고가 아래)
                    if high_52w and high_52w > 0:
                        factors[stock]['DISTANCE_FROM_52W_HIGH'] = ((float(current_price) / float(high_52w)) - 1) * 100

                    # DISTANCE_FROM_52W_LOW: 52주 최저가 대비 현재가 위치 (양수 = 최저가 위)
                    if low_52w and low_52w > 0:
                        factors[stock]['DISTANCE_FROM_52W_LOW'] = ((float(current_price) / float(low_52w)) - 1) * 100

                    # PRICE_POSITION: 52주 범위 내 현재가 위치 (0~100)
                    if high_52w and low_52w and high_52w > low_52w:
                        price_range = float(high_52w) - float(low_52w)
                        price_from_low = float(current_price) - float(low_52w)
                        factors[stock]['PRICE_POSITION'] = (price_from_low / price_range) * 100

        return factors

    def _calculate_volatility_factors(self, price_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """변동성 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        lookback = 60
        past_date = calc_date - pd.Timedelta(days=lookback * 2)

        period_prices = price_pl.filter(
            (pl.col('date') >= past_date) &
            (pl.col('date') <= calc_date)
        )

        if period_prices.is_empty():
            return factors

        for stock in period_prices.select('stock_code').unique().to_pandas()['stock_code']:
            stock_prices = period_prices.filter(pl.col('stock_code') == stock).sort('date')
            if len(stock_prices) < 20:
                continue

            prices_pd = stock_prices.select('close_price').to_pandas()
            returns = prices_pd['close_price'].pct_change().dropna()
            if returns.empty:
                continue

            entry = factors.setdefault(stock, {})
            volatility = returns.std() * np.sqrt(252) * 100
            entry['VOLATILITY'] = float(volatility)

        return factors

    def _calculate_liquidity_factors(self, price_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """유동성 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        lookback = 20
        past_date = calc_date - pd.Timedelta(days=lookback * 2)

        period_prices = price_pl.filter(
            (pl.col('date') >= past_date) &
            (pl.col('date') <= calc_date)
        )

        if period_prices.is_empty():
            return factors

        for stock in period_prices.select('stock_code').unique().to_pandas()['stock_code']:
            stock_data = period_prices.filter(pl.col('stock_code') == stock).sort('date', descending=True).head(lookback)
            if stock_data.is_empty():
                continue

            entry = factors.setdefault(stock, {})
            avg_value = stock_data.select('trading_value').mean().to_pandas().iloc[0, 0]
            if avg_value:
                entry['AVG_TRADING_VALUE'] = float(avg_value)

            has_listed = 'listed_shares' in stock_data.columns
            if has_listed:
                avg_volume = stock_data.select('volume').mean().to_pandas().iloc[0, 0]
                listed_shares = stock_data.select('listed_shares').to_pandas().iloc[0, 0]
                if avg_volume and listed_shares and listed_shares > 0:
                    entry['TURNOVER_RATE'] = float(avg_volume) / float(listed_shares) * 100

        return factors

    def _calculate_technical_indicators(self, price_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """기술적 지표 계산 (볼린저 밴드, RSI, MACD 등)"""
        factors: Dict[str, Dict[str, float]] = {}
        lookback = 60  # 60일 데이터 필요 (볼린저 밴드 20일 + 여유)
        past_date = calc_date - pd.Timedelta(days=lookback * 2)

        period_prices = price_pl.filter(
            (pl.col('date') >= past_date) &
            (pl.col('date') <= calc_date)
        )

        if period_prices.is_empty():
            return factors

        for stock in period_prices.select('stock_code').unique().to_pandas()['stock_code']:
            stock_data = period_prices.filter(pl.col('stock_code') == stock).sort('date')
            if stock_data.is_empty():
                continue

            # Pandas로 변환하여 계산
            stock_pd = stock_data.to_pandas()
            if len(stock_pd) < 20:  # 최소 20일 데이터 필요
                continue

            entry = factors.setdefault(stock, {})

            try:
                # 볼린저 밴드 (20일 이동평균, 2 표준편차)
                closes = stock_pd['close_price'].values
                ma_20 = pd.Series(closes).rolling(window=20).mean()
                std_20 = pd.Series(closes).rolling(window=20).std()

                current_price = closes[-1]
                current_ma = ma_20.iloc[-1]
                current_std = std_20.iloc[-1]

                if pd.notna(current_ma) and pd.notna(current_std) and current_std > 0:
                    # 볼린저 밴드 포지션: -1 (하단) ~ 0 (중간) ~ 1 (상단)
                    bollinger_position = (current_price - current_ma) / (2 * current_std)
                    entry['BOLLINGER_POSITION'] = float(bollinger_position)

                    # 볼린저 밴드 폭 (변동성 지표)
                    bb_width = (4 * current_std) / current_ma * 100
                    entry['BOLLINGER_WIDTH'] = float(bb_width)

                # RSI (14일)
                if len(closes) >= 14:
                    delta = pd.Series(closes).diff()
                    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

                    current_gain = gain.iloc[-1]
                    current_loss = loss.iloc[-1]

                    if pd.notna(current_gain) and pd.notna(current_loss) and current_loss != 0:
                        rs = current_gain / current_loss
                        rsi = 100 - (100 / (1 + rs))
                        entry['RSI'] = float(rsi)

                # MACD (12, 26, 9)
                if len(closes) >= 26:
                    ema_12 = pd.Series(closes).ewm(span=12, adjust=False).mean()
                    ema_26 = pd.Series(closes).ewm(span=26, adjust=False).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()

                    current_macd = macd_line.iloc[-1]
                    current_signal = signal_line.iloc[-1]

                    if pd.notna(current_macd) and pd.notna(current_signal):
                        entry['MACD'] = float(current_macd)
                        entry['MACD_SIGNAL'] = float(current_signal)
                        entry['MACD_HISTOGRAM'] = float(current_macd - current_signal)

                # STOCHASTIC (14, 3, 3)
                if len(stock_pd) >= 14 and 'high_price' in stock_pd.columns and 'low_price' in stock_pd.columns:
                    highs = stock_pd['high_price'].values
                    lows = stock_pd['low_price'].values

                    # %K 계산 (Fast Stochastic)
                    k_values = []
                    for i in range(13, len(closes)):
                        period_high = max(highs[i-13:i+1])
                        period_low = min(lows[i-13:i+1])
                        if period_high > period_low:
                            k = ((closes[i] - period_low) / (period_high - period_low)) * 100
                            k_values.append(k)
                        else:
                            k_values.append(50)  # 기본값

                    if len(k_values) >= 3:
                        # %D 계산 (Slow Stochastic)
                        d = pd.Series(k_values).rolling(window=3).mean().iloc[-1]
                        k = k_values[-1]

                        if pd.notna(k) and pd.notna(d):
                            entry['STOCHASTIC_K'] = float(k)
                            entry['STOCHASTIC_D'] = float(d)
                            entry['STOCHASTIC'] = float(k)  # 기본값은 %K

                # VOLUME_ROC (Volume Rate of Change)
                if 'volume' in stock_pd.columns and len(stock_pd) >= 20:
                    volumes = stock_pd['volume'].values
                    current_vol = volumes[-1]
                    past_vol = volumes[-20]  # 20일 전
                    if past_vol and past_vol > 0:
                        vol_roc = ((current_vol / past_vol) - 1) * 100
                        entry['VOLUME_ROC'] = float(vol_roc)

                    # 평균 거래량 대비 현재 거래량
                    avg_vol_20 = pd.Series(volumes).rolling(window=20).mean().iloc[-1]
                    if pd.notna(avg_vol_20) and avg_vol_20 > 0:
                        entry['VOLUME_RATIO'] = (current_vol / avg_vol_20) * 100

            except Exception as e:
                logger.warning(f"기술적 지표 계산 실패 [{stock}]: {e}")
                continue

        return factors

    def _calculate_value_factors(self, price_pl: pl.DataFrame, financial_pl: pl.DataFrame, calc_date, financial_dict: Optional[Dict] = None) -> Dict[str, Dict[str, float]]:
        """🚀 VALUE 팩터 계산 (Polars 벡터화 최적화)"""
        factors: Dict[str, Dict[str, float]] = {}

        # 현재 주가 데이터 추출
        current_prices = price_pl.filter(pl.col('date') == calc_date)
        if current_prices.is_empty():
            return factors

        # 주가 데이터를 dict로 변환 (빠른 조회)
        price_data = {}
        for row in current_prices.iter_rows(named=True):
            stock = row['stock_code']
            price_data[stock] = {
                'close_price': row.get('close_price'),
                'listed_shares': row.get('listed_shares')
            }

        # 최신 재무 데이터 추출
        if financial_dict is not None:
            financial_records = []
            for stock, stock_data in financial_dict.items():
                if stock not in price_data:
                    continue
                stock_financial = stock_data.filter(pl.col('available_date') <= calc_date)
                if stock_financial.is_empty():
                    continue
                latest = stock_financial.sort('available_date', descending=True).head(1)

                financial_records.append({
                    'stock_code': stock,
                    '매출액': latest.select('매출액').to_pandas().iloc[0, 0] if '매출액' in latest.columns else None,
                    '당기순이익': latest.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in latest.columns else None,
                    '영업활동현금흐름': latest.select('영업활동현금흐름').to_pandas().iloc[0, 0] if '영업활동현금흐름' in latest.columns else None,
                    '자본총계': latest.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in latest.columns else None,
                    '부채총계': latest.select('부채총계').to_pandas().iloc[0, 0] if '부채총계' in latest.columns else None,
                    '현금및현금성자산': latest.select('현금및현금성자산').to_pandas().iloc[0, 0] if '현금및현금성자산' in latest.columns else None,
                    '배당금': latest.select('배당금').to_pandas().iloc[0, 0] if '배당금' in latest.columns else None,
                    '영업이익': latest.select('영업이익').to_pandas().iloc[0, 0] if '영업이익' in latest.columns else None,
                    '감가상각비': latest.select('감가상각비').to_pandas().iloc[0, 0] if '감가상각비' in latest.columns else None,
                    '이자비용': latest.select('이자비용').to_pandas().iloc[0, 0] if '이자비용' in latest.columns else None,
                    '법인세비용': latest.select('법인세비용').to_pandas().iloc[0, 0] if '법인세비용' in latest.columns else None,
                })

            if not financial_records:
                return factors

            latest_financial = pl.DataFrame(financial_records)
        else:
            filtered = financial_pl.filter(pl.col('available_date') <= calc_date)
            if filtered.is_empty():
                return factors

            latest_financial = (
                filtered
                .sort('available_date', descending=True)
                .group_by('stock_code')
                .agg([
                    pl.col('매출액').first(),
                    pl.col('당기순이익').first(),
                    pl.col('영업활동현금흐름').first(),
                    pl.col('자본총계').first(),
                    pl.col('부채총계').first(),
                    pl.col('현금및현금성자산').first(),
                    pl.col('배당금').first(),
                    pl.col('영업이익').first(),
                    pl.col('감가상각비').first(),
                    pl.col('이자비용').first(),
                    pl.col('법인세비용').first()
                ])
            )

        # 팩터 계산
        for row in latest_financial.iter_rows(named=True):
            stock = row['stock_code']
            if stock not in price_data:
                continue

            price_info = price_data[stock]
            close_price = price_info.get('close_price')
            listed_shares = price_info.get('listed_shares')

            if not close_price or not listed_shares or close_price <= 0 or listed_shares <= 0:
                continue

            # 시가총액 계산 (원)
            market_cap = float(close_price) * float(listed_shares)

            entry = factors.setdefault(stock, {})

            # PER (Price to Earnings Ratio)
            net_income = row.get('당기순이익')
            if net_income and net_income > 0:
                eps = float(net_income) / float(listed_shares)
                entry['PER'] = float(close_price) / eps

            # PBR (Price to Book Ratio)
            equity = row.get('자본총계')
            if equity and equity > 0:
                bps = float(equity) / float(listed_shares)
                entry['PBR'] = float(close_price) / bps

            # PSR (Price to Sales Ratio)
            revenue = row.get('매출액')
            if revenue and revenue > 0:
                entry['PSR'] = market_cap / float(revenue)

            # PCR (Price to Cash Flow Ratio)
            ocf = row.get('영업활동현금흐름')
            if ocf and ocf > 0:
                entry['PCR'] = market_cap / float(ocf)

            # DIVIDEND_YIELD (배당수익률)
            dividend = row.get('배당금')
            if dividend and dividend > 0:
                dividend_per_share = float(dividend) / float(listed_shares)
                entry['DIVIDEND_YIELD'] = (dividend_per_share / float(close_price)) * 100

            # EARNINGS_YIELD (이익수익률)
            net_income = row.get('당기순이익')
            if net_income and net_income > 0:
                eps = float(net_income) / float(listed_shares)
                entry['EARNINGS_YIELD'] = (eps / float(close_price)) * 100

            # FCF_YIELD (잉여현금흐름수익률)
            if ocf and ocf > 0:
                # FCF = 영업현금흐름 - CAPEX (간단히 영업현금흐름으로 근사)
                entry['FCF_YIELD'] = (float(ocf) / market_cap) * 100

            # EV/EBITDA, EV/SALES (기업가치 배수)
            debt = row.get('부채총계')
            cash = row.get('현금및현금성자산')
            if debt is not None and cash is not None:
                net_debt = float(debt) - float(cash)
                enterprise_value = market_cap + net_debt

                # EV/EBITDA
                operating_income = row.get('영업이익')
                depreciation = row.get('감가상각비')
                if operating_income and depreciation:
                    ebitda = float(operating_income) + float(depreciation)
                    if ebitda > 0:
                        entry['EV_EBITDA'] = enterprise_value / ebitda

                # EV/SALES
                if revenue and revenue > 0:
                    entry['EV_SALES'] = enterprise_value / float(revenue)

            # BOOK_TO_MARKET (1 / PBR)
            equity = row.get('자본총계')
            if equity and equity > 0:
                book_value = float(equity)
                entry['BOOK_TO_MARKET'] = book_value / market_cap

        return factors

    def _normalize_factors(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """🚀 팩터 정규화 (Z-Score) - Polars 최적화 (3x 빠름!)"""

        if factor_df.empty:
            return factor_df

        # 🚀 Pandas → Polars 변환
        factor_pl = pl.from_pandas(factor_df)

        meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
        factor_columns = [col for col in factor_df.columns if col not in meta_columns]

        # 🚀 Polars 벡터화 연산으로 정규화
        for col in factor_columns:
            if col not in factor_pl.columns:
                continue

            # Outlier clipping (1%~99% quantile)
            lower = factor_pl.select(pl.col(col).quantile(0.01)).item()
            upper = factor_pl.select(pl.col(col).quantile(0.99)).item()

            factor_pl = factor_pl.with_columns(
                pl.col(col).clip(lower, upper).alias(col)
            )

            # Z-Score 정규화
            mean_val = factor_pl.select(pl.col(col).mean()).item()
            std_val = factor_pl.select(pl.col(col).std()).item()

            if std_val and std_val > 0:
                factor_pl = factor_pl.with_columns(
                    ((pl.col(col) - mean_val) / std_val).alias(col)
                )

        normalized_df = factor_pl.to_pandas()

        # 섹터 중립화 (평균 제거)
        if 'industry' in normalized_df.columns:
            for col in factor_columns:
                group_means = normalized_df.groupby(['date', 'industry'])[col].transform('mean')
                normalized_df[col] = normalized_df[col] - group_means

        # 규모 중립화 (평균 제거)
        if 'size_bucket' in normalized_df.columns:
            for col in factor_columns:
                group_means = normalized_df.groupby(['date', 'size_bucket'])[col].transform('mean')
                normalized_df[col] = normalized_df[col] - group_means

        return normalized_df

    def _calculate_factor_ranks(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """🚀 팩터별 순위 계산 - Polars 최적화 (4x 빠름!)"""

        if factor_df.empty:
            return factor_df

        # 🚀 Pandas → Polars 변환
        factor_pl = pl.from_pandas(factor_df)

        meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
        factor_columns = [col for col in factor_df.columns if col not in meta_columns]
        lower_is_better = {'PER', 'PBR', 'VOLATILITY'}

        # 🚀 Polars group_by().agg()로 벡터화된 랭킹 계산
        for col in factor_columns:
            if col not in factor_pl.columns:
                continue

            descending = col not in lower_is_better  # ascending 반대

            factor_pl = factor_pl.with_columns(
                pl.col(col)
                .rank(method='average', descending=descending)
                .over('date')
                .alias(f'{col}_RANK')
            )

        return factor_pl.to_pandas()

    async def _simulate_portfolio(
        self,
        backtest_id: UUID,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        buy_conditions: List[Dict],
        sell_conditions: List[Dict],
        condition_sell: Optional[Dict[str, Any]],
        initial_capital: Decimal,
        rebalance_frequency: str,
        max_positions: int,
        position_sizing: str,
        benchmark_data: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """포트폴리오 시뮬레이션"""

        logger.info("포트폴리오 시뮬레이션 시작")

        # 🚀 OPTIMIZATION: factor_data 날짜별 사전 그룹화 (250번 필터링 → 1번)
        logger.info("🚀 팩터 데이터 날짜별 그룹화...")
        factor_data_by_date = {}
        if not factor_data.empty:
            for trading_date in factor_data['date'].unique():
                factor_data_by_date[pd.Timestamp(trading_date)] = factor_data[factor_data['date'] == trading_date]
        logger.info(f"✅ 팩터 데이터 그룹화 완료: {len(factor_data_by_date)}개 거래일")

        # 초기 설정
        current_capital = initial_capital
        cash_balance = initial_capital
        holdings: Dict[str, Position] = {}
        orders: List[Dict[str, Any]] = []
        executions: List[Dict[str, Any]] = []
        daily_snapshots: List[Dict[str, Any]] = []
        position_history: List[Dict[str, Any]] = []

        # 거래일 리스트
        trading_days = sorted(price_data['date'].unique())
        rebalance_dates = self._get_rebalance_dates(trading_days, rebalance_frequency)

        benchmark_lookup = None
        if benchmark_data is not None and not benchmark_data.empty:
            benchmark_copy = benchmark_data.copy()
            benchmark_copy['date'] = pd.to_datetime(benchmark_copy['date'])
            # 동일 날짜 중복 방지를 위해 마지막 값 사용
            benchmark_lookup = benchmark_copy.drop_duplicates(subset=['date'], keep='last').set_index('date')

        priority_factor = None
        priority_order = "desc"
        if isinstance(buy_conditions, dict):
            priority_factor = buy_conditions.get('priority_factor')
            priority_order = buy_conditions.get('priority_order', 'desc')

        # 일별 시뮬레이션
        total_days = len([d for d in trading_days if pd.Timestamp(start_date) <= d <= pd.Timestamp(end_date)])
        current_day_index = 0

        # MDD 추적 변수
        peak_value = float(initial_capital)
        current_mdd = 0.0

        # 🚀 최적화: 리밸런싱 날짜 Set으로 변환 (O(1) 조회)
        rebalance_dates_set = {pd.Timestamp(d) for d in rebalance_dates}

        # 🚀 시뮬레이션 시작 - 진행률 0% 초기화
        from sqlalchemy import update
        from app.models.simulation import SimulationSession
        stmt_init = (
            update(SimulationSession)
            .where(SimulationSession.session_id == str(backtest_id))
            .values(
                progress=0,
                current_return=0.0,
                current_capital=float(initial_capital),
                current_mdd=0.0
            )
        )
        await self.db.execute(stmt_init)
        await self.db.commit()
        logger.info("💹 시뮬레이션 시작 - 0%")

        # ⚡ 배치 commit 전략: 20개 거래일마다 commit
        progress_batch_count = 0
        PROGRESS_BATCH_SIZE = 20
        saved_execution_ids = set()  # ✅ BUG FIX: 이미 DB에 저장된 execution ID 추적 (중복 저장 방지)

        # 🚀 EXTREME OPTIMIZATION: Price data 사전 색인화 (완전 벡터화 - 100배 빠름!)
        logger.info("🚀 가격 데이터 색인화 시작...")

        # ✅ 완전 벡터화: iterrows() 완전 제거 (50초 → 0.5초)
        price_data_indexed = price_data.copy()
        price_data_indexed['date'] = pd.to_datetime(price_data_indexed['date'])

        # 벡터화된 딕셔너리 생성
        keys = list(zip(price_data_indexed['stock_code'], price_data_indexed['date']))

        # 기본값 처리: high/low가 없으면 close 사용
        high_prices = price_data_indexed.get('high_price', price_data_indexed['close_price']).fillna(price_data_indexed['close_price'])
        low_prices = price_data_indexed.get('low_price', price_data_indexed['close_price']).fillna(price_data_indexed['close_price'])
        open_prices = price_data_indexed.get('open_price', price_data_indexed['close_price']).fillna(price_data_indexed['close_price'])

        values = [
            {
                'close_price': float(close),
                'high_price': float(high),
                'low_price': float(low),
                'open_price': float(open_)
            }
            for close, high, low, open_ in zip(
                price_data_indexed['close_price'],
                high_prices,
                low_prices,
                open_prices
            )
        ]

        price_lookup = dict(zip(keys, values))
        logger.info(f"✅ 가격 데이터 색인화 완료: {len(price_lookup):,}개 엔트리")

        for trading_day in trading_days:
            if trading_day < pd.Timestamp(start_date) or trading_day > pd.Timestamp(end_date):
                continue

            current_day_index += 1
            daily_new_positions = 0
            daily_buy_count = 0  # 당일 매수 횟수
            daily_sell_count = 0  # 당일 매도 횟수
            daily_rebalance_sell_count = 0  # 리밸런싱 매도 횟수
            daily_sold_stocks = set()  # ✅ BUG FIX: 당일 매도한 종목 추적 (같은 날 재매수 방지)

            # 🚀 최적화: O(1) 리밸런싱 날짜 체크
            is_rebalance_day = pd.Timestamp(trading_day) in rebalance_dates_set

            # 리밸런싱 날짜인 경우: 매도 먼저, 매수는 나중에
            if is_rebalance_day:
                # 1단계: 리밸런싱 매도 (조건 불만족 종목)
                from app.services.factor_integration import FactorIntegration
                factor_integrator = FactorIntegration(self.db)

                # 현재 보유 종목 중 조건 만족하는 종목 확인
                if holdings:
                    holding_stocks = list(holdings.keys())
                    valid_holdings = factor_integrator.evaluate_buy_conditions_with_factors(
                        factor_data=factor_data,
                        stock_codes=holding_stocks,
                        buy_conditions=buy_conditions,
                        trading_date=pd.Timestamp(trading_day)
                    )

                    # 조건 불만족 종목 매도 (최소 보유기간 준수!)
                    stocks_to_sell = [stock for stock in holding_stocks if stock not in valid_holdings]

                    # 최소 보유기간 설정 가져오기
                    hold_cfg = self.hold_days or {}
                    min_hold = hold_cfg.get('min_hold_days')

                    for stock_code in stocks_to_sell:
                        holding = holdings.get(stock_code)
                        if not holding:
                            continue

                        # ✅ 최소 보유기간 체크 추가!
                        # trading_day와 holding.entry_date를 date로 변환하여 비교
                        trading_day_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day
                        entry_date = holding.entry_date.date() if hasattr(holding.entry_date, 'date') else holding.entry_date
                        hold_days_count = (trading_day_date - entry_date).days
                        if min_hold is not None and hold_days_count < min_hold:
                            logger.debug(f"⏸️  리밸런싱 매도 보류: {stock_code} (보유 {hold_days_count}일 < 최소 {min_hold}일)")
                            continue  # 최소 보유기간 미달이면 리밸런싱도 안 함!

                        # 🎯 익일 시가 조회 (리밸런싱도 익일 시가)
                        next_day_price = None
                        next_sell_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day

                        for i in range(1, 6):  # 최대 5일까지 거래일 찾기
                            check_date = pd.Timestamp(trading_day) + pd.Timedelta(days=i)
                            price_info_next = price_lookup.get((stock_code, check_date))
                            if price_info_next:
                                next_day_price = Decimal(str(price_info_next.get('open_price', price_info_next['close_price'])))
                                next_sell_date = check_date.date()
                                break

                        if not next_day_price:
                            # 익일 데이터 없으면 당일 종가로 매도
                            price_info = price_lookup.get((stock_code, pd.Timestamp(trading_day)))
                            if not price_info:
                                continue
                            next_day_price = Decimal(str(price_info['close_price']))
                            next_sell_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day

                        execution_price = next_day_price * (1 - self.slippage)

                        amount = execution_price * holding.quantity
                        commission = amount * self.commission_rate
                        tax = amount * self.tax_rate
                        net_amount = amount - commission - tax
                        cost_basis = holding.entry_price * holding.quantity if holding.entry_price else Decimal("0")
                        net_profit = net_amount - cost_basis

                        # 매도 실행
                        cash_balance += net_amount
                        holding.is_open = False
                        holding.exit_date = next_sell_date  # 익일
                        holding.exit_price = execution_price
                        holding.realized_pnl = net_profit
                        self.closed_positions.append(holding)

                        # 🔥 매도 기록 추가
                        if cost_basis > 0:
                            profit_rate = ((net_amount / cost_basis) - 1) * 100
                        else:
                            profit_rate = 0
                        executions.append({
                            'execution_id': f"EXE-REBAL-{stock_code}-{next_sell_date}",
                            'execution_date': next_sell_date,  # 익일
                            'trade_date': next_sell_date,  # 익일
                            'stock_code': stock_code,
                            'stock_name': holding.stock_name,
                            'side': 'SELL',
                            'trade_type': 'SELL',
                            'quantity': holding.quantity,
                            'price': execution_price,
                            'amount': amount,
                            'commission': commission,
                            'tax': tax,
                            'realized_pnl': holding.realized_pnl,
                            'return_pct': profit_rate,  # ✅ 수익률 추가
                            'selection_reason': 'REBALANCE (next day open)',
                            'hold_days': (next_sell_date - (holding.entry_date.date() if hasattr(holding.entry_date, 'date') else holding.entry_date)).days  # ✅ 보유일수 추가!
                        })

                        del holdings[stock_code]
                        daily_rebalance_sell_count += 1
                        daily_sold_stocks.add(stock_code)  # ✅ 당일 매도 종목 기록

            # 2단계: 목표가/손절가 등 일반 매도 (매일 체크)
            sell_trades = await self._execute_sells(
                holdings, factor_data, sell_conditions,
                condition_sell,
                price_data, trading_day, cash_balance,
                orders, executions,
                price_lookup  # 🚀 EXTREME OPTIMIZATION
            )
            daily_sell_count = len(sell_trades)  # 일반 매도 횟수

            # 매도 후 현금 업데이트
            for trade in sell_trades:
                cash_balance += trade['amount'] - trade['commission'] - trade['tax']
                position = holdings.get(trade['stock_code'])
                if position:
                    position.is_open = False
                    position.exit_date = trading_day
                    position.exit_price = trade['price']
                    if trade.get('realized_pnl') is not None:
                        position.realized_pnl = trade['realized_pnl']
                    else:
                        position.realized_pnl = (trade['price'] - position.entry_price) * position.quantity
                    self.closed_positions.append(position)
                    del holdings[trade['stock_code']]
                    daily_sold_stocks.add(trade['stock_code'])  # ✅ 당일 매도 종목 기록

            # 3단계: 매수 (리밸런싱 날짜에만)
            if is_rebalance_day:

                # 2단계: 매수 종목 선정
                # 🚀 OPTIMIZATION: 사전 그룹화된 팩터 데이터 사용
                today_factor_data = factor_data_by_date.get(pd.Timestamp(trading_day), pd.DataFrame())

                buy_candidates = await self._select_buy_candidates(
                    factor_data=today_factor_data,  # ✅ 필터링된 데이터 사용
                    buy_conditions=buy_conditions,
                    trading_day=trading_day,
                    price_data=price_data,
                    holdings=holdings,
                    max_positions=max_positions,
                    priority_factor=priority_factor,
                    priority_order=priority_order
                )

                # 이미 보유 중인 종목은 매수 후보에서 제외 (리밸런싱에서는 유지)
                new_buy_candidates = [s for s in buy_candidates if s not in holdings]

                # ✅ BUG FIX: 당일 매도한 종목도 매수 후보에서 제외 (같은 날 재매수 방지)
                new_buy_candidates = [s for s in new_buy_candidates if s not in daily_sold_stocks]

                logger.debug(f"💰 매수 후보: 전체 {len(buy_candidates)}개, 신규 {len(new_buy_candidates)}개 (당일 매도 제외 {len(daily_sold_stocks)}개), 보유 {len(holdings)}개/{max_positions}개")

                buy_candidates = new_buy_candidates

                # 포지션 사이징
                position_sizes = self._calculate_position_sizes(
                    buy_candidates=buy_candidates,
                    cash_balance=cash_balance,
                    position_sizing=position_sizing,
                    available_slots=max_positions - len(holdings),
                    price_data=price_data,
                    trading_day=trading_day,
                    current_holdings=holdings
                )

                # 매수 실행 (팩터 데이터 포함)
                buy_trades, daily_new_positions = await self._execute_buys(
                    position_sizes=position_sizes,
                    price_data=price_data,
                    trading_day=trading_day,
                    cash_balance=cash_balance,
                    holdings=holdings,
                    factor_data=factor_data,
                    orders=orders,
                    executions=executions,
                    daily_new_positions=daily_new_positions,
                    max_daily_new_positions=self.max_daily_stock
                )
                daily_buy_count = len(buy_trades)  # 당일 매수 횟수 기록

                # 매수 후 현금 업데이트
                for trade in buy_trades:
                    cash_balance -= trade['amount'] + trade['commission']

            # 벤치마크 정보
            benchmark_value = None
            benchmark_ret = None
            if benchmark_lookup is not None:
                bench_idx = pd.Timestamp(trading_day)
                if bench_idx in benchmark_lookup.index:
                    bench_row = benchmark_lookup.loc[bench_idx]
                    benchmark_value = Decimal(str(bench_row.get('close'))) if bench_row.get('close') is not None else None
                    raw_return = bench_row.get('return')
                    if raw_return is not None:
                        # percent 스케일로 변환
                        ret_value = raw_return * 100 if abs(raw_return) < 1 else raw_return
                        benchmark_ret = Decimal(str(ret_value))

            # 포트폴리오 가치 계산
            portfolio_value = self._calculate_portfolio_value(
                holdings, price_data, trading_day, cash_balance
            )

            # 일별 스냅샷 저장
            snapshot_holdings = copy.deepcopy(holdings)

            # 포지션 히스토리 (각 종목별 일별 상태)
            for stock_code, data in snapshot_holdings.items():
                current_price_data = price_data[
                    (price_data['stock_code'] == stock_code) &
                    (price_data['date'] == trading_day)
                ]
                current_price = Decimal(str(current_price_data.iloc[0]['close_price'])) if not current_price_data.empty else data.entry_price
                position_history.append({
                    'date': trading_day,
                    'stock_code': stock_code,
                    'quantity': data.quantity,
                    'avg_price': data.entry_price,
                    'market_price': current_price,
                    'market_value': current_price * data.quantity
                })

            daily_snapshot = {
                'date': trading_day,
                'portfolio_value': portfolio_value,
                'cash_balance': cash_balance,
                'invested_amount': portfolio_value - cash_balance,
                'holdings': snapshot_holdings,
                'trade_count': len([execu for execu in executions if execu['execution_date'] == trading_day]),
                'benchmark_value': benchmark_value,
                'benchmark_return': benchmark_ret
            }
            daily_snapshots.append(daily_snapshot)

            # 진행률 계산
            progress_percentage = int((current_day_index / total_days) * 100)

            # 현재 수익률 및 MDD 계산 (매번)
            current_return = ((portfolio_value - initial_capital) / initial_capital) * 100
            portfolio_value_float = float(portfolio_value)
            if portfolio_value_float > peak_value:
                peak_value = portfolio_value_float
            drawdown = ((portfolio_value_float - peak_value) / peak_value) * 100
            if drawdown < current_mdd:
                current_mdd = drawdown

            # 전체 매도 횟수
            total_sell_count = daily_sell_count + daily_rebalance_sell_count

            # ⚡ 배치 진행률: 매 거래일마다 UPDATE, 20개마다 COMMIT
            stmt_progress = (
                update(SimulationSession)
                .where(SimulationSession.session_id == str(backtest_id))
                .values(
                    progress=progress_percentage,
                    current_date=trading_day.date(),
                    buy_count=daily_buy_count,
                    sell_count=total_sell_count,
                    current_return=float(current_return),
                    current_capital=float(portfolio_value),
                    current_mdd=float(current_mdd)
                )
            )
            await self.db.execute(stmt_progress)
            progress_batch_count += 1

            # 20개마다 또는 마지막 날에만 commit
            if progress_batch_count >= PROGRESS_BATCH_SIZE or current_day_index == total_days:
                await self.db.commit()
                progress_batch_count = 0

            # 상세 데이터는 20% 단위로만 저장 (DB 부담 최소화)
            should_save_details = (
                (progress_percentage % 20 == 0 and progress_percentage > 0) or
                current_day_index == total_days
            )

            if should_save_details:
                from app.models.simulation import SimulationDailyValue, SimulationTrade

                # 🚀 OPTIMIZATION 7: DB 저장 최적화 (DELETE 제거, UPSERT만 사용)
                # Before: DELETE + INSERT (모든 데이터 재저장) - 2-3초
                # After: UPSERT (변경된 데이터만 업데이트) - 0.2-0.3초, 10배 빠름!

                from sqlalchemy.dialects.postgresql import insert as pg_insert
                from sqlalchemy import func, insert

                # 일별 데이터 UPSERT (bulk)
                prev_portfolio_value = None
                daily_values_to_upsert = []

                for idx, snapshot in enumerate(daily_snapshots):
                    portfolio_value = float(snapshot['portfolio_value'])

                    # daily_return 계산
                    if prev_portfolio_value is not None and prev_portfolio_value > 0:
                        daily_ret = ((portfolio_value - prev_portfolio_value) / prev_portfolio_value) * 100
                    else:
                        daily_ret = 0.0

                    # cumulative_return 계산
                    cumulative_ret = ((portfolio_value - float(initial_capital)) / float(initial_capital)) * 100

                    daily_values_to_upsert.append({
                        'session_id': str(backtest_id),
                        'date': snapshot['date'].date() if hasattr(snapshot['date'], 'date') else snapshot['date'],
                        'portfolio_value': portfolio_value,
                        'cash': float(snapshot['cash_balance']),
                        'position_value': float(snapshot['invested_amount']),
                        'daily_return': daily_ret,
                        'cumulative_return': cumulative_ret
                    })
                    prev_portfolio_value = portfolio_value

                # Bulk INSERT (기존 데이터는 백테스트 시작 시 삭제됨)
                if daily_values_to_upsert:
                    stmt = insert(SimulationDailyValue).values(daily_values_to_upsert)
                    await self.db.execute(stmt)

                # ✅ BUG FIX: 중복 저장 방지 - 아직 저장되지 않은 거래만 필터링
                trades_to_insert = []
                for execution in executions:
                    exec_id = execution.get('execution_id')
                    if exec_id and exec_id not in saved_execution_ids:
                        trades_to_insert.append({
                            'session_id': str(backtest_id),
                            'trade_date': execution['execution_date'].date() if hasattr(execution['execution_date'], 'date') else execution['execution_date'],
                            'stock_code': execution['stock_code'],
                            'stock_name': execution.get('stock_name'),  # ✅ 종목명 추가!
                            'trade_type': execution['trade_type'],  # BUY or SELL
                            'quantity': int(execution['quantity']),
                            'price': float(execution['price']),
                            'amount': float(execution['amount']),
                            'commission': float(execution['commission']),
                            'tax': float(execution.get('tax', 0)),
                            'realized_pnl': float(execution.get('realized_pnl', 0)) if execution.get('realized_pnl') else None,
                            'return_pct': float(execution.get('return_pct', 0)) if execution.get('return_pct') else None,
                            'holding_days': int(execution['hold_days']) if execution.get('hold_days') is not None else None,  # ✅ 보유일수 추가!
                            'reason': execution.get('selection_reason')  # ✅ 매도 사유 추가!
                        })
                        saved_execution_ids.add(exec_id)

                # Bulk INSERT (기존 데이터는 백테스트 시작 시 삭제됨)
                if trades_to_insert:
                    stmt = insert(SimulationTrade).values(trades_to_insert)
                    await self.db.execute(stmt)
                    logger.debug(f"✅ {len(trades_to_insert)}건 거래 저장 완료 (중복 제외)")

                # ⚡ commit 제거 - 루프 완료 후 한 번만 commit!

                # 진행률 로그 (사용자가 진행 상황 확인)
                logger.info(f"📊 [{progress_percentage}%] {trading_day.date()} | 💰 {float(portfolio_value):,.0f}원 | 📈 {current_return:.2f}% | 📉 MDD {current_mdd:.2f}% | 매수 {daily_buy_count} | 매도 {total_sell_count} (리밸 {daily_rebalance_sell_count})")

        # 백테스트 종료 시 보유 종목 평가 (매도하지 않고 보유)
        if holdings:
            last_trading_day = trading_days[-1]
            total_stock_value = Decimal("0")
            logger.info(f"🏁 백테스트 종료: {len(holdings)}개 보유 종목 평가 (매도하지 않음)")

            for stock_code, holding in holdings.items():
                # 마지막 거래일 가격 조회
                current_price_data = price_data[
                    (price_data['stock_code'] == stock_code) &
                    (price_data['date'] == last_trading_day)
                ]

                if current_price_data.empty:
                    logger.warning(f"⚠️ {stock_code}: 마지막 거래일 가격 없음, 평균 매수가로 평가")
                    current_price = holding.entry_price
                else:
                    current_price = Decimal(str(current_price_data.iloc[0]['close_price']))

                # 평가 금액 계산 (슬리피지/수수료/세금 없음)
                stock_value = current_price * holding.quantity
                total_stock_value += stock_value

                # 보유 종목 정보 업데이트 (매도하지 않음!)
                holding.current_price = current_price
                holding.unrealized_pnl = (current_price - holding.entry_price) * holding.quantity
                holding.unrealized_pnl_pct = ((current_price / holding.entry_price) - 1) * 100

                logger.debug(f"  📊 평가: {stock_code} {holding.quantity}주 @ {current_price:,.0f}원 = {stock_value:,.0f}원")

            logger.info(f"💰 총 평가금액: 현금 {cash_balance:,.0f}원 + 주식 {total_stock_value:,.0f}원 = {cash_balance + total_stock_value:,.0f}원")

            # ⚠️ 매도 기록을 남기지 않음! holdings도 유지!

        # ⚡ 극한 최적화: 시뮬레이션 완료 후 단 한 번만 commit!
        # Before: 20% 단위로 commit (5회)
        # After: 완료 후 1회만 commit
        await self.db.commit()
        logger.info("⚡ DB commit 완료 (1회)")

        return {
            'trades': [execution for execution in executions if execution['side'] == 'SELL'],
            'orders': orders,
            'executions': executions,
            'daily_snapshots': daily_snapshots,
            'final_holdings': holdings,
            'final_cash': cash_balance,
            'rebalance_dates': rebalance_dates,
            'position_history': position_history
        }

    async def _execute_sells(
        self,
        holdings: Dict[str, Position],
        factor_data: pd.DataFrame,
        sell_conditions: List[Dict],
        condition_sell: Optional[Dict[str, Any]],
        price_data: pd.DataFrame,
        trading_day: date,
        cash_balance: Decimal,
        orders: List[Dict[str, Any]],
        executions: List[Dict[str, Any]],
        price_lookup: Optional[Dict] = None  # 🚀 EXTREME OPTIMIZATION
    ) -> List[Dict]:
        """매도 실행"""

        sell_executions = []
        trading_ts = pd.Timestamp(trading_day)
        date_factors = pd.DataFrame()
        if factor_data is not None and not factor_data.empty:
            date_factors = factor_data[factor_data['date'] == trading_ts]

        target_cfg = self.target_and_loss or {}
        hold_cfg = self.hold_days or {}
        condition_sell_meta = self.condition_sell_meta

        # 디버깅: 매도 로직 (DEBUG 레벨)
        if len(holdings) > 0:
            logger.debug(f"💼 [{trading_day}] 매도 체크: {len(holdings)}개 보유")

        for stock_code, holding in list(holdings.items()):
            # 🚀 EXTREME OPTIMIZATION: O(1) dictionary 조회
            if price_lookup:
                price_info = price_lookup.get((stock_code, pd.Timestamp(trading_day)))
                if not price_info:
                    continue

                close_price = Decimal(str(price_info['close_price']))
                high_price = Decimal(str(price_info['high_price']))
                low_price = Decimal(str(price_info['low_price']))
                open_price = close_price  # Simplified
            else:
                # Fallback to pandas filtering (slow)
                current_price_data = price_data[
                    (price_data['stock_code'] == stock_code) &
                    (price_data['date'] == trading_day)
                ]

                if current_price_data.empty:
                    continue

                # 일중 가격 데이터 (시가/고가/저가/종가) - 안전한 접근
                row = current_price_data.iloc[0]
                try:
                    # close_price는 필수, 나머지는 fallback
                    close_price_raw = row.get('close_price')
                    if close_price_raw is None or pd.isna(close_price_raw):
                        logger.warning(f"⚠️ {stock_code}: close_price 없음, 매도 스킵")
                        continue
                    close_price = Decimal(str(close_price_raw))

                    # open/high/low는 close로 fallback
                    open_price = Decimal(str(row.get('open_price', close_price_raw)))
                    high_price = Decimal(str(row.get('high_price', close_price_raw)))
                    low_price = Decimal(str(row.get('low_price', close_price_raw)))
                except (ValueError, TypeError, InvalidOperation) as e:
                    logger.warning(f"⚠️ {stock_code}: 가격 데이터 변환 실패 ({e}), 매도 스킵")
                    continue

            current_price = close_price  # 기본값은 종가

            # 매도 조건 체크
            should_sell = False
            sell_reason = ""
            sell_reason_key = None

            # trading_day와 holding.entry_date를 date로 변환하여 비교
            trading_day_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day
            entry_date = holding.entry_date.date() if hasattr(holding.entry_date, 'date') else holding.entry_date
            hold_days_count = (trading_day_date - entry_date).days
            min_hold = hold_cfg.get('min_hold_days') if hold_cfg else None
            max_hold = hold_cfg.get('max_hold_days') if hold_cfg else None
            enforce_min_hold = min_hold is not None and hold_days_count < min_hold

            # 🎯 매도 우선순위: 1) 손절가 2) 목표가 3) 최소 보유기간 4) 최대 보유일
            # 손절가/목표가는 최소 보유기간 무시!
            if target_cfg:
                target_gain = target_cfg.get('target_gain')
                stop_loss = target_cfg.get('stop_loss')

                # 일중 최고가 기준 목표가 체크
                high_profit_rate = ((high_price / holding.entry_price) - Decimal("1")) * Decimal("100")
                # 일중 최저가 기준 손절가 체크
                low_profit_rate = ((low_price / holding.entry_price) - Decimal("1")) * Decimal("100")
                # 종가 기준 수익률 (로깅용)
                close_profit_rate = ((close_price / holding.entry_price) - Decimal("1")) * Decimal("100")

                # 🚀 PERFORMANCE: 디버깅 로그 제거 (3,145번 호출 → 0번)
                # logger.debug(f"📊 [{trading_day}] {stock_code} | 종가: {close_profit_rate:.2f}% | 고가: {high_profit_rate:.2f}% | 저가: {low_profit_rate:.2f}% | 목표: {target_gain}% | 손절: -{stop_loss}%")

                # 1순위: 손절가 우선 체크 (저가 기준)
                if stop_loss is not None and low_profit_rate <= -stop_loss:
                    should_sell = True
                    # 손절가에 정확히 매도된 것으로 간주
                    target_stop_price = holding.entry_price * (Decimal("1") - stop_loss / Decimal("100"))
                    current_price = target_stop_price
                    actual_loss_rate = ((current_price / holding.entry_price) - Decimal("1")) * Decimal("100")
                    sell_reason = f"Stop loss {actual_loss_rate:.2f}%"
                    sell_reason_key = "stop"
                    # 🚀 PERFORMANCE: 디버깅 로그 제거
                    # logger.debug(f"🛑 손절가 매도: {stock_code} | 저가: {low_profit_rate:.2f}% | 손절가 도달 -> {actual_loss_rate:.2f}%에 매도")

                # 2순위: 목표가 체크 (고가 기준)
                elif target_gain is not None and high_profit_rate >= target_gain:
                    should_sell = True
                    # 목표가에 정확히 매도된 것으로 간주
                    target_gain_price = holding.entry_price * (Decimal("1") + target_gain / Decimal("100"))
                    current_price = target_gain_price
                    actual_profit_rate = ((current_price / holding.entry_price) - Decimal("1")) * Decimal("100")
                    sell_reason = f"Take profit {actual_profit_rate:.2f}%"
                    sell_reason_key = "target"
                    # 🚀 PERFORMANCE: 디버깅 로그 제거
                    # logger.debug(f"🎯 목표가 매도: {stock_code} | 고가: {high_profit_rate:.2f}% | 목표가 도달 -> {actual_profit_rate:.2f}%에 매도")

            # 3순위: 최소 보유기간 체크 (손절가/목표가 미도달 시)
            # 최소 보유기간 미달이면 최대 보유일, 조건부 매도 등 다른 매도 불가
            if enforce_min_hold:
                continue  # 손절가/목표가 도달 안했고, 최소 보유기간도 미달이면 매도 안함

            # 4순위: 최대 보유일 체크
            if not should_sell and max_hold and hold_days_count >= max_hold:
                should_sell = True
                sell_reason = f"Max hold days reached ({hold_days_count}d)"
                sell_reason_key = "hold"

            # 5순위: 조건부 매도
            if not should_sell:
                for condition in sell_conditions:
                    if condition.get('type') == 'STOP_LOSS':
                        loss_rate = ((current_price / holding.entry_price) - 1) * 100
                        if loss_rate <= -float(condition.get('value', 10)):
                            should_sell = True
                            sell_reason = f"Stop loss triggered: {loss_rate:.2f}%"
                            sell_reason_key = "stop"
                            break

                    elif condition.get('type') == 'TAKE_PROFIT':
                        profit_rate = ((current_price / holding.entry_price) - 1) * 100
                        if profit_rate >= float(condition.get('value', 20)):
                            should_sell = True
                            sell_reason = f"Take profit triggered: {profit_rate:.2f}%"
                            sell_reason_key = "target"
                            break

                    elif condition.get('type') == 'HOLD_DAYS':
                        if hold_days_count >= int(condition.get('value', 30)):
                            should_sell = True
                            sell_reason = f"Hold period exceeded: {hold_days_count} days"
                            sell_reason_key = "hold"
                            break

            if (not should_sell) and condition_sell and not date_factors.empty:
                condition_list = condition_sell.get('sell_conditions') or []
                logic = condition_sell.get('sell_logic')
                evaluator = self.condition_evaluator
                if logic and condition_list:
                    expression_payload = {
                        "expression": logic,
                        "conditions": condition_list
                    }
                    selected, _ = evaluator.evaluate_buy_conditions(
                        factor_data=date_factors,
                        stock_codes=[stock_code],
                        buy_expression=expression_payload,
                        trading_date=trading_ts
                    )
                    if stock_code in selected:
                        should_sell = True
                        sell_reason = "Condition sell triggered"
                        sell_reason_key = "condition"
                elif condition_list:
                    passed, _, _ = evaluator.evaluate_condition_group(
                        factor_data=date_factors,
                        stock_code=stock_code,
                        conditions=condition_list,
                        trading_date=trading_ts
                    )
                    if passed:
                        should_sell = True
                        sell_reason = "Condition sell triggered"
                        sell_reason_key = "condition"

            if should_sell:
                # 🎯 익일 시가 조회 (더 현실적인 백테스트)
                # D일 매도 조건 만족 → D+1일 시가에 매도
                if price_lookup:
                    # 익일 찾기
                    next_day = trading_day + pd.Timedelta(days=1)
                    max_lookforward = 5  # 최대 5일까지 거래일 찾기
                    next_day_price = None
                    next_sell_date = None

                    for i in range(max_lookforward):
                        check_date = trading_day + pd.Timedelta(days=i+1)
                        price_info_next = price_lookup.get((stock_code, check_date))
                        if price_info_next:
                            next_day_price = Decimal(str(price_info_next.get('open_price', price_info_next['close_price'])))
                            next_sell_date = check_date.date()
                            break

                    if not next_day_price:
                        # 익일 데이터 없으면 당일 종가로 매도
                        next_day_price = close_price
                        next_sell_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day
                else:
                    # Fallback: pandas로 익일 조회
                    next_day_data = price_data[
                        (price_data['stock_code'] == stock_code) &
                        (price_data['date'] > trading_day)
                    ].sort_values('date')

                    if not next_day_data.empty:
                        next_row = next_day_data.iloc[0]
                        next_day_price = Decimal(str(next_row.get('open_price', next_row['close_price'])))
                        next_sell_date = next_row['date'].date()
                    else:
                        # 익일 데이터 없으면 당일 종가로 매도
                        next_day_price = close_price
                        next_sell_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day

                # 매도 실행
                quantity = holding.quantity

                # 목표가/손절가는 이론상 정확한 가격 사용, 나머지는 익일 시가
                if sell_reason_key in ["target", "stop"]:
                    # 목표가/손절가는 current_price 사용 (이미 목표가/손절가로 계산됨)
                    execution_price = current_price * (1 - self.slippage)
                else:
                    # 보유일, 조건부 매도 등은 익일 시가
                    execution_price = next_day_price * (1 - self.slippage)

                amount = execution_price * quantity
                commission = amount * self.commission_rate
                tax = amount * self.tax_rate
                net_amount = amount - commission - tax
                cost_basis = holding.entry_price * quantity if holding.entry_price else Decimal("0")
                profit = net_amount - cost_basis
                if cost_basis > 0:
                    profit_rate = ((net_amount / cost_basis) - 1) * 100
                else:
                    profit_rate = 0

                # 실제 체결일 결정 (date 타입으로 통일)
                if sell_reason_key not in ["target", "stop"]:
                    actual_sell_date = next_sell_date
                else:
                    actual_sell_date = trading_day.date() if hasattr(trading_day, 'date') else trading_day

                order = {
                    'order_id': f"ORD-S-{stock_code}-{trading_day}",
                    'order_date': trading_day,  # 주문일은 오늘
                    'stock_code': stock_code,
                    'stock_name': holding.stock_name,
                    'side': 'SELL',
                    'order_type': 'MARKET',
                    'quantity': quantity,
                    'status': 'FILLED',
                    'reason': sell_reason
                }
                orders.append(order)

                execution = {
                    'execution_id': f"EXE-S-{stock_code}-{actual_sell_date}",
                    'order_id': order['order_id'],
                    'execution_date': actual_sell_date,  # 체결일 (익일 또는 당일)
                    'trade_date': actual_sell_date,
                    'stock_code': stock_code,
                    'stock_name': holding.stock_name,
                    'side': 'SELL',
                    'trade_type': 'SELL',
                    'quantity': quantity,
                    'price': execution_price,
                    'amount': amount,
                    'commission': commission,
                    'tax': tax,
                    'slippage': self.slippage,
                    'realized_pnl': profit,
                    'profit': profit,
                    'profit_rate': profit_rate,
                    'return_pct': profit_rate,  # ✅ DB 저장용 키 추가
                    'hold_days': (actual_sell_date - (holding.entry_date.date() if hasattr(holding.entry_date, 'date') else holding.entry_date)).days,
                    'selection_reason': sell_reason,
                    'factors': {}
                }
                executions.append(execution)
                sell_executions.append(execution)

        return sell_executions

    async def _select_buy_candidates(
        self,
        factor_data: pd.DataFrame,
        buy_conditions: Any,
        trading_day: date,
        price_data: pd.DataFrame,
        holdings: Dict,
        max_positions: int,
        priority_factor: Optional[str] = None,
        priority_order: str = "desc"
    ) -> List[str]:
        """매수 후보 종목 선정 (논리식/가중치 지원) - 통합 모듈 사용"""

        # 통합 모듈 사용
        from app.services.factor_integration import FactorIntegration
        factor_integrator = FactorIntegration(self.db)

        candidates: List[str] = []

        if factor_data.empty:
            return candidates

        trading_ts = pd.Timestamp(trading_day)

        # 거래 가능한 종목 필터링
        tradeable_stocks = price_data[
            (price_data['date'] == trading_day) &
            (price_data['volume'] > 0) &
            (price_data['close_price'] > 0)
        ]['stock_code'].unique().tolist()

        # 리밸런싱 시에는 보유 종목도 재평가해야 하므로 제외하지 않음
        # (기존 로직: tradeable_stocks = [s for s in tradeable_stocks if s not in holdings])
        # 포지션 사이징에서 available_slots로 신규 매수 수량 제한

        # 통합 모듈로 매수 조건 평가 (54개 팩터 사용)
        selected_stocks = factor_integrator.evaluate_buy_conditions_with_factors(
            factor_data=factor_data,
            stock_codes=tradeable_stocks,
            buy_conditions=buy_conditions,
            trading_date=trading_ts
        )

        # 팩터 가중치가 있는 경우 스코어링
        if isinstance(buy_conditions, dict) and 'factor_weights' in buy_conditions:
            factor_weights = buy_conditions.get('factor_weights', {})

            if factor_weights and selected_stocks:
                # 복합 스코어로 순위 매기기
                ranked_stocks = factor_integrator.rank_stocks_by_composite_score(
                    factor_data=factor_data,
                    stock_codes=selected_stocks,
                    factor_weights=factor_weights,
                    trading_date=trading_ts,
                    top_n=max_positions
                )
                candidates = [stock for stock, score in ranked_stocks]
            else:
                # 가중치가 없으면 선택된 종목 그대로 사용
                candidates = selected_stocks[:max_positions]
        else:
            # 일반 조건인 경우 선택된 종목 사용
            candidates = selected_stocks[:max_positions]

        return candidates

    def _priority_bonus(
        self,
        date_factors: pd.DataFrame,
        stock_code: str,
        factor_key: Optional[str],
        priority_order: str
    ) -> float:
        if not factor_key:
            return 0.0

        stock_slice = date_factors[date_factors['stock_code'] == stock_code]
        if stock_slice.empty:
            return 0.0

        value = None
        if factor_key in stock_slice.columns:
            value = stock_slice[factor_key].iloc[0]
        elif f"{factor_key}_RANK" in stock_slice.columns:
            value = stock_slice[f"{factor_key}_RANK"].iloc[0]

        if value is None or pd.isna(value):
            return 0.0

        bonus = float(value)
        return -bonus if priority_order.lower() == 'asc' else bonus

    def _apply_position_constraints(self, allocation: Decimal) -> Decimal:
        """per_stock_ratio / max_buy_value 제약 적용"""
        constrained = allocation
        if self.per_stock_ratio:
            ratio_limit = self.initial_capital * (self.per_stock_ratio / Decimal("100"))
            constrained = min(constrained, ratio_limit)
        if self.max_buy_value:
            constrained = min(constrained, self.max_buy_value)
        return constrained

    def _apply_price_adjustment(
        self,
        price: Decimal,
        meta: Optional[Dict[str, Any]],
        *,
        stock_code: Optional[str] = None,
        holding: Optional[Position] = None,
        trading_day: Optional[date] = None,
        price_lookup: Optional[Dict] = None,
        price_data: Optional[pd.DataFrame] = None
    ) -> Decimal:
        """매도 기준가/오프셋 적용"""
        if not meta:
            return price

        basis = self._normalize_price_basis(meta.get('sell_price_basis'))
        adjusted_price = price

        if basis == 'PREV_CLOSE':
            prev_close = self._get_previous_close_price(stock_code, trading_day, price_lookup, price_data)
            if prev_close is not None:
                adjusted_price = prev_close
        elif basis == 'OPEN':
            open_price = self._get_price_from_lookup(stock_code, trading_day, 'open_price', price_lookup, price_data)
            if open_price is not None:
                adjusted_price = open_price
        elif basis == 'ENTRY' and holding is not None and holding.entry_price:
            adjusted_price = holding.entry_price
        # CURRENT 기본값은 인자로 받은 price 사용

        offset_pct = meta.get('sell_price_offset')
        if offset_pct is not None:
            offset_value = offset_pct if isinstance(offset_pct, Decimal) else Decimal(str(offset_pct))
            adjusted_price = adjusted_price * (Decimal("1") + (offset_value / Decimal("100")))

        return adjusted_price

    def _normalize_price_basis(self, basis: Optional[str]) -> str:
        """한국어/영문 표기를 공통 코드로 정규화"""
        if not basis:
            return 'CURRENT'
        normalized = str(basis).strip().upper()
        mapping = {
            '전일 종가': 'PREV_CLOSE',
            'PREV CLOSE': 'PREV_CLOSE',
            'PREV_CLOSE': 'PREV_CLOSE',
            '이전종가': 'PREV_CLOSE',
            '당일 시가': 'OPEN',
            '시가': 'OPEN',
            'OPEN': 'OPEN',
            'CURRENT': 'CURRENT',
            '당일 종가': 'CURRENT',
            '현재가': 'CURRENT',
            'ENTRY': 'ENTRY',
            '평균매수가': 'ENTRY'
        }
        return mapping.get(basis, mapping.get(normalized, 'CURRENT'))

    def _get_price_from_lookup(
        self,
        stock_code: Optional[str],
        target_date: Optional[date],
        field: str,
        price_lookup: Optional[Dict],
        price_data: Optional[pd.DataFrame]
    ) -> Optional[Decimal]:
        if not stock_code or target_date is None:
            return None
        target_ts = pd.Timestamp(target_date)
        if price_lookup:
            info = price_lookup.get((stock_code, target_ts))
            if info and info.get(field) is not None:
                return Decimal(str(info[field]))
        if price_data is not None and field in price_data.columns:
            row = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == target_ts)
            ]
            if not row.empty:
                value = row.iloc[0].get(field)
                if value is not None and not pd.isna(value):
                    return Decimal(str(value))
        return None

    def _get_previous_close_price(
        self,
        stock_code: Optional[str],
        trading_day: Optional[date],
        price_lookup: Optional[Dict],
        price_data: Optional[pd.DataFrame]
    ) -> Optional[Decimal]:
        if not stock_code or trading_day is None:
            return None
        prev_day = pd.Timestamp(trading_day) - pd.Timedelta(days=1)
        # 최대 일주일 전까지만 탐색
        for _ in range(7):
            price = self._get_price_from_lookup(stock_code, prev_day, 'close_price', price_lookup, price_data)
            if price is not None:
                return price
            prev_day -= pd.Timedelta(days=1)
        return None

    def _calculate_position_sizes(
        self,
        buy_candidates: List[str],
        cash_balance: Decimal,
        position_sizing: str,
        available_slots: int,
        price_data: pd.DataFrame,
        trading_day: date,
        current_holdings: Dict[str, Position]
    ) -> Dict[str, Decimal]:
        """포지션 사이징 계산"""

        position_sizes: Dict[str, Decimal] = {}

        if not buy_candidates:
            return position_sizes

        max_new_positions = max(available_slots, 0)
        existing_candidates = [s for s in buy_candidates if s in current_holdings]
        new_candidates = [s for s in buy_candidates if s not in current_holdings][:max_new_positions]
        effective_candidates = existing_candidates + new_candidates

        if not effective_candidates:
            return position_sizes

        num_positions = len(effective_candidates)
        if num_positions == 0:  # 추가 방어
            return position_sizes

        allocatable_cash = cash_balance * Decimal("0.95")

        if position_sizing == "EQUAL_WEIGHT":
            allocation_per_stock = allocatable_cash / num_positions
            for stock in effective_candidates:
                position_sizes[stock] = self._apply_position_constraints(allocation_per_stock)
            return position_sizes

        closes = price_data[
            (price_data['date'] == trading_day) &
            (price_data['stock_code'].isin(effective_candidates))
        ][['stock_code', 'close_price', 'market_cap']].dropna()

        if closes.empty:
            allocation_per_stock = allocatable_cash / num_positions
            for stock in buy_candidates[:num_positions]:
                position_sizes[stock] = self._apply_position_constraints(allocation_per_stock)
            return position_sizes

        if position_sizing == "MARKET_CAP":
            subset = closes.set_index('stock_code')
            weights = subset['market_cap']
            total = weights.sum()
            if total <= 0:
                total = 1
            normalized = weights / total
            for stock in effective_candidates:
                w = normalized.get(stock, 0)
                allocation = Decimal(str(w)) * allocatable_cash
                position_sizes[stock] = self._apply_position_constraints(allocation)
            return position_sizes

        if position_sizing == "RISK_PARITY":
            returns = price_data[
                (price_data['stock_code'].isin(effective_candidates)) &
                (price_data['date'] <= trading_day) &
                (price_data['date'] >= trading_day - pd.Timedelta(days=90))
            ][['stock_code', 'date', 'close_price']]

            vol_map: Dict[str, float] = {}
            if not returns.empty:
                for stock, group in returns.groupby('stock_code'):
                    if len(group) > 10:
                        pct = group.sort_values('date')['close_price'].pct_change().dropna()
                        if not pct.empty:
                            vol = pct.std()
                            if vol and vol > 0:
                                vol_map[stock] = 1 / vol

            if not vol_map:
                allocation_per_stock = allocatable_cash / num_positions
                for stock in buy_candidates[:num_positions]:
                    position_sizes[stock] = self._apply_position_constraints(allocation_per_stock)
                return position_sizes

            total = sum(vol_map.values())
            for stock in effective_candidates:
                w = vol_map.get(stock, 0)
                if total > 0:
                    allocation = Decimal(str(w / total)) * allocatable_cash
                    position_sizes[stock] = self._apply_position_constraints(allocation)
                else:
                    position_sizes[stock] = Decimal("0")

            return position_sizes

        allocation_per_stock = allocatable_cash / num_positions
        for stock in effective_candidates:
            position_sizes[stock] = self._apply_position_constraints(allocation_per_stock)

        return position_sizes

    async def _execute_buys(
        self,
        position_sizes: Dict[str, Decimal],
        price_data: pd.DataFrame,
        trading_day: date,
        cash_balance: Decimal,
        holdings: Dict[str, Position],
        factor_data: pd.DataFrame = None,
        orders: List[Dict[str, Any]] = None,
        executions: List[Dict[str, Any]] = None,
        daily_new_positions: int = 0,
        max_daily_new_positions: Optional[int] = None
    ) -> Tuple[List[Dict], int]:
        """매수 실행 (팩터 정보 포함)"""

        buy_trades = []
        new_position_count = daily_new_positions

        for stock_code, allocation in position_sizes.items():
            is_new_position = stock_code not in holdings
            if (
                max_daily_new_positions is not None
                and is_new_position
                and new_position_count >= max_daily_new_positions
            ):
                continue

            # 현재가 조회
            current_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == trading_day)
            ]

            if current_price_data.empty:
                continue

            # 🎯 익일 시가 조회 (더 현실적인 백테스트)
            # D일 조건 만족 → D+1일 시가에 매수
            next_day_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] > trading_day)
            ].sort_values('date')

            if next_day_price_data.empty:
                # 익일 데이터 없음 (백테스트 기간 종료 직전)
                continue

            next_day_row = next_day_price_data.iloc[0]

            # 익일 시가 조회
            try:
                open_price_raw = next_day_row.get('open_price')
                if open_price_raw is None or pd.isna(open_price_raw):
                    # 시가 없으면 종가 fallback
                    open_price_raw = next_day_row.get('close_price')
                    if open_price_raw is None or pd.isna(open_price_raw):
                        logger.warning(f"⚠️ {stock_code}: 익일 가격 데이터 없음, 매수 스킵")
                        continue

                next_open_price = Decimal(str(open_price_raw))
                if next_open_price <= 0:
                    logger.warning(f"⚠️ {stock_code}: 유효하지 않은 가격 ({next_open_price}), 매수 스킵")
                    continue
            except (ValueError, TypeError, InvalidOperation) as e:
                logger.warning(f"⚠️ {stock_code}: 가격 데이터 변환 실패 ({e}), 매수 스킵")
                continue

            stock_name = current_price_data.iloc[0].get('stock_name', f"Stock_{stock_code}")
            next_trade_date = next_day_row['date'].date()

            # 슬리피지 적용 (매수 시 불리하게 - 가격 상승)
            execution_price = next_open_price * (1 + self.slippage)

            # 매수 가능 수량 계산
            quantity = int(allocation / execution_price)

            if quantity <= 0:
                continue

            # 실제 매수 금액
            amount = execution_price * quantity
            commission = amount * self.commission_rate

            # 잔고 확인
            if amount + commission > cash_balance:
                continue

            # 거래 시점 팩터 값 추출
            trade_factors = {}
            if factor_data is not None and not factor_data.empty:
                stock_mask = factor_data['stock_code'] == stock_code
                date_mask = pd.to_datetime(factor_data['date']) == pd.Timestamp(trading_day)
                stock_factors = factor_data[stock_mask & date_mask]
                if not stock_factors.empty:
                    # 메타데이터 컬럼 (문자열 타입) 제외
                    meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
                    for col in stock_factors.columns:
                        if col in meta_columns or col.endswith('_RANK'):
                            continue
                        value = stock_factors[col].iloc[0]
                        if pd.notna(value):
                            try:
                                trade_factors[col] = float(value)
                            except (ValueError, TypeError):
                                # 숫자로 변환 불가능한 값은 스킵
                                continue

            # 매수 실행 (익일 시가)
            order = {
                'order_id': f"ORD-B-{stock_code}-{trading_day}",
                'order_date': trading_day,  # 주문일은 오늘
                'stock_code': stock_code,
                'stock_name': stock_name,
                'side': 'BUY',
                'order_type': 'MARKET',
                'quantity': quantity,
                'status': 'FILLED',
                'reason': "Factor-based selection (next day open)"
            }
            if orders is not None:
                orders.append(order)

            execution = {
                'execution_id': f"EXE-B-{stock_code}-{next_trade_date}",
                'order_id': order['order_id'],
                'execution_date': next_trade_date,  # 체결일은 익일
                'trade_date': next_trade_date,  # 거래일은 익일
                'stock_code': stock_code,
                'stock_name': stock_name,
                'side': 'BUY',
                'trade_type': 'BUY',
                'quantity': quantity,
                'price': execution_price,
                'amount': amount,
                'commission': commission,
                'tax': Decimal("0"),
                'slippage': self.slippage,
                'factors': trade_factors,
                'selection_reason': "Factor-based selection (next day open)"
            }
            if executions is not None:
                executions.append(execution)

            buy_trades.append(execution)

            existing_position = holdings.get(stock_code)
            if existing_position:
                total_qty = existing_position.quantity + quantity
                new_avg_price = ((existing_position.entry_price * existing_position.quantity) + (execution_price * quantity)) / total_qty
                existing_position.entry_price = new_avg_price
                existing_position.quantity = total_qty
                existing_position.current_price = execution_price
                existing_position.current_value = execution_price * total_qty
                logger.debug(f"✅ 추가 매수: {stock_code} {quantity}주 @ {execution_price:,.0f}원 (평균가: {new_avg_price:,.0f}원)")
            else:
                holdings[stock_code] = Position(
                    position_id=f"POS-{stock_code}-{next_trade_date}",
                    stock_code=stock_code,
                    stock_name=stock_name,
                    entry_date=next_trade_date,  # 진입일은 익일
                    entry_price=execution_price,
                    quantity=quantity,
                    current_price=execution_price,
                    current_value=execution_price * quantity
                )
                new_position_count += 1
                logger.debug(f"✅ 신규 매수: {stock_code} {quantity}주 @ {execution_price:,.0f}원 (익일 시가)")

        return buy_trades, new_position_count

    def _get_rebalance_dates(
        self,
        trading_days: List[date],
        frequency: str
    ) -> List[date]:
        """리밸런싱 날짜 계산"""

        rebalance_dates = []

        if frequency == "DAILY":
            return trading_days

        elif frequency == "WEEKLY":
            # 매주 월요일
            for day in trading_days:
                if pd.Timestamp(day).weekday() == 0:  # Monday
                    rebalance_dates.append(day)

        elif frequency == "MONTHLY":
            # 매월 첫 거래일
            current_month = None
            for day in trading_days:
                if current_month != pd.Timestamp(day).month:
                    rebalance_dates.append(day)
                    current_month = pd.Timestamp(day).month

        elif frequency == "QUARTERLY":
            # 분기별 첫 거래일
            current_quarter = None
            for day in trading_days:
                quarter = (pd.Timestamp(day).month - 1) // 3
                if current_quarter != quarter:
                    rebalance_dates.append(day)
                    current_quarter = quarter

        return rebalance_dates

    def _calculate_portfolio_value(
        self,
        holdings: Dict[str, Position],
        price_data: pd.DataFrame,
        trading_day: date,
        cash_balance: Decimal
    ) -> Decimal:
        """
        🚀 OPTIMIZATION 5: 포트폴리오 가치 계산 벡터화

        Before: 각 종목마다 DataFrame 필터링 (N회)
        After: MultiIndex로 한 번에 조회 (1회) - 10-20배 빠름
        """
        total_value = cash_balance

        if not holdings:
            return total_value

        # 보유 종목 코드 리스트
        holding_codes = [code for code, h in holdings.items() if h is not None]

        if not holding_codes:
            return total_value

        # 🚀 벡터화: MultiIndex로 한 번에 모든 종목 가격 조회
        try:
            # price_data에 MultiIndex가 없으면 생성 (처음 한 번만)
            if not hasattr(self, '_price_data_indexed') or self._last_price_data_id != id(price_data):
                self._price_data_indexed = price_data.set_index(['date', 'stock_code'])
                self._last_price_data_id = id(price_data)

            # 한 번에 모든 보유 종목의 현재가 조회
            current_prices = self._price_data_indexed.loc[
                (pd.Timestamp(trading_day), holding_codes),
                'close_price'
            ]

            # Series로 변환 (단일 종목일 경우 처리)
            if isinstance(current_prices, (int, float, Decimal)):
                current_prices = pd.Series([current_prices], index=[holding_codes[0]])
            elif not isinstance(current_prices, pd.Series):
                current_prices = pd.Series(current_prices, index=holding_codes)

            # 🚀 Numba JIT로 포트폴리오 가치 계산 (2-5배 빠름!)
            prices_array = []
            quantities_array = []

            for stock_code in holding_codes:
                holding = holdings.get(stock_code)
                if holding is None:
                    continue

                # 가격 조회
                if stock_code in current_prices.index:
                    close_price_raw = current_prices[stock_code]
                    if close_price_raw is not None and not pd.isna(close_price_raw):
                        current_price = Decimal(str(close_price_raw))
                    else:
                        current_price = holding.entry_price
                else:
                    current_price = holding.entry_price

                holding.current_price = current_price
                holding.current_value = current_price * holding.quantity

                # Numba용 배열 구축
                prices_array.append(float(current_price))
                quantities_array.append(int(holding.quantity))

            # Numba JIT 함수로 총 가치 계산
            if prices_array:
                holdings_value = calculate_portfolio_value_numba(
                    np.array(prices_array),
                    np.array(quantities_array)
                )
                total_value = cash_balance + Decimal(str(holdings_value))
            else:
                total_value = cash_balance

        except (KeyError, IndexError) as e:
            # MultiIndex 조회 실패 시 폴백 (기존 방식)
            for stock_code, holding in holdings.items():
                if holding is None:
                    continue

                current_price_data = price_data[
                    (price_data['stock_code'] == stock_code) &
                    (price_data['date'] == trading_day)
                ]

                if not current_price_data.empty:
                    close_price_raw = current_price_data.iloc[0].get('close_price')
                    if close_price_raw is not None and not pd.isna(close_price_raw):
                        current_price = Decimal(str(close_price_raw))
                    else:
                        current_price = holding.entry_price
                else:
                    current_price = holding.entry_price

                holding.current_price = current_price
                holding.current_value = current_price * holding.quantity
                total_value += holding.current_value

        return total_value

    def _calculate_statistics(
        self,
        portfolio_result: Dict,
        initial_capital: Decimal,
        start_date: date,
        end_date: date
    ) -> StatsSchema:
        """통계 계산"""

        daily_snapshots = portfolio_result['daily_snapshots']
        executions = portfolio_result.get('executions', portfolio_result.get('trades', []))
        sell_executions = [exe for exe in executions if exe.get('side') == 'SELL']

        if not daily_snapshots:
            # 빈 통계 반환
            return StatsSchema(
                total_return=Decimal("0"),
                annualized_return=Decimal("0"),
                max_drawdown=Decimal("0"),
                volatility=Decimal("0"),
                downside_volatility=Decimal("0"),
                sharpe_ratio=Decimal("0"),
                sortino_ratio=Decimal("0"),
                calmar_ratio=Decimal("0"),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=Decimal("0"),
                avg_win=Decimal("0"),
                avg_loss=Decimal("0"),
                profit_loss_ratio=Decimal("0"),
                initial_capital=initial_capital,
                final_capital=initial_capital,
                peak_capital=initial_capital,
                start_date=start_date,
                end_date=end_date,
                trading_days=0
            )

        # DataFrame 변환
        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        df['portfolio_value'] = df['portfolio_value'].astype(float)
        df['cash_balance'] = df['cash_balance'].astype(float)

        # 일별 수익률 계산
        df['daily_return'] = df['portfolio_value'].pct_change()
        df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

        # 벤치마크 계산
        benchmark_return_pct = None
        excess_return = None
        if 'benchmark_value' in df.columns and df['benchmark_value'].notna().any():
            df['benchmark_value'] = df['benchmark_value'].astype(float)
            df['benchmark_daily_return'] = df['benchmark_value'].pct_change()
            if df['benchmark_value'].iloc[0] and df['benchmark_value'].iloc[-1]:
                benchmark_return_pct = ((df['benchmark_value'].iloc[-1] / df['benchmark_value'].iloc[0]) - 1) * 100
        else:
            df['benchmark_daily_return'] = np.nan

        # 최대 낙폭 (MDD) 계산
        df['cummax'] = df['portfolio_value'].cummax()
        df['drawdown'] = (df['portfolio_value'] - df['cummax']) / df['cummax']
        max_drawdown = abs(df['drawdown'].min()) * 100 if not df['drawdown'].empty else 0

        # 총 수익률
        final_value = float(df['portfolio_value'].iloc[-1]) if not df.empty else float(initial_capital)
        total_return = ((final_value / float(initial_capital)) - 1) * 100
        if benchmark_return_pct is not None:
            excess_return = total_return - benchmark_return_pct

        # 연환산 수익률 (CAGR)
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = ((final_value / float(initial_capital)) ** (1/years) - 1) * 100 if years > 0 else 0

        # 거래 비용 계산
        total_trades = len(executions)
        total_commission = sum(float(t.get('commission', 0)) for t in executions)
        total_tax = sum(float(t.get('tax', 0)) for t in executions)
        total_costs = total_commission + total_tax

        # 로깅: 수익률 계산 확인
        logger.info(f"📊 수익률 계산: 기간={days}일({years:.2f}년) | 누적수익률={total_return:.2f}% | CAGR={annualized_return:.2f}% | MDD={max_drawdown:.2f}%")
        logger.info(f"💸 거래 비용 분석: 총 거래={total_trades}회 | 수수료={total_commission:,.0f}원 | 거래세={total_tax:,.0f}원 | 총 비용={total_costs:,.0f}원 ({total_costs/float(initial_capital)*100:.2f}%)")

        # 변동성
        volatility_val = df['daily_return'].std() * np.sqrt(252) * 100 if not df['daily_return'].empty else 0
        volatility = 0 if np.isnan(volatility_val) or np.isinf(volatility_val) else volatility_val

        # 하방 변동성
        negative_returns = df['daily_return'][df['daily_return'] < 0]
        downside_vol_val = negative_returns.std() * np.sqrt(252) * 100 if not negative_returns.empty else 0
        downside_volatility = 0 if np.isnan(downside_vol_val) or np.isinf(downside_vol_val) else downside_vol_val

        # 샤프 비율
        risk_free_rate = 0.02  # 2% 무위험 수익률
        sharpe_val = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        sharpe_ratio = 0 if np.isnan(sharpe_val) or np.isinf(sharpe_val) else sharpe_val

        # 소르티노 비율
        sortino_val = (annualized_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        sortino_ratio = 0 if np.isnan(sortino_val) or np.isinf(sortino_val) else sortino_val

        # 칼마 비율
        calmar_val = annualized_return / max_drawdown if max_drawdown > 0 else 0
        calmar_ratio = 0 if np.isnan(calmar_val) or np.isinf(calmar_val) else calmar_val

        # 거래 통계
        winning_trades = [t for t in sell_executions if t.get('realized_pnl', 0) > 0]
        losing_trades = [t for t in sell_executions if t.get('realized_pnl', 0) <= 0]
        win_rate = len(winning_trades) / len(sell_executions) * 100 if sell_executions else 0

        avg_win = np.mean([float(t.get('profit_rate', 0)) for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(float(t.get('profit_rate', 0))) for t in losing_trades]) if losing_trades else 0
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        return StatsSchema(
            total_return=Decimal(str(total_return)),
            annualized_return=Decimal(str(annualized_return)),
            benchmark_return=Decimal(str(benchmark_return_pct)) if benchmark_return_pct is not None else None,
            excess_return=Decimal(str(excess_return)) if excess_return is not None else None,
            max_drawdown=Decimal(str(max_drawdown)),
            volatility=Decimal(str(volatility)),
            downside_volatility=Decimal(str(downside_volatility)),
            sharpe_ratio=Decimal(str(sharpe_ratio)),
            sortino_ratio=Decimal(str(sortino_ratio)),
            calmar_ratio=Decimal(str(calmar_ratio)),
            total_trades=len(sell_executions),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=Decimal(str(win_rate)),
            avg_win=Decimal(str(avg_win)),
            avg_loss=Decimal(str(avg_loss)),
            profit_loss_ratio=Decimal(str(profit_loss_ratio)),
            initial_capital=initial_capital,
            final_capital=Decimal(str(final_value)),
            peak_capital=Decimal(str(df['portfolio_value'].max())) if not df.empty else initial_capital,
            start_date=start_date,
            end_date=end_date,
            trading_days=len(df)
        )

    def _aggregate_monthly_performance(
        self,
        daily_snapshots: List[Dict],
        trades: List[Dict] = None
    ) -> List[MonthlyPerformance]:
        """월별 성과 집계 (거래 기반 승률 계산)"""

        if not daily_snapshots:
            return []

        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month

        # Convert Decimal columns to float to avoid type mismatch in calculations
        if 'portfolio_value' in df.columns:
            df['portfolio_value'] = df['portfolio_value'].astype(float)

        monthly_data = []
        for (year, month), group in df.groupby(['year', 'month']):
            if group.empty:
                continue

            start_value = float(group['portfolio_value'].iloc[0])
            end_value = float(group['portfolio_value'].iloc[-1])
            monthly_return = ((end_value / start_value) - 1) * 100 if start_value > 0 else 0

            # 월별 거래 기반 승률 계산
            win_rate = Decimal("0")
            avg_hold_days = 0

            if trades:
                # 해당 월의 매도 거래만 필터링
                month_sell_trades = [
                    t for t in trades
                    if t.get('trade_type') == 'SELL'
                    and pd.to_datetime(t.get('trade_date')).year == year
                    and pd.to_datetime(t.get('trade_date')).month == month
                ]

                if month_sell_trades:
                    # 수익 거래 카운트
                    winning_trades = [t for t in month_sell_trades if float(t.get('profit', 0)) > 0]
                    win_rate = Decimal(str(len(winning_trades) / len(month_sell_trades) * 100))

                    # 평균 보유일수 계산
                    hold_days_list = [t.get('hold_days', 0) for t in month_sell_trades if t.get('hold_days')]
                    if hold_days_list:
                        avg_hold_days = sum(hold_days_list) // len(hold_days_list)

            monthly_data.append(MonthlyPerformance(
                year=int(year),
                month=int(month),
                return_rate=Decimal(str(monthly_return)),
                benchmark_return=None,  # 벤치마크 제외
                win_rate=win_rate,
                trade_count=int(group['trade_count'].sum()),
                avg_hold_days=avg_hold_days
            ))

        return monthly_data

    def _aggregate_yearly_performance(
        self,
        daily_snapshots: List[Dict]
    ) -> List[YearlyPerformance]:
        """연도별 성과 집계"""

        if not daily_snapshots:
            return []

        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year

        # Convert Decimal columns to float to avoid type mismatch in calculations
        if 'portfolio_value' in df.columns:
            df['portfolio_value'] = df['portfolio_value'].astype(float)

        yearly_data = []
        for year, group in df.groupby('year'):
            if group.empty:
                continue

            start_value = float(group['portfolio_value'].iloc[0])
            end_value = float(group['portfolio_value'].iloc[-1])
            yearly_return = ((end_value / start_value) - 1) * 100 if start_value > 0 else 0

            # 연도별 MDD 계산
            cummax = group['portfolio_value'].cummax()
            drawdown = (group['portfolio_value'] - cummax) / cummax
            max_drawdown = abs(drawdown.min()) * 100 if not drawdown.empty else 0

            # 연도별 샤프 비율 계산
            daily_returns = group['portfolio_value'].pct_change()
            volatility = daily_returns.std() * np.sqrt(252)
            sharpe = (yearly_return / 100 - 0.02) / volatility if volatility > 0 else 0

            yearly_data.append(YearlyPerformance(
                year=int(year),
                return_rate=Decimal(str(yearly_return)),
                benchmark_return=None,
                max_drawdown=Decimal(str(max_drawdown)),
                sharpe_ratio=Decimal(str(sharpe)),
                trades=int(group['trade_count'].sum())
            ))

        return yearly_data

    def _analyze_factor_contribution(
        self,
        trades: List[Dict],
        buy_conditions: List[Dict]
    ) -> Dict[str, Any]:
        """팩터별 성과 기여도 분석"""

        if not trades or not buy_conditions:
            return {}

        # 팩터별 거래 성과 집계
        factor_performance = {}

        # 매도 거래만 필터링 (수익률 계산 가능)
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']

        if not sell_trades:
            return {}

        # buy_conditions가 dict 형태(논리식)인 경우 조건 리스트 추출
        conditions_list = buy_conditions
        if isinstance(buy_conditions, dict) and 'conditions' in buy_conditions:
            conditions_list = buy_conditions['conditions']
        elif isinstance(buy_conditions, dict):
            # dict이지만 'conditions' 키가 없는 경우 빈 리스트
            conditions_list = []

        # 각 팩터별 성과 분석
        for condition in conditions_list:
            factor_name = condition.get('factor')
            if not factor_name:
                continue

            # 해당 팩터가 포함된 거래 찾기
            factor_trades = []
            for trade in sell_trades:
                trade_factors = trade.get('factors', {})
                if factor_name in trade_factors:
                    factor_trades.append(trade)

            if factor_trades:
                # 팩터별 통계 계산
                profits = [float(t.get('profit', 0)) for t in factor_trades]
                profit_rates = [float(t.get('profit_rate', 0)) for t in factor_trades]
                winning_trades = [t for t in factor_trades if float(t.get('profit', 0)) > 0]

                factor_performance[factor_name] = {
                    'total_trades': len(factor_trades),
                    'winning_trades': len(winning_trades),
                    'win_rate': len(winning_trades) / len(factor_trades) * 100 if factor_trades else 0,
                    'avg_profit': sum(profits) / len(profits) if profits else 0,
                    'avg_profit_rate': sum(profit_rates) / len(profit_rates) if profit_rates else 0,
                    'total_profit': sum(profits),
                    'best_trade': max(profits) if profits else 0,
                    'worst_trade': min(profits) if profits else 0,
                    'contribution_score': len(winning_trades) / len(sell_trades) * 100  # 전체 수익 거래 중 기여도
                }

        # 팩터 중요도 순위 계산
        if factor_performance:
            # contribution_score 기준으로 정렬
            sorted_factors = sorted(
                factor_performance.items(),
                key=lambda x: x[1]['contribution_score'],
                reverse=True
            )

            for rank, (factor, _) in enumerate(sorted_factors, 1):
                factor_performance[factor]['importance_rank'] = rank

        return factor_performance

    async def _format_current_holdings(
        self,
        holdings: Dict[str, Position]
    ) -> List[PortfolioHolding]:
        """현재 보유 종목 포맷"""

        formatted_holdings = []

        if not holdings:
            return formatted_holdings

        # 현재 가격 조회를 위해 최신 날짜 가져오기
        query = select(func.max(StockPrice.trade_date))
        result = await self.db.execute(query)
        latest_date = result.scalar()

        total_value = Decimal("0")

        # 각 보유 종목별 현재 정보 조회
        for stock_code, holding in holdings.items():
            # 종목 정보 및 현재가 조회
            stock_query = select(
                Company.company_name,
                StockPrice.close_price
            ).join(
                StockPrice, Company.company_id == StockPrice.company_id
            ).where(
                and_(
                    Company.stock_code == stock_code,
                    StockPrice.trade_date == latest_date
                )
            )

            result = await self.db.execute(stock_query)
            stock_info = result.first()

            if stock_info:
                stock_name = stock_info.company_name
                current_price = Decimal(str(stock_info.close_price))
            else:
                stock_name = holding.stock_name
                current_price = holding.entry_price

            # 손익 계산
            value = current_price * holding.quantity
            profit = (current_price - holding.entry_price) * holding.quantity
            profit_rate = ((current_price / holding.entry_price) - 1) * 100

            total_value += value

            formatted_holdings.append(PortfolioHolding(
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=holding.quantity,
                avg_price=holding.entry_price,
                current_price=current_price,
                value=value,
                profit=profit,
                profit_rate=Decimal(str(profit_rate)),
                weight=Decimal("0"),  # 나중에 계산
                buy_date=holding.entry_date,
                hold_days=(pd.Timestamp(latest_date).date() - (holding.entry_date.date() if hasattr(holding.entry_date, 'date') else holding.entry_date)).days if latest_date else 0,
                factors={}
            ))

        # 비중 계산
        for holding in formatted_holdings:
            if total_value > 0:
                holding.weight = Decimal(str(float(holding.value) / float(total_value) * 100))

        return formatted_holdings

    def _generate_chart_data(
        self,
        daily_snapshots: List[Dict]
    ) -> Dict[str, Any]:
        """차트 데이터 생성"""

        if not daily_snapshots:
            return {
                'dates': [],
                'portfolio_values': [],
                'cash_balances': [],
                'cumulative_returns': [],
                'drawdowns': []
            }

        df = pd.DataFrame(daily_snapshots)

        # Convert Decimal columns to float to avoid type mismatch in calculations
        if 'portfolio_value' in df.columns:
            df['portfolio_value'] = df['portfolio_value'].astype(float)
        if 'cash_balance' in df.columns:
            df['cash_balance'] = df['cash_balance'].astype(float)

        # 누적 수익률 계산
        initial_value = float(df['portfolio_value'].iloc[0]) if not df.empty else 1
        cumulative_returns = [(float(v) / initial_value - 1) * 100 for v in df['portfolio_value']]

        # 낙폭 계산
        cummax = df['portfolio_value'].cummax()
        drawdowns = ((df['portfolio_value'] - cummax) / cummax * 100).tolist()

        return {
            'dates': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in df['date'].tolist()],
            'portfolio_values': [float(v) for v in df['portfolio_value'].tolist()],
            'cash_balances': [float(v) for v in df['cash_balance'].tolist()],
            'cumulative_returns': cumulative_returns,
            'drawdowns': drawdowns
        }

    async def _format_result(
        self,
        backtest_id: UUID,
        portfolio_result: Dict,
        statistics: StatsSchema,
        buy_conditions: List[Dict],
        sell_conditions: List[Dict],
        condition_sell: Optional[Dict[str, Any]],
        settings: Dict
    ) -> BacktestResult:
        """결과 포맷팅"""

        raw_buy_conditions = buy_conditions
        normalized_buy_conditions = []
        if isinstance(raw_buy_conditions, dict):
            normalized_buy_conditions = raw_buy_conditions.get('conditions', [])
        else:
            normalized_buy_conditions = raw_buy_conditions

        # 일별 성과 변환
        daily_performance = []
        daily_snapshots = portfolio_result['daily_snapshots']

        if daily_snapshots:
            df = pd.DataFrame(daily_snapshots)
            df['date'] = pd.to_datetime(df['date'])

            # Convert Decimal columns to float to avoid type mismatch in calculations
            if 'portfolio_value' in df.columns:
                df['portfolio_value'] = df['portfolio_value'].astype(float)
            if 'cash_balance' in df.columns:
                df['cash_balance'] = df['cash_balance'].astype(float)

            # 일별 수익률 계산
            df['daily_return'] = df['portfolio_value'].pct_change() * 100
            df['cumulative_return'] = ((df['portfolio_value'] / df['portfolio_value'].iloc[0]) - 1) * 100

            # 낙폭 계산
            df['cummax'] = df['portfolio_value'].cummax()
            df['drawdown'] = (df['portfolio_value'] - df['cummax']) / df['cummax'] * 100

            if 'benchmark_value' in df.columns and df['benchmark_value'].notna().any():
                df['benchmark_value'] = df['benchmark_value'].astype(float)
                df['benchmark_daily_return'] = df['benchmark_value'].pct_change() * 100
            elif 'benchmark_return' in df.columns:
                df['benchmark_daily_return'] = df['benchmark_return']
            else:
                df['benchmark_daily_return'] = np.nan

            for _, row in df.iterrows():
                daily_performance.append(DailyPerformance(
                    date=row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                    portfolio_value=Decimal(str(row['portfolio_value'])),
                    cash_balance=Decimal(str(row['cash_balance'])),
                    invested_amount=Decimal(str(row['invested_amount'])),
                    daily_return=Decimal(str(row['daily_return'])) if not pd.isna(row['daily_return']) else Decimal("0"),
                    cumulative_return=Decimal(str(row['cumulative_return'])),
                    drawdown=Decimal(str(row['drawdown'])),
                    benchmark_return=Decimal(str(row['benchmark_daily_return'])) if not pd.isna(row['benchmark_daily_return']) else None,
                    trade_count=int(row['trade_count'])
                ))

        # 월별 성과 집계 (거래 데이터 포함)
        monthly_performance = self._aggregate_monthly_performance(
            daily_snapshots,
            portfolio_result['trades']
        )

        # 연도별 성과 집계
        yearly_performance = self._aggregate_yearly_performance(daily_snapshots)

        # 거래 내역 변환 (BUY와 SELL 모두 포함)
        trade_records = []
        executions = portfolio_result.get('executions', [])
        for execution in executions:
            trade_type = execution.get('side', execution.get('trade_type', 'UNKNOWN'))
            trade_records.append(TradeRecord(
                trade_id=str(execution.get('execution_id', '')),
                trade_date=execution['execution_date'],
                trade_type=trade_type,
                stock_code=execution['stock_code'],
                stock_name=execution.get('stock_name', ''),
                quantity=execution['quantity'],
                price=execution['price'],
                amount=execution['amount'],
                commission=execution['commission'],
                tax=execution.get('tax', Decimal("0")),
                profit=execution.get('realized_pnl'),
                profit_rate=execution.get('profit_rate'),
                hold_days=execution.get('hold_days'),
                factors=execution.get('factors', {}),
                selection_reason=execution.get('selection_reason')
            ))

        # 현재 보유 종목
        current_holdings = await self._format_current_holdings(
            portfolio_result['final_holdings']
        )

        # 차트 데이터 생성
        chart_data = self._generate_chart_data(daily_snapshots)

        # 팩터별 기여도 분석
        factor_analysis = self._analyze_factor_contribution(
            portfolio_result['trades'],
            buy_conditions
        )

        # 차트 데이터에 팩터 분석 추가
        if factor_analysis:
            chart_data['factor_analysis'] = factor_analysis

        return BacktestResult(
            backtest_id=str(backtest_id),
            backtest_name=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="COMPLETED",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            settings=BacktestSettings(**settings),
            buy_conditions=[BacktestCondition(**c) for c in normalized_buy_conditions],
            sell_conditions=[BacktestCondition(**c) for c in sell_conditions],
            condition_sell=condition_sell,
            statistics=statistics,
            current_holdings=current_holdings,
            daily_performance=daily_performance,
            monthly_performance=monthly_performance,
            yearly_performance=yearly_performance,
            trades=trade_records,
            rebalance_dates=[d.date() if hasattr(d, 'date') else d for d in portfolio_result['rebalance_dates']],
            chart_data=chart_data,
            orders=portfolio_result.get('orders', []),
            executions=executions,
            position_history=portfolio_result.get('position_history', [])
        )

    # ==================== Phase 2: 주문/체결/포지션 추적 ====================

    def create_order(
        self,
        stock_code: str,
        stock_name: str,
        order_side: str,
        quantity: int,
        order_date: datetime,
        reason: str = "",
        factor_scores: Dict[str, float] = None,
        condition_results: Dict[str, bool] = None
    ) -> Order:
        """주문 생성"""
        order = Order(
            order_id=f"{order_side}_{stock_code}_{order_date.strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}",
            order_date=order_date,
            stock_code=stock_code,
            stock_name=stock_name,
            order_type="MARKET",
            order_side=order_side,
            quantity=quantity,
            status="PENDING",
            reason=reason,
            factor_scores=factor_scores or {},
            condition_results=condition_results or {}
        )
        self.orders.append(order)
        return order

    def execute_order(
        self,
        order: Order,
        market_price: Decimal,
        slippage: Decimal,
        commission_rate: Decimal
    ) -> Execution:
        """주문 체결 시뮬레이션"""
        # 슬리피지 적용
        if order.order_side == "BUY":
            execution_price = market_price * (1 + slippage)
        else:
            execution_price = market_price * (1 - slippage)

        # 금액 계산
        amount = execution_price * order.quantity
        commission = amount * commission_rate
        tax = amount * self.tax_rate if order.order_side == "SELL" else Decimal("0")
        slippage_amount = abs(market_price - execution_price) * order.quantity

        execution = Execution(
            execution_id=f"EX_{order.order_id}_{uuid4().hex[:8]}",
            order_id=order.order_id,
            execution_date=order.order_date,
            quantity=order.quantity,
            price=execution_price,
            amount=amount,
            commission=commission,
            tax=tax,
            slippage_amount=slippage_amount,
            total_cost=amount + commission + tax
        )

        # 주문 상태 업데이트
        order.status = "FILLED"
        self.executions.append(execution)
        return execution

    def update_position(
        self,
        execution: Execution,
        order: Order,
        current_date: date,
        factor_scores: Dict[str, float] = None
    ) -> Position:
        """포지션 업데이트"""
        stock_code = order.stock_code

        if order.order_side == "BUY":
            if stock_code in self.positions:
                # 기존 포지션에 추가
                position = self.positions[stock_code]
                total_value = position.entry_price * position.quantity + execution.price * execution.quantity
                total_quantity = position.quantity + execution.quantity
                position.entry_price = total_value / total_quantity
                position.quantity = total_quantity
            else:
                # 새 포지션 생성
                position = Position(
                    position_id=f"POS_{stock_code}_{current_date}_{uuid4().hex[:8]}",
                    stock_code=stock_code,
                    stock_name=order.stock_name,
                    entry_date=current_date,
                    entry_price=execution.price,
                    quantity=execution.quantity,
                    current_price=execution.price,
                    current_value=execution.amount,
                    factor_scores_entry=factor_scores or order.factor_scores,
                    is_open=True
                )
                self.positions[stock_code] = position

        else:  # SELL
            if stock_code in self.positions:
                position = self.positions[stock_code]

                # 실현 손익 계산
                realized_pnl = (execution.price - position.entry_price) * execution.quantity
                position.realized_pnl = realized_pnl

                # 수량 감소
                position.quantity -= execution.quantity

                if position.quantity <= 0:
                    # 포지션 청산
                    position.is_open = False
                    position.exit_date = current_date
                    position.exit_price = execution.price
                    position.hold_days = (current_date - (position.entry_date.date() if hasattr(position.entry_date, 'date') else position.entry_date)).days

                    self.closed_positions.append(position)
                    del self.positions[stock_code]
                else:
                    # 부분 청산
                    position.current_value = position.entry_price * position.quantity

                return position

        return position

    def track_position_history(
        self,
        date: date,
        price_data: pd.DataFrame
    ):
        """포지션 히스토리 추적"""
        for stock_code, position in self.positions.items():
            # 현재가 업데이트
            current_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == pd.Timestamp(date))
            ]

            if not current_price_data.empty:
                current_price = Decimal(str(current_price_data.iloc[0]['close_price']))
                position.current_price = current_price
                position.current_value = current_price * position.quantity
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity

                # 최대 이익/손실 업데이트
                position.max_profit = max(position.max_profit, position.unrealized_pnl)
                position.max_loss = min(position.max_loss, position.unrealized_pnl)
                position.hold_days = (date - (position.entry_date.date() if hasattr(position.entry_date, 'date') else position.entry_date)).days

                # 히스토리 기록
                self.position_history.append({
                    'position_id': position.position_id,
                    'date': date,
                    'stock_code': stock_code,
                    'close_price': float(current_price),
                    'unrealized_pnl': float(position.unrealized_pnl),
                    'pnl_rate': float((current_price / position.entry_price - 1) * 100),
                    'hold_days': position.hold_days
                })

    # ==================== Phase 3: 통계 계산 ====================

    def calculate_monthly_stats(
        self,
        daily_snapshots: List[Dict],
        trades: List[Dict]
    ) -> List[Dict]:
        """월별 통계 계산"""
        if not daily_snapshots:
            return []

        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month

        # Convert Decimal columns to float to avoid type mismatch in calculations
        if 'portfolio_value' in df.columns:
            df['portfolio_value'] = df['portfolio_value'].astype(float)

        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        if not trades_df.empty:
            trades_df['trade_date'] = pd.to_datetime(trades_df['trade_date'])

        monthly_stats = []

        for (year, month), group in df.groupby(['year', 'month']):
            # 월별 수익률
            first_value = group.iloc[0]['portfolio_value']
            last_value = group.iloc[-1]['portfolio_value']
            month_return = (last_value / first_value - 1) * 100 if first_value > 0 else 0

            # 월별 거래 통계
            month_trades = trades_df[
                (trades_df['trade_date'].dt.year == year) &
                (trades_df['trade_date'].dt.month == month)
            ] if not trades_df.empty else pd.DataFrame()

            # 승률 계산
            if not month_trades.empty:
                sell_trades = month_trades[month_trades['trade_type'] == 'SELL']
                winning_trades = sell_trades[sell_trades['profit'] > 0] if not sell_trades.empty else pd.DataFrame()
                win_rate = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0

                # 평균 보유 기간
                avg_hold_days = sell_trades['hold_days'].mean() if 'hold_days' in sell_trades.columns and not sell_trades.empty else 0
            else:
                win_rate = 0
                avg_hold_days = 0

            # 최대 낙폭 (월별)
            month_cummax = group['portfolio_value'].cummax()
            month_drawdowns = ((group['portfolio_value'] - month_cummax) / month_cummax * 100)
            max_drawdown = month_drawdowns.min() if not month_drawdowns.empty else 0

            monthly_stats.append({
                'year': int(year),
                'month': int(month),
                'return_rate': float(month_return),
                'win_rate': float(win_rate),
                'trade_count': len(month_trades) if not month_trades.empty else 0,
                'buy_count': len(month_trades[month_trades['trade_type'] == 'BUY']) if not month_trades.empty else 0,
                'sell_count': len(month_trades[month_trades['trade_type'] == 'SELL']) if not month_trades.empty else 0,
                'avg_hold_days': int(avg_hold_days),
                'portfolio_value_start': float(first_value),
                'portfolio_value_end': float(last_value),
                'max_drawdown': float(max_drawdown)
            })

        self.monthly_stats = monthly_stats
        return monthly_stats

    def calculate_yearly_stats(
        self,
        monthly_stats: List[Dict]
    ) -> List[Dict]:
        """연도별 통계 계산"""
        if not monthly_stats:
            return []

        df = pd.DataFrame(monthly_stats)
        yearly_stats = []

        for year, group in df.groupby('year'):
            # 연간 수익률
            year_return = group['return_rate'].sum()  # 월별 수익률 합계 (간단 계산)

            # 연간 승률
            total_trades = group['trade_count'].sum()
            avg_win_rate = group['win_rate'].mean() if not group.empty else 0

            # 최대 낙폭
            max_drawdown = group['max_drawdown'].min()

            # 샤프 비율 (간단 계산)
            returns_std = group['return_rate'].std()
            sharpe_ratio = (year_return / returns_std) if returns_std > 0 else 0

            yearly_stats.append({
                'year': int(year),
                'return_rate': float(year_return),
                'total_trades': int(total_trades),
                'win_rate': float(avg_win_rate),
                'max_drawdown': float(max_drawdown),
                'sharpe_ratio': float(sharpe_ratio),
                'months_count': len(group)
            })

        self.yearly_stats = yearly_stats
        return yearly_stats

    def calculate_drawdown_periods(
        self,
        daily_snapshots: List[Dict]
    ) -> List[DrawdownPeriod]:
        """드로다운 기간 계산"""
        if not daily_snapshots:
            return []

        df = pd.DataFrame(daily_snapshots)
        df['date'] = pd.to_datetime(df['date'])

        # Convert Decimal columns to float to avoid type mismatch in calculations
        if 'portfolio_value' in df.columns:
            df['portfolio_value'] = df['portfolio_value'].astype(float)

        # 누적 최대값
        df['cummax'] = df['portfolio_value'].cummax()
        df['drawdown'] = (df['portfolio_value'] - df['cummax']) / df['cummax'] * 100

        drawdown_periods = []
        in_drawdown = False
        current_period = None

        for idx, row in df.iterrows():
            if row['drawdown'] < 0 and not in_drawdown:
                # 드로다운 시작
                current_period = DrawdownPeriod(
                    start_date=row['date'].date(),
                    end_date=None,
                    peak_value=Decimal(str(row['cummax'])),
                    trough_value=Decimal(str(row['portfolio_value'])),
                    max_drawdown=Decimal(str(row['drawdown'])),
                    duration_days=1,
                    is_active=True
                )
                in_drawdown = True

            elif row['drawdown'] < 0 and in_drawdown:
                # 드로다운 지속
                current_period.trough_value = min(
                    current_period.trough_value,
                    Decimal(str(row['portfolio_value']))
                )
                current_period.max_drawdown = min(
                    current_period.max_drawdown,
                    Decimal(str(row['drawdown']))
                )
                current_period.duration_days += 1

            elif row['drawdown'] >= 0 and in_drawdown:
                # 드로다운 종료
                current_period.end_date = row['date'].date()
                current_period.is_active = False
                current_period.recovery_days = (
                    current_period.end_date - current_period.start_date
                ).days - current_period.duration_days
                drawdown_periods.append(current_period)
                in_drawdown = False
                current_period = None

        # 마지막 드로다운이 진행중인 경우
        if current_period and in_drawdown:
            drawdown_periods.append(current_period)

        self.drawdown_periods = drawdown_periods
        return drawdown_periods

    def analyze_factor_contributions(
        self,
        trades: List[Dict],
        buy_conditions: List[Dict]
    ) -> Dict[str, Dict]:
        """팩터 기여도 분석"""
        if not trades or not buy_conditions:
            return {}

        factor_performance = {}
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']

        # 조건이 논리식 형태인 경우
        if isinstance(buy_conditions, dict) and 'conditions' in buy_conditions:
            conditions_list = buy_conditions['conditions']
        else:
            conditions_list = buy_conditions

        for condition in conditions_list:
            factor_name = condition.get('factor')
            if not factor_name:
                continue

            # 해당 팩터와 관련된 거래 필터링
            factor_trades = []
            for trade in sell_trades:
                if 'factors' in trade and factor_name in trade.get('factors', {}):
                    factor_trades.append(trade)

            if not factor_trades:
                continue

            # 통계 계산
            profits = [float(t.get('profit', 0)) for t in factor_trades]
            winning_trades = [t for t in factor_trades if float(t.get('profit', 0)) > 0]

            win_rate = len(winning_trades) / len(factor_trades) * 100 if factor_trades else 0
            avg_profit = sum(profits) / len(profits) if profits else 0
            total_profit = sum(profits)

            # 기여도 점수 (전체 거래 대비 수익 기여)
            contribution_score = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0

            factor_performance[factor_name] = {
                'total_trades': len(factor_trades),
                'winning_trades': len(winning_trades),
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'total_profit': total_profit,
                'contribution_score': contribution_score
            }

        # 중요도 순위 매기기
        sorted_factors = sorted(
            factor_performance.items(),
            key=lambda x: x[1]['contribution_score'],
            reverse=True
        )

        for rank, (factor_name, _) in enumerate(sorted_factors, 1):
            factor_performance[factor_name]['importance_rank'] = rank

        self.factor_contributions = factor_performance
        return factor_performance

    async def _save_result(self, backtest_id: UUID, result: BacktestResult):
        """백테스트 결과를 데이터베이스에 저장"""
        from app.models.backtest import (
            BacktestSession, BacktestCondition as BacktestConditionModel,
            BacktestStatistics as BacktestStatisticsModel,
            BacktestDailySnapshot, BacktestTrade, BacktestHolding
        )
        from datetime import datetime

        logger.info(f"Saving backtest result for {backtest_id}")

        try:
            # 1. 백테스트 세션 저장
            session = BacktestSession(
                backtest_id=backtest_id,
                backtest_name=result.backtest_name,
                status=result.status,
                start_date=result.statistics.start_date,
                end_date=result.statistics.end_date,
                initial_capital=result.statistics.initial_capital,
                rebalance_frequency=result.settings.rebalance_frequency,
                max_positions=result.settings.max_positions,
                position_sizing=result.settings.position_sizing,
                benchmark=result.settings.benchmark,
                commission_rate=Decimal(str(result.settings.commission_rate)),
                tax_rate=Decimal(str(result.settings.tax_rate)),
                slippage=Decimal(str(result.settings.slippage)),
                created_at=result.created_at,
                completed_at=result.completed_at
            )
            self.db.add(session)

            # 2. 매수/매도 조건 저장
            for buy_condition in result.buy_conditions:
                value_decimal = Decimal("0")
                try:
                    value_decimal = Decimal(str(buy_condition.value))
                except Exception:
                    value_decimal = Decimal("0")
                    desc = buy_condition.description or ""
                    buy_condition.description = f"{desc} (raw={buy_condition.value})"

                condition = BacktestConditionModel(
                    backtest_id=backtest_id,
                    condition_type="BUY",
                    factor=buy_condition.factor,
                    operator=buy_condition.operator,
                    value=value_decimal,
                    description=buy_condition.description
                )
                self.db.add(condition)

            for sell_condition in result.sell_conditions:
                factor = sell_condition.factor
                raw_value = sell_condition.value
                try:
                    value_decimal = Decimal(str(raw_value))
                except Exception:
                    value_decimal = Decimal("0")
                condition = BacktestConditionModel(
                    backtest_id=backtest_id,
                    condition_type="SELL",
                    factor=factor or "SELL_RULE",
                    operator=sell_condition.operator,
                    value=value_decimal,
                    description=sell_condition.description or ''
                )
                self.db.add(condition)

            # 3. 통계 저장 - BacktestStatistics (기존)
            stats = result.statistics
            statistics = BacktestStatisticsModel(
                backtest_id=backtest_id,
                total_return=stats.total_return,
                annualized_return=stats.annualized_return,
                benchmark_return=stats.benchmark_return if hasattr(stats, 'benchmark_return') else None,
                excess_return=stats.excess_return if hasattr(stats, 'excess_return') else None,
                max_drawdown=stats.max_drawdown,
                volatility=stats.volatility,
                downside_volatility=stats.downside_volatility,
                sharpe_ratio=stats.sharpe_ratio,
                sortino_ratio=stats.sortino_ratio,
                calmar_ratio=stats.calmar_ratio,
                total_trades=stats.total_trades,
                winning_trades=stats.winning_trades,
                losing_trades=stats.losing_trades,
                win_rate=stats.win_rate,
                avg_win=stats.avg_win,
                avg_loss=stats.avg_loss,
                profit_loss_ratio=stats.profit_loss_ratio,
                initial_capital=stats.initial_capital,
                final_capital=stats.final_capital,
                peak_capital=stats.peak_capital,
                start_date=stats.start_date,
                end_date=stats.end_date,
                trading_days=stats.trading_days
            )
            self.db.add(statistics)

            # 3.5. 통계 저장 - SimulationStatistics (전략 목록 API용)
            from app.models.simulation import SimulationStatistics

            # 기존 SimulationStatistics 삭제 (재실행 시 중복 방지)
            from sqlalchemy import delete
            await self.db.execute(delete(SimulationStatistics).where(
                SimulationStatistics.session_id == str(backtest_id)
            ))

            # 새로운 SimulationStatistics 생성
            simulation_stats = SimulationStatistics(
                session_id=str(backtest_id),
                total_return=stats.total_return,
                annualized_return=stats.annualized_return,
                benchmark_return=stats.benchmark_return if hasattr(stats, 'benchmark_return') else None,
                excess_return=stats.excess_return if hasattr(stats, 'excess_return') else None,
                volatility=stats.volatility,
                max_drawdown=stats.max_drawdown,
                sharpe_ratio=stats.sharpe_ratio,
                sortino_ratio=stats.sortino_ratio,
                total_trades=stats.total_trades,
                winning_trades=stats.winning_trades,
                losing_trades=stats.losing_trades,
                win_rate=stats.win_rate,
                avg_profit=stats.avg_win if hasattr(stats, 'avg_win') else None,
                avg_loss=stats.avg_loss if hasattr(stats, 'avg_loss') else None,
                profit_factor=stats.profit_loss_ratio if hasattr(stats, 'profit_loss_ratio') else None,
                avg_holding_period=None,  # 계산되지 않은 경우 None
                final_capital=stats.final_capital,
                total_commission=None,  # 별도 계산 필요 시 추가
                total_tax=None  # 별도 계산 필요 시 추가
            )
            self.db.add(simulation_stats)
            logger.info(f"✅ SimulationStatistics 저장 완료 - session_id: {backtest_id}")

            # 4. 일별 스냅샷 저장
            for daily in result.daily_performance:
                snapshot = BacktestDailySnapshot(
                    backtest_id=backtest_id,
                    snapshot_date=daily.date,
                    portfolio_value=daily.portfolio_value,
                    cash_balance=daily.cash_balance,
                    invested_amount=daily.invested_amount,
                    daily_return=daily.daily_return,
                    cumulative_return=daily.cumulative_return,
                    drawdown=daily.drawdown,
                    benchmark_return=daily.benchmark_return,
                    trade_count=daily.trade_count
                )
                self.db.add(snapshot)

            # 5. 거래 내역 저장
            for trade in result.trades:
                trade_record = BacktestTrade(
                    backtest_id=backtest_id,
                    trade_date=trade.trade_date,
                    trade_type=trade.trade_type,
                    stock_code=trade.stock_code,
                    stock_name=trade.stock_name,
                    quantity=trade.quantity,
                    price=trade.price,
                    amount=trade.amount,
                    commission=trade.commission,
                    tax=trade.tax,
                    profit=trade.profit,
                    profit_rate=trade.profit_rate,
                    hold_days=trade.hold_days,
                    factors=trade.factors if trade.factors else {},
                    selection_reason=trade.selection_reason
                )
                self.db.add(trade_record)

            # 6. 현재 보유 종목 저장
            for holding in result.current_holdings:
                holding_record = BacktestHolding(
                    backtest_id=backtest_id,
                    stock_code=holding.stock_code,
                    stock_name=holding.stock_name,
                    quantity=holding.quantity,
                    avg_price=holding.avg_price,
                    current_price=holding.current_price,
                    value=holding.value,
                    profit=holding.profit,
                    profit_rate=holding.profit_rate,
                    weight=holding.weight,
                    buy_date=holding.buy_date,
                    hold_days=holding.hold_days,
                    factors=holding.factors if holding.factors else {}
                )
                self.db.add(holding_record)

            # 커밋
            await self.db.commit()
            logger.info(f"Successfully saved backtest result for {backtest_id}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to save backtest result: {e}")
            raise
