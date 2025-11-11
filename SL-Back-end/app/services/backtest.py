"""
GenPort 스타일 백테스트 엔진 (확장판)
- 논리식 조건 지원
- 주문/체결/포지션 추적
- 상세 통계 계산
"""

import asyncio
import logging
import copy
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any, Union
from uuid import UUID, uuid4
import pandas as pd
import numpy as np
import polars as pl
from collections import defaultdict
from dataclasses import dataclass, asdict

from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Company, StockPrice, FinancialStatement,
    BalanceSheet, IncomeStatement, CashflowStatement
)
from app.schemas.backtest_genport import (
    BacktestResultGenPort, PortfolioHolding, DailyPerformance,
    MonthlyPerformance, YearlyPerformance, TradeRecord,
    BacktestStatistics as StatsSchema, BacktestCondition,
    BacktestSettings
)
from app.services.condition_evaluator import ConditionEvaluator, LogicalExpressionParser

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

    async def run_backtest(
        self,
        backtest_id: UUID,
        buy_conditions: List[Dict],
        sell_conditions: List[Dict],
        start_date: date,
        end_date: date,
        condition_sell: Optional[Dict[str, Any]] = None,
        initial_capital: Decimal = Decimal("100000000"),
        rebalance_frequency: str = "MONTHLY",
        max_positions: int = 20,
        position_sizing: str = "EQUAL_WEIGHT",
        benchmark: str = "KOSPI",
        commission_rate: float = 0.00015,  # 0.015% 기본값
        slippage: float = 0.001  # 0.1% 기본값
    ) -> BacktestResultGenPort:
        """백테스트 실행"""

        # Decimal로 변환
        self.commission_rate = Decimal(str(commission_rate))
        self.slippage = Decimal(str(slippage))

        try:
            # 1. 데이터 준비
            logger.info(f"백테스트 시작: {backtest_id}")
            price_data = await self._load_price_data(start_date, end_date)
            financial_data = await self._load_financial_data(start_date, end_date)

            # 2. 팩터 계산 - 통합 모듈 사용 (54개 팩터)
            from app.services.factor_integration import FactorIntegration
            factor_integrator = FactorIntegration(self.db)

            # 모든 종목 코드 추출
            stock_codes = price_data['stock_code'].unique().tolist() if not price_data.empty else None

            # 54개 팩터 모두 계산
            factor_data = await factor_integrator.get_integrated_factor_data(
                start_date=start_date,
                end_date=end_date,
                stock_codes=stock_codes
            )

            logger.info(f"팩터 계산 완료: {len(factor_data)}개 레코드, {len(factor_data.columns)-3}개 팩터")

            # 기존 13개 팩터 계산은 백업용으로 남겨둠 (필요시 폴백)
            if factor_data.empty:
                logger.warning("통합 팩터 계산 실패, 기존 방식으로 폴백")
                factor_data = await self._calculate_all_factors(
                    price_data, financial_data, start_date, end_date
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

    async def _load_price_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """가격 데이터 로드"""

        # 날짜 범위 확장 (모멘텀 계산을 위해 252일 추가)
        extended_start = start_date - timedelta(days=365)

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
            and_(
                StockPrice.trade_date >= extended_start,
                StockPrice.trade_date <= end_date,
                StockPrice.close_price.isnot(None),
                StockPrice.volume > 0
            )
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

        logger.info(f"Loaded {len(df)} price records for {df['stock_code'].nunique()} stocks")

        return df

    async def _load_financial_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """재무 데이터 로드"""

        # 재무제표 기간 설정 (분기별 데이터 고려)
        extended_start = start_date - timedelta(days=180)  # 6개월 전 데이터부터

        # 손익계산서 데이터
        income_query = select(
            FinancialStatement.company_id,
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            FinancialStatement.report_date,
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
                FinancialStatement.report_date >= extended_start,
                FinancialStatement.report_date <= end_date,
                IncomeStatement.account_nm.in_([
                    '매출액', '매출', '영업수익',
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
            FinancialStatement.report_date,
            BalanceSheet.account_nm,
            BalanceSheet.thstrm_amount.label('current_amount')
        ).join(
            BalanceSheet, FinancialStatement.stmt_id == BalanceSheet.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(
                FinancialStatement.report_date >= extended_start,
                FinancialStatement.report_date <= end_date,
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

        # 데이터 통합 및 피벗
        if not income_df.empty:
            income_pivot = income_df.pivot_table(
                index=['company_id', 'stock_code', 'fiscal_year', 'report_code', 'report_date'],
                columns='account_nm',
                values='current_amount',
                aggfunc='first'
            ).reset_index()
        else:
            income_pivot = pd.DataFrame()

        if not balance_df.empty:
            balance_pivot = balance_df.pivot_table(
                index=['company_id', 'stock_code', 'fiscal_year', 'report_code', 'report_date'],
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
                on=['company_id', 'stock_code', 'fiscal_year', 'report_code', 'report_date'],
                how='outer'
            )
        elif not income_pivot.empty:
            financial_df = income_pivot
        elif not balance_pivot.empty:
            financial_df = balance_pivot
        else:
            financial_df = pd.DataFrame()

        if not financial_df.empty:
            financial_df['report_date'] = pd.to_datetime(financial_df['report_date'])
            logger.info(f"Loaded financial data for {financial_df['stock_code'].nunique()} companies")

        return financial_df

    async def _load_benchmark_data(self, benchmark: str, start_date: date, end_date: date) -> pd.DataFrame:
        """벤치마크 데이터 로드 (KOSPI/KOSDAQ)"""

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

        return benchmark_df

    async def _calculate_all_factors(
        self,
        price_data: pd.DataFrame,
        financial_data: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """모든 팩터 계산"""

        logger.info("팩터 계산 시작")

        if price_data.empty:
            logger.warning("No price data available for factor calculation")
            return pd.DataFrame()

        # Polars DataFrame으로 변환 (성능 향상)
        price_pl = pl.from_pandas(price_data)
        financial_pl = pl.from_pandas(financial_data) if not financial_data.empty else None

        factor_rows: List[Dict[str, Any]] = []
        unique_dates = sorted(price_data[price_data['date'] >= pd.Timestamp(start_date)]['date'].unique())

        for calc_date in unique_dates:
            todays_prices = price_data[price_data['date'] == calc_date]
            if todays_prices.empty:
                continue

            industry_map = {}
            if 'industry' in todays_prices.columns:
                industry_map = dict(zip(todays_prices['stock_code'], todays_prices['industry']))

            size_bucket_map = self._assign_size_buckets(todays_prices)
            stock_factor_map: Dict[str, Dict[str, float]] = defaultdict(dict)
            price_until_date = price_pl.filter(pl.col('date') <= calc_date)

            if financial_pl is not None:
                value_map = self._calculate_value_factors(price_until_date, financial_pl, calc_date)
                self._merge_factor_maps(stock_factor_map, value_map)

                profit_map = self._calculate_profitability_factors(financial_pl, calc_date)
                self._merge_factor_maps(stock_factor_map, profit_map)

                growth_map = self._calculate_growth_factors(financial_pl, calc_date)
                self._merge_factor_maps(stock_factor_map, growth_map)

            momentum_map = self._calculate_momentum_factors(price_until_date, calc_date)
            self._merge_factor_maps(stock_factor_map, momentum_map)

            volatility_map = self._calculate_volatility_factors(price_until_date, calc_date)
            self._merge_factor_maps(stock_factor_map, volatility_map)

            liquidity_map = self._calculate_liquidity_factors(price_until_date, calc_date)
            self._merge_factor_maps(stock_factor_map, liquidity_map)

            for stock in todays_prices['stock_code'].unique():
                record = {
                    'date': pd.Timestamp(calc_date),
                    'stock_code': stock,
                    'industry': industry_map.get(stock),
                    'size_bucket': size_bucket_map.get(stock)
                }
                record.update(stock_factor_map.get(stock, {}))
                factor_rows.append(record)

        factor_df = pd.DataFrame(factor_rows)

        if not factor_df.empty:
            # 팩터 정규화 및 순위 계산
            factor_df = self._normalize_factors(factor_df)
            factor_df = self._calculate_factor_ranks(factor_df)

            logger.info(
                "팩터 계산 완료: %d개 종목-일 조합, %d개 팩터",
                len(factor_df),
                len([c for c in factor_df.columns if c not in ('date', 'stock_code')])
            )

        return factor_df

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

    def _calculate_value_factors(self, price_pl: pl.DataFrame, financial_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """가치 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        latest_price = price_pl.filter(pl.col('date') == calc_date)
        latest_financial = financial_pl.filter(pl.col('report_date') <= calc_date)

        if latest_price.is_empty() or latest_financial.is_empty():
            return factors

        for stock in latest_price.select('stock_code').unique().to_pandas()['stock_code']:
            stock_price = latest_price.filter(pl.col('stock_code') == stock)
            stock_financial = latest_financial.filter(pl.col('stock_code') == stock)

            if stock_financial.is_empty():
                continue

            stock_financial = stock_financial.sort('report_date', descending=True).head(1)
            entry = factors.setdefault(stock, {})

            net_income = stock_financial.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in stock_financial.columns else None
            equity = stock_financial.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in stock_financial.columns else None
            market_cap = stock_price.select('market_cap').to_pandas().iloc[0, 0] if 'market_cap' in stock_price.columns else None

            if net_income and market_cap and net_income > 0:
                entry['PER'] = float(market_cap) / float(net_income)
            if equity and market_cap and equity > 0:
                entry['PBR'] = float(market_cap) / float(equity)

        return factors

    def _calculate_profitability_factors(self, financial_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """수익성 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        latest_financial = financial_pl.filter(pl.col('report_date') <= calc_date)

        if latest_financial.is_empty():
            return factors

        for stock in latest_financial.select('stock_code').unique().to_pandas()['stock_code']:
            stock_financial = latest_financial.filter(pl.col('stock_code') == stock).sort('report_date', descending=True).head(1)
            entry = factors.setdefault(stock, {})

            net_income = stock_financial.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in stock_financial.columns else None
            equity = stock_financial.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in stock_financial.columns else None
            assets = stock_financial.select('자산총계').to_pandas().iloc[0, 0] if '자산총계' in stock_financial.columns else None

            if net_income and equity and equity > 0:
                entry['ROE'] = float(net_income) / float(equity) * 100
            if net_income and assets and assets > 0:
                entry['ROA'] = float(net_income) / float(assets) * 100

        return factors

    def _calculate_growth_factors(self, financial_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """성장성 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        current_financial = financial_pl.filter(pl.col('report_date') <= calc_date)
        year_ago = calc_date - pd.Timedelta(days=365)
        past_financial = financial_pl.filter(pl.col('report_date') <= year_ago)

        if current_financial.is_empty() or past_financial.is_empty():
            return factors

        for stock in current_financial.select('stock_code').unique().to_pandas()['stock_code']:
            current = current_financial.filter(pl.col('stock_code') == stock).sort('report_date', descending=True).head(1)
            past = past_financial.filter(pl.col('stock_code') == stock).sort('report_date', descending=True).head(1)

            if past.is_empty():
                continue

            entry = factors.setdefault(stock, {})

            if '매출액' in current.columns and '매출액' in past.columns:
                current_revenue = current.select('매출액').to_pandas().iloc[0, 0]
                past_revenue = past.select('매출액').to_pandas().iloc[0, 0]
                if current_revenue and past_revenue and past_revenue > 0:
                    entry['REVENUE_GROWTH'] = (float(current_revenue) / float(past_revenue) - 1) * 100

            if '당기순이익' in current.columns and '당기순이익' in past.columns:
                current_income = current.select('당기순이익').to_pandas().iloc[0, 0]
                past_income = past.select('당기순이익').to_pandas().iloc[0, 0]
                if current_income and past_income and past_income > 0:
                    entry['EARNINGS_GROWTH'] = (float(current_income) / float(past_income) - 1) * 100

        return factors

    def _calculate_momentum_factors(self, price_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """모멘텀 팩터 계산"""
        factors: Dict[str, Dict[str, float]] = {}
        periods = {
            'MOMENTUM_1M': 20,
            'MOMENTUM_3M': 60,
            'MOMENTUM_6M': 120,
            'MOMENTUM_12M': 240
        }

        current_prices = price_pl.filter(pl.col('date') == calc_date)
        if current_prices.is_empty():
            return factors

        for stock in current_prices.select('stock_code').unique().to_pandas()['stock_code']:
            stock_current = current_prices.filter(pl.col('stock_code') == stock)
            entry = factors.setdefault(stock, {})

            for factor_name, lookback_days in periods.items():
                past_date = calc_date - pd.Timedelta(days=lookback_days * 1.2)
                past_window = price_pl.filter(
                    (pl.col('stock_code') == stock) &
                    (pl.col('date') >= past_date) &
                    (pl.col('date') <= calc_date - pd.Timedelta(days=lookback_days))
                ).sort('date', descending=True)

                if past_window.is_empty():
                    continue

                past_price = past_window.select('close_price').to_pandas().iloc[-1, 0]
                current_price = stock_current.select('close_price').to_pandas().iloc[0, 0]

                if past_price and current_price and past_price > 0:
                    entry[factor_name] = (float(current_price) / float(past_price) - 1) * 100

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

    def _normalize_factors(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """팩터 정규화 (Z-Score)"""

        if factor_df.empty:
            return factor_df

        normalized_df = factor_df.copy()

        meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
        factor_columns = [col for col in factor_df.columns if col not in meta_columns]

        for col in factor_columns:
            if col not in normalized_df.columns:
                continue

            series = normalized_df[col]
            if series.dropna().empty:
                continue

            lower = series.quantile(0.01)
            upper = series.quantile(0.99)
            normalized_df[col] = series.clip(lower, upper)

            mean = normalized_df[col].mean()
            std = normalized_df[col].std()
            if std and std > 0:
                normalized_df[col] = (normalized_df[col] - mean) / std

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
        """팩터별 순위 계산"""

        if factor_df.empty:
            return factor_df

        ranked_df = factor_df.copy()
        meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
        factor_columns = [col for col in factor_df.columns if col not in meta_columns]
        lower_is_better = {'PER', 'PBR', 'VOLATILITY'}

        for col in factor_columns:
            ascending = col in lower_is_better
            ranked_df[f'{col}_RANK'] = ranked_df.groupby('date')[col].rank(
                ascending=ascending,
                method='average'
            )

        return ranked_df

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
        for trading_day in trading_days:
            if trading_day < pd.Timestamp(start_date) or trading_day > pd.Timestamp(end_date):
                continue

            # 매도 신호 확인 및 실행 (매일 체크)
            sell_trades = await self._execute_sells(
                holdings, factor_data, sell_conditions,
                condition_sell,
                price_data, trading_day, cash_balance,
                orders, executions
            )
            sell_executions = sell_trades

            # 매도 후 현금 업데이트
            for trade in sell_trades:
                cash_balance += trade['amount'] - trade['commission'] - trade['tax']
                position = holdings.get(trade['stock_code'])
                if position:
                    position.is_open = False
                    position.exit_date = trading_day
                    position.exit_price = trade['price']
                    position.realized_pnl = (trade['price'] - position.entry_price) * position.quantity
                    self.closed_positions.append(position)
                    del holdings[trade['stock_code']]

            # 리밸런싱 체크 (매수는 리밸런싱 날짜에만)
            if pd.Timestamp(trading_day) in [pd.Timestamp(d) for d in rebalance_dates]:
                # 매수 종목 선정
                buy_candidates = await self._select_buy_candidates(
                    factor_data=factor_data,
                    buy_conditions=buy_conditions,
                    trading_day=trading_day,
                    price_data=price_data,
                    holdings=holdings,
                    max_positions=max_positions,
                    priority_factor=priority_factor,
                    priority_order=priority_order
                )

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
                buy_trades = await self._execute_buys(
                    position_sizes=position_sizes,
                    price_data=price_data,
                    trading_day=trading_day,
                    cash_balance=cash_balance,
                    holdings=holdings,
                    factor_data=factor_data,
                    orders=orders,
                    executions=executions
                )
                buy_executions = buy_trades

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
        executions: List[Dict[str, Any]]
    ) -> List[Dict]:
        """매도 실행"""

        sell_executions = []
        trading_ts = pd.Timestamp(trading_day)
        date_factors = pd.DataFrame()
        if factor_data is not None and not factor_data.empty:
            date_factors = factor_data[factor_data['date'] == trading_ts]

        for stock_code, holding in list(holdings.items()):
            # 현재가 조회
            current_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == trading_day)
            ]

            if current_price_data.empty:
                continue

            current_price = Decimal(str(current_price_data.iloc[0]['close_price']))

            # 매도 조건 체크
            should_sell = False
            sell_reason = ""

            for condition in sell_conditions:
                if condition.get('type') == 'STOP_LOSS':
                    # 손절 조건
                    loss_rate = ((current_price / holding.entry_price) - 1) * 100
                    if loss_rate <= -float(condition.get('value', 10)):
                        should_sell = True
                        sell_reason = f"Stop loss triggered: {loss_rate:.2f}%"
                        break

                elif condition.get('type') == 'TAKE_PROFIT':
                    # 익절 조건
                    profit_rate = ((current_price / holding.entry_price) - 1) * 100
                    if profit_rate >= float(condition.get('value', 20)):
                        should_sell = True
                        sell_reason = f"Take profit triggered: {profit_rate:.2f}%"
                        break

                elif condition.get('type') == 'HOLD_DAYS':
                    # 보유 기간 조건
                    hold_days = (trading_day - holding.entry_date).days
                    if hold_days >= int(condition.get('value', 30)):
                        should_sell = True
                        sell_reason = f"Hold period exceeded: {hold_days} days"
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

            if should_sell:
                # 매도 실행
                quantity = holding.quantity

                # 슬리피지 적용 (매도 시 불리하게 - 가격 하락)
                execution_price = current_price * (1 - self.slippage)

                amount = execution_price * quantity
                commission = amount * self.commission_rate
                tax = amount * self.tax_rate

                profit = (execution_price - holding.entry_price) * quantity
                profit_rate = ((execution_price / holding.entry_price) - 1) * 100

                order = {
                    'order_id': f"ORD-S-{stock_code}-{trading_day}",
                    'order_date': trading_day,
                    'stock_code': stock_code,
                    'stock_name': f"Stock_{stock_code}",
                    'side': 'SELL',
                    'order_type': 'MARKET',
                    'quantity': quantity,
                    'status': 'FILLED',
                    'reason': sell_reason
                }
                orders.append(order)

                execution = {
                    'execution_id': f"EXE-S-{stock_code}-{trading_day}",
                    'order_id': order['order_id'],
                    'execution_date': trading_day,
                    'trade_date': trading_day,
                    'stock_code': stock_code,
                    'stock_name': f"Stock_{stock_code}",
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
                    'hold_days': (trading_day - holding.entry_date).days,
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

        # 현재 보유 종목 제외
        tradeable_stocks = [s for s in tradeable_stocks if s not in holdings]

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
        allocatable_cash = cash_balance * Decimal("0.95")

        if position_sizing == "EQUAL_WEIGHT":
            allocation_per_stock = allocatable_cash / num_positions
            for stock in effective_candidates:
                position_sizes[stock] = allocation_per_stock
            return position_sizes

        closes = price_data[
            (price_data['date'] == trading_day) &
            (price_data['stock_code'].isin(effective_candidates))
        ][['stock_code', 'close_price', 'market_cap']].dropna()

        if closes.empty:
            allocation_per_stock = allocatable_cash / num_positions
            for stock in buy_candidates[:num_positions]:
                position_sizes[stock] = allocation_per_stock
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
                position_sizes[stock] = Decimal(str(w)) * allocatable_cash
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
                    position_sizes[stock] = allocation_per_stock
                return position_sizes

            total = sum(vol_map.values())
            for stock in effective_candidates:
                w = vol_map.get(stock, 0)
                if total > 0:
                    position_sizes[stock] = Decimal(str(w / total)) * allocatable_cash
                else:
                    position_sizes[stock] = Decimal("0")

            return position_sizes

        allocation_per_stock = allocatable_cash / num_positions
        for stock in effective_candidates:
            position_sizes[stock] = allocation_per_stock

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
        executions: List[Dict[str, Any]] = None
    ) -> List[Dict]:
        """매수 실행 (팩터 정보 포함)"""

        buy_trades = []

        for stock_code, allocation in position_sizes.items():
            # 현재가 조회
            current_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == trading_day)
            ]

            if current_price_data.empty:
                continue

            current_price = Decimal(str(current_price_data.iloc[0]['close_price']))

            # 슬리피지 적용
            execution_price = current_price * (1 + self.slippage)

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
                    for col in stock_factors.columns:
                        if col in ('date', 'stock_code') or col.endswith('_RANK'):
                            continue
                        value = stock_factors[col].iloc[0]
                        if pd.notna(value):
                            trade_factors[col] = float(value)

            # 매수 실행
            order = {
                'order_id': f"ORD-B-{stock_code}-{trading_day}",
                'order_date': trading_day,
                'stock_code': stock_code,
                'stock_name': f"Stock_{stock_code}",
                'side': 'BUY',
                'order_type': 'MARKET',
                'quantity': quantity,
                'status': 'FILLED',
                'reason': "Factor-based selection"
            }
            if orders is not None:
                orders.append(order)

            execution = {
                'execution_id': f"EXE-B-{stock_code}-{trading_day}",
                'order_id': order['order_id'],
                'execution_date': trading_day,
                'trade_date': trading_day,
                'stock_code': stock_code,
                'stock_name': f"Stock_{stock_code}",
                'side': 'BUY',
                'trade_type': 'BUY',
                'quantity': quantity,
                'price': execution_price,
                'amount': amount,
                'commission': commission,
                'tax': Decimal("0"),
                'slippage': self.slippage,
                'factors': trade_factors,
                'selection_reason': "Factor-based selection"
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
            else:
                holdings[stock_code] = Position(
                    position_id=f"POS-{stock_code}-{trading_day}",
                    stock_code=stock_code,
                    stock_name=f"Stock_{stock_code}",
                    entry_date=trading_day,
                    entry_price=execution_price,
                    quantity=quantity,
                    current_price=execution_price,
                    current_value=execution_price * quantity
                )

        return buy_trades

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
        """포트폴리오 가치 계산"""

        total_value = cash_balance

        for stock_code, holding in holdings.items():
            current_price_data = price_data[
                (price_data['stock_code'] == stock_code) &
                (price_data['date'] == trading_day)
            ]

            if not current_price_data.empty:
                current_price = Decimal(str(current_price_data.iloc[0]['close_price']))
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

        # 변동성
        volatility = df['daily_return'].std() * np.sqrt(252) * 100 if not df['daily_return'].empty else 0

        # 하방 변동성
        negative_returns = df['daily_return'][df['daily_return'] < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252) * 100 if not negative_returns.empty else 0

        # 샤프 비율
        risk_free_rate = 0.02  # 2% 무위험 수익률
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

        # 소르티노 비율
        sortino_ratio = (annualized_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0

        # 칼마 비율
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

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

        # 각 팩터별 성과 분석
        for condition in buy_conditions:
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
                hold_days=(latest_date - holding.entry_date).days if latest_date else 0,
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
    ) -> BacktestResultGenPort:
        """결과 포맷팅"""

        # 일별 성과 변환
        daily_performance = []
        daily_snapshots = portfolio_result['daily_snapshots']

        if daily_snapshots:
            df = pd.DataFrame(daily_snapshots)
            df['date'] = pd.to_datetime(df['date'])

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

        # 거래 내역 변환
        trade_records = []
        executions = portfolio_result.get('executions', [])
        for execution in executions:
            if execution.get('side') != 'SELL':
                continue
            trade_records.append(TradeRecord(
                trade_id=execution.get('execution_id', ''),
                trade_date=execution['execution_date'],
                trade_type='SELL',
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

        return BacktestResultGenPort(
            backtest_id=str(backtest_id),
            backtest_name=f"genport_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="COMPLETED",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            settings=BacktestSettings(**settings),
            buy_conditions=[BacktestCondition(**c) for c in buy_conditions],
            sell_conditions=[BacktestCondition(**c) for c in sell_conditions],
            condition_sell=condition_sell,
            statistics=statistics,
            current_holdings=current_holdings,
            daily_performance=daily_performance,
            monthly_performance=monthly_performance,
            yearly_performance=yearly_performance,
            trades=trade_records,
            rebalance_dates=[d.date() if hasattr(d, 'date') else d for d in portfolio_result['rebalance_dates']],
            chart_data=chart_data
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
                    position.hold_days = (current_date - position.entry_date).days

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
                position.hold_days = (date - position.entry_date).days

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

    async def _save_result(self, backtest_id: UUID, result: BacktestResultGenPort):
        """백테스트 결과를 데이터베이스에 저장"""
        from app.models.backtest_genport import (
            BacktestSession, BacktestCondition, BacktestStatistics,
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
                condition = BacktestCondition(
                    backtest_id=backtest_id,
                    condition_type="BUY",
                    factor=buy_condition.factor,
                    operator=buy_condition.operator,
                    value=Decimal(str(buy_condition.value)),
                    description=buy_condition.description
                )
                self.db.add(condition)

            for sell_condition in result.sell_conditions:
                # 매도 조건은 type이 있는 경우와 factor가 있는 경우 구분
                if hasattr(sell_condition, 'factor'):
                    factor = sell_condition.factor
                else:
                    # STOP_LOSS, TAKE_PROFIT, HOLD_DAYS 같은 타입
                    factor = sell_condition.get('type', 'UNKNOWN')

                condition = BacktestCondition(
                    backtest_id=backtest_id,
                    condition_type="SELL",
                    factor=factor,
                    operator=sell_condition.get('operator', '='),
                    value=Decimal(str(sell_condition.get('value', 0))),
                    description=sell_condition.get('description', '')
                )
                self.db.add(condition)

            # 3. 통계 저장
            stats = result.statistics
            statistics = BacktestStatistics(
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
