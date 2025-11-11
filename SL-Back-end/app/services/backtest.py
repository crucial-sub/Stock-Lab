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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import hashlib
import json

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

        # 매도 조건 저장
        self.target_and_loss = None
        if target_and_loss:
            self.target_and_loss = {
                "target_gain": Decimal(str(target_and_loss.get('target_gain'))) if target_and_loss.get('target_gain') is not None else None,
                "stop_loss": Decimal(str(target_and_loss.get('stop_loss'))) if target_and_loss.get('stop_loss') is not None else None
            }

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

        try:
            # 1. 데이터 준비
            logger.info(f"백테스트 시작: {backtest_id}")
            logger.info(f"매매 대상 필터 - 테마: {self.target_themes}, 종목: {self.target_stocks}")

            price_data = await self._load_price_data(start_date, end_date, target_themes, target_stocks)
            financial_data = await self._load_financial_data(start_date, end_date)

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

            # SimpleCondition 객체 리스트 생성 (최적화된 팩터 계산을 위해)
            # BacktestCondition 스키마 대신 간단한 객체 사용
            class SimpleCondition:
                def __init__(self, exp_left_side, inequality, exp_right_side):
                    self.exp_left_side = exp_left_side
                    self.inequality = inequality
                    self.exp_right_side = exp_right_side

            backtest_conditions = []
            if isinstance(buy_conditions, list):
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
        target_stocks: List[str] = None
    ) -> pd.DataFrame:
        """가격 데이터 로드 (매매 대상 필터 적용)"""

        logger.info(f"📊 가격 데이터 로드 - target_themes: {target_themes}, target_stocks: {target_stocks}")

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
        if target_themes or target_stocks:
            filter_conditions = []

            if target_themes:
                # 선택된 산업(테마)에 속한 종목만
                filter_conditions.append(Company.industry.in_(target_themes))

            if target_stocks:
                # 선택된 개별 종목만
                filter_conditions.append(Company.stock_code.in_(target_stocks))

            # OR 조건으로 결합 (테마 또는 개별 종목)
            if len(filter_conditions) > 1:
                conditions.append(or_(*filter_conditions))
            elif len(filter_conditions) == 1:
                conditions.append(filter_conditions[0])

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

        logger.info(f"Loaded {len(df)} price records for {df['stock_code'].nunique()} stocks")

        return df

    async def _load_financial_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """재무 데이터 로드"""

        # 재무제표 기간 설정 (분기별 데이터 고려)
        extended_start = start_date - timedelta(days=180)  # 6개월 전 데이터부터

        # 손익계산서 데이터
        # Note: report_date 컬럼이 DB에 없으므로 bsns_year로 필터링
        start_year = str(start_date.year - 1)  # 1년 전 데이터부터
        end_year = str(end_date.year)

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

    def _extract_required_factors(self, buy_conditions: List[Any], priority_factor: Optional[str]) -> Set[str]:
        """매수 조건에서 필요한 팩터만 추출"""
        required_factors = set()

        logger.info(f"팩터 추출 시작 - buy_conditions 타입: {type(buy_conditions)}, 개수: {len(buy_conditions) if buy_conditions else 0}")

        # 매수 조건에서 팩터 추출
        if buy_conditions:
            for idx, condition in enumerate(buy_conditions):
                logger.info(f"조건 {idx+1}: 타입={type(condition)}, 내용={condition}")

                # 딕셔너리 또는 객체 둘 다 지원
                if isinstance(condition, dict):
                    exp_left = condition.get('exp_left_side', '')
                    exp_right = condition.get('exp_right_side', '')
                else:
                    exp_left = getattr(condition, 'exp_left_side', '')
                    exp_right = getattr(condition, 'exp_right_side', '')

                logger.info(f"  exp_left: '{exp_left}', exp_right: '{exp_right}'")

                # 왼쪽 표현식에서 팩터 추출 (예: "기본값({PER})" -> "PER", "기본값({pbr})" -> "PBR")
                left_match = re.findall(r'\{([^}]+)\}', exp_left)
                logger.info(f"  left_match: {left_match}")

                for match in left_match:
                    # 괄호 안의 영문 코드 추출
                    code_match = re.search(r'\(([A-Z_]+)\)', match)
                    if code_match:
                        factor_code = code_match.group(1)
                        required_factors.add(factor_code)
                        logger.info(f"  추출된 팩터 (괄호): {factor_code}")
                    else:
                        # 소문자를 대문자로 변환
                        factor_code = match.strip().upper()
                        required_factors.add(factor_code)
                        logger.info(f"  추출된 팩터 (직접): {factor_code}")

                # 오른쪽 표현식이 문자열인 경우에도 팩터 추출
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

        logger.info("최적화된 팩터 계산 시작")
        logger.info(f"받은 buy_conditions: {buy_conditions}, 타입: {type(buy_conditions)}, 길이: {len(buy_conditions) if buy_conditions else 0}")
        logger.info(f"받은 priority_factor: {priority_factor}")

        if price_data.empty:
            logger.warning("No price data available for factor calculation")
            return pd.DataFrame()

        # 1. 필요한 팩터만 추출
        required_factors = self._extract_required_factors(buy_conditions or [], priority_factor)
        if not required_factors:
            logger.info("모든 팩터 계산 (조건 없음)")
            required_factors = {'PER', 'PBR', 'ROE', 'ROA', 'MOMENTUM_1M', 'MOMENTUM_3M',
                              'MOMENTUM_6M', 'MOMENTUM_12M', 'VOLATILITY_20D', 'VOLATILITY_60D',
                              'VOLUME_RATIO_20D', 'TURNOVER_RATE_20D'}

        # Polars DataFrame으로 변환
        price_pl = pl.from_pandas(price_data)
        financial_pl = pl.from_pandas(financial_data) if not financial_data.empty else None

        unique_dates = sorted(price_data[price_data['date'] >= pd.Timestamp(start_date)]['date'].unique())
        total_dates = len(unique_dates)
        logger.info(f"팩터 계산 대상: {total_dates}개 거래일, 필요 팩터: {len(required_factors)}개")

        start_time = time.time()

        # 2. Redis 캐시 초기화
        try:
            await cache.initialize()
            cache_enabled = True
        except Exception as e:
            logger.warning(f"Redis 캐시 비활성화: {e}")
            cache_enabled = False

        # 3. 병렬 처리를 위한 날짜 그룹 생성
        chunk_size = max(1, total_dates // 10)  # 10개 청크로 분할
        date_chunks = [unique_dates[i:i+chunk_size] for i in range(0, total_dates, chunk_size)]

        async def calculate_date_chunk(dates_chunk, chunk_idx):
            """날짜 청크별 팩터 계산"""
            chunk_rows = []

            for date_idx, calc_date in enumerate(dates_chunk):
                # 캐시 키 생성
                cache_key = None
                if cache_enabled:
                    cache_params = {
                        'date': str(calc_date),
                        'factors': sorted(list(required_factors)),
                        'stocks': sorted(price_data['stock_code'].unique().tolist())
                    }
                    cache_key = cache._generate_key('backtest_factors', cache_params)

                    # 캐시 조회 (에러 발생 시 무시하고 계속 진행)
                    try:
                        cached_data = await cache.get(cache_key)
                        if cached_data:
                            chunk_rows.extend(cached_data)
                            continue
                    except Exception as e:
                        logger.warning(f"캐시 조회 실패 (계산으로 대체): {e}")
                        pass

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

                # 2. 선택적 팩터 계산
                if financial_pl is not None:
                    # 가치 팩터 (PER, PBR)
                    if any(f in required_factors for f in ['PER', 'PBR']):
                        try:
                            logger.info(f"🎯 가치 팩터 계산 시작 - required_factors: {required_factors}")
                            value_map = self._calculate_value_factors(price_until_date, financial_pl, calc_date)
                            # 필요한 팩터만 필터링
                            filtered_value_map = {}
                            for stock, factors in value_map.items():
                                filtered_value_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                            self._merge_factor_maps(stock_factor_map, filtered_value_map)
                        except Exception as e:
                            logger.error(f"가치 팩터 계산 에러 ({calc_date}): {e}")

                    # 수익성 팩터 (ROE, ROA)
                    if any(f in required_factors for f in ['ROE', 'ROA']):
                        try:
                            profit_map = self._calculate_profitability_factors(financial_pl, calc_date)
                            filtered_profit_map = {}
                            for stock, factors in profit_map.items():
                                filtered_profit_map[stock] = {k: v for k, v in factors.items() if k in required_factors}
                            self._merge_factor_maps(stock_factor_map, filtered_profit_map)
                        except Exception as e:
                            logger.error(f"수익성 팩터 계산 에러 ({calc_date}): {e}")

                    # 성장성 팩터
                    if any(f in required_factors for f in ['SALES_GROWTH', 'EARNINGS_GROWTH']):
                        try:
                            growth_map = self._calculate_growth_factors(financial_pl, calc_date)
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

                # 캐시 저장 (에러 발생 시 무시하고 계속 진행)
                if cache_enabled and cache_key and date_rows:
                    try:
                        await cache.set(cache_key, date_rows, ttl=3600)  # 1시간 캐싱
                    except Exception as e:
                        logger.warning(f"캐시 저장 실패 (무시): {e}")
                        pass

                chunk_rows.extend(date_rows)

            # 진행상황 로깅
            progress = (chunk_idx + 1) * 100 // len(date_chunks)
            elapsed = time.time() - start_time
            logger.info(f"청크 {chunk_idx + 1}/{len(date_chunks)} 완료 ({progress}%) - 경과: {elapsed:.1f}초")

            return chunk_rows

        # 4. 병렬 처리 실행
        all_rows = []
        tasks = []
        for idx, chunk in enumerate(date_chunks):
            task = calculate_date_chunk(chunk, idx)
            tasks.append(task)

        # 모든 태스크 실행 및 결과 수집
        results = await asyncio.gather(*tasks)
        for chunk_result in results:
            all_rows.extend(chunk_result)

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

    def _calculate_value_factors(self, price_pl: pl.DataFrame, financial_pl: pl.DataFrame, calc_date) -> Dict[str, Dict[str, float]]:
        """가치 팩터 계산"""
        logger.info(f"🎯 _calculate_value_factors 호출됨! calc_date={calc_date}")
        factors: Dict[str, Dict[str, float]] = {}
        latest_price = price_pl.filter(pl.col('date') == calc_date)
        latest_financial = financial_pl.filter(pl.col('report_date') <= calc_date)
        logger.info(f"🎯 latest_price 건수: {len(latest_price)}, latest_financial 건수: {len(latest_financial)}")

        if latest_price.is_empty() or latest_financial.is_empty():
            logger.debug(f"가치 팩터 계산 건너뜀 - price empty: {latest_price.is_empty()}, financial empty: {latest_financial.is_empty()}")
            return factors

        for stock in latest_price.select('stock_code').unique().to_pandas()['stock_code']:
            stock_price = latest_price.filter(pl.col('stock_code') == stock)
            stock_financial = latest_financial.filter(pl.col('stock_code') == stock)

            if stock_financial.is_empty():
                continue

            # 최신 재무 데이터 선택 (PBR용 - 최신 분기 포함)
            stock_financial_latest = stock_financial.sort('report_date', descending=True).head(1)

            # PER 계산을 위해 당기순이익이 있는 연간 보고서 우선 선택
            # report_code='11011'은 연간보고서
            annual_reports = stock_financial.filter(pl.col('report_code') == '11011')
            if not annual_reports.is_empty():
                stock_financial_annual = annual_reports.sort('report_date', descending=True).head(1)
            else:
                stock_financial_annual = None

            entry = factors.setdefault(stock, {})

            # NaN 체크를 위해 pandas의 isna() 사용
            import pandas as pd

            # 당기순이익: 연간 보고서에서 가져오기 (없으면 None)
            if stock_financial_annual is not None:
                net_income_raw = stock_financial_annual.select('당기순이익').to_pandas().iloc[0, 0] if '당기순이익' in stock_financial_annual.columns else None
            else:
                net_income_raw = None

            # 자본총계: 최신 데이터 사용
            equity_raw = stock_financial_latest.select('자본총계').to_pandas().iloc[0, 0] if '자본총계' in stock_financial_latest.columns else None
            market_cap_raw = stock_price.select('market_cap').to_pandas().iloc[0, 0] if 'market_cap' in stock_price.columns else None

            # NaN을 None으로 변환
            net_income = None if net_income_raw is None or pd.isna(net_income_raw) else net_income_raw
            equity = None if equity_raw is None or pd.isna(equity_raw) else equity_raw
            market_cap = None if market_cap_raw is None or pd.isna(market_cap_raw) else market_cap_raw

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
        total_days = len([d for d in trading_days if pd.Timestamp(start_date) <= d <= pd.Timestamp(end_date)])
        current_day_index = 0

        # MDD 추적 변수
        peak_value = float(initial_capital)
        current_mdd = 0.0

        for trading_day in trading_days:
            if trading_day < pd.Timestamp(start_date) or trading_day > pd.Timestamp(end_date):
                continue

            current_day_index += 1
            daily_new_positions = 0
            daily_buy_count = 0  # 당일 매수 횟수
            daily_sell_count = 0  # 당일 매도 횟수

            # 매도 신호 확인 및 실행 (매일 체크)
            sell_trades = await self._execute_sells(
                holdings, factor_data, sell_conditions,
                condition_sell,
                price_data, trading_day, cash_balance,
                orders, executions
            )
            daily_sell_count = len(sell_trades)  # 당일 매도 횟수 기록

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
                # 1단계: 리밸런싱 - 조건 불만족 종목 매도
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

                    # 조건 불만족 종목 매도
                    stocks_to_sell = [stock for stock in holding_stocks if stock not in valid_holdings]
                    for stock_code in stocks_to_sell:
                        holding = holdings.get(stock_code)
                        if not holding:
                            continue

                        # 현재가 조회
                        current_price_data = price_data[
                            (price_data['stock_code'] == stock_code) &
                            (price_data['date'] == trading_day)
                        ]
                        if current_price_data.empty:
                            continue

                        current_price = Decimal(str(current_price_data.iloc[0]['close_price']))
                        execution_price = current_price * (1 - self.slippage)

                        amount = execution_price * holding.quantity
                        commission = amount * self.commission_rate
                        tax = amount * self.tax_rate

                        logger.info(f"🔄 리밸런싱 매도: {stock_code} (조건 불만족)")

                        # 매도 실행
                        sell_trade = {
                            'stock_code': stock_code,
                            'price': execution_price,
                            'quantity': holding.quantity,
                            'amount': amount,
                            'commission': commission,
                            'tax': tax
                        }

                        cash_balance += amount - commission - tax
                        holding.is_open = False
                        holding.exit_date = trading_day
                        holding.exit_price = execution_price
                        holding.realized_pnl = (execution_price - holding.entry_price) * holding.quantity
                        self.closed_positions.append(holding)
                        del holdings[stock_code]

                # 2단계: 매수 종목 선정
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

                # 이미 보유 중인 종목은 매수 후보에서 제외 (리밸런싱에서는 유지)
                new_buy_candidates = [s for s in buy_candidates if s not in holdings]

                logger.info(f"💰 매수 후보(전체): {len(buy_candidates)}개 - {buy_candidates[:10]}")
                logger.info(f"💰 매수 후보(신규): {len(new_buy_candidates)}개 - {new_buy_candidates[:10]}")
                logger.info(f"💼 현재 보유: {len(holdings)}개, 최대 포지션: {max_positions}, 여유: {max_positions - len(holdings)}")

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

            # 실시간 진행 상황 업데이트 (매 10일마다 또는 5% 진행마다)
            progress_percentage = int((current_day_index / total_days) * 100)
            should_update = (
                current_day_index % 10 == 0 or  # 10일마다
                progress_percentage % 5 == 0  # 5%마다
            )

            if should_update:
                # 현재 수익률 계산
                current_return = ((portfolio_value - initial_capital) / initial_capital) * 100

                # MDD 계산
                portfolio_value_float = float(portfolio_value)
                if portfolio_value_float > peak_value:
                    peak_value = portfolio_value_float
                drawdown = ((portfolio_value_float - peak_value) / peak_value) * 100
                if drawdown < current_mdd:
                    current_mdd = drawdown
                # SimulationSession 업데이트
                from sqlalchemy import update
                from app.models.simulation import SimulationSession

                stmt = (
                    update(SimulationSession)
                    .where(SimulationSession.session_id == str(backtest_id))
                    .values(
                        progress=progress_percentage,
                        current_date=trading_day.date(),
                        buy_count=daily_buy_count,  # 당일 매수 횟수
                        sell_count=daily_sell_count,  # 당일 매도 횟수
                        current_return=float(current_return),
                        current_capital=float(portfolio_value),
                        current_mdd=float(current_mdd)
                    )
                )
                await self.db.execute(stmt)
                await self.db.commit()

                logger.info(f"📊 실시간 진행 상황 업데이트: {progress_percentage}% | 날짜: {trading_day.date()} | 매수: {daily_buy_count} | 매도: {daily_sell_count} | 수익률: {current_return:.2f}% | MDD: {current_mdd:.2f}%")

        # 백테스트 종료 시 모든 보유 종목 강제 매도
        if holdings:
            last_trading_day = trading_days[-1]
            logger.info(f"🏁 백테스트 종료: {len(holdings)}개 보유 종목 강제 매도")

            for stock_code, holding in list(holdings.items()):
                # 마지막 거래일 가격 조회
                current_price_data = price_data[
                    (price_data['stock_code'] == stock_code) &
                    (price_data['date'] == last_trading_day)
                ]

                if current_price_data.empty:
                    logger.warning(f"⚠️ {stock_code}: 마지막 거래일 가격 없음, 평균 매수가로 매도")
                    current_price = holding.entry_price
                else:
                    current_price = Decimal(str(current_price_data.iloc[0]['close_price']))

                execution_price = current_price * (1 - self.slippage)
                amount = execution_price * holding.quantity
                commission = amount * self.commission_rate
                tax = amount * self.tax_rate

                logger.info(f"  🔚 강제 매도: {stock_code} {holding.quantity}주 @ {execution_price:,.0f}원")

                # 매도 거래 기록
                cash_balance += amount - commission - tax
                holding.is_open = False
                holding.exit_date = last_trading_day
                holding.exit_price = execution_price
                holding.realized_pnl = (execution_price - holding.entry_price) * holding.quantity
                self.closed_positions.append(holding)

                # 체결 기록 추가
                executions.append({
                    'execution_id': len(executions) + 1,
                    'execution_date': last_trading_day,
                    'stock_code': stock_code,
                    'side': 'SELL',
                    'quantity': holding.quantity,
                    'price': execution_price,
                    'amount': amount,
                    'commission': commission,
                    'tax': tax,
                    'reason': 'BACKTEST_END'
                })
                orders.append({
                    'order_id': f"ORD-S-{stock_code}-{last_trading_day}-FORCE",
                    'order_date': last_trading_day,
                    'stock_code': stock_code,
                    'stock_name': holding.stock_name,
                    'side': 'SELL',
                    'order_type': 'MARKET',
                    'quantity': holding.quantity,
                    'status': 'FILLED',
                    'reason': 'BACKTEST_END'
                })

            # holdings 비우기
            holdings.clear()

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

        target_cfg = self.target_and_loss or {}
        hold_cfg = self.hold_days or {}
        condition_sell_meta = self.condition_sell_meta

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
            sell_reason_key = None

            hold_days_count = (trading_day - holding.entry_date).days
            min_hold = hold_cfg.get('min_hold_days') if hold_cfg else None
            max_hold = hold_cfg.get('max_hold_days') if hold_cfg else None
            enforce_min_hold = min_hold is not None and hold_days_count < min_hold

            if max_hold and hold_days_count >= max_hold:
                should_sell = True
                sell_reason = f"Max hold days reached ({hold_days_count}d)"
                sell_reason_key = "hold"

            if not should_sell and target_cfg:
                profit_rate = ((current_price / holding.entry_price) - Decimal("1")) * Decimal("100")
                target_gain = target_cfg.get('target_gain')
                stop_loss = target_cfg.get('stop_loss')

                if target_gain is not None and profit_rate >= target_gain:
                    should_sell = True
                    sell_reason = f"Take profit {profit_rate:.2f}%"
                    sell_reason_key = "target"

                if not should_sell and stop_loss is not None and profit_rate <= -stop_loss:
                    should_sell = True
                    sell_reason = f"Stop loss {profit_rate:.2f}%"
                    sell_reason_key = "stop"

            if not should_sell and not enforce_min_hold:
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
                # 매도 실행
                quantity = holding.quantity

                # 슬리피지 적용 (매도 시 불리하게 - 가격 하락)
                execution_price = current_price * (1 - self.slippage)
                price_meta = None
                if sell_reason_key == "condition":
                    price_meta = condition_sell_meta
                elif sell_reason_key == "hold":
                    price_meta = hold_cfg
                execution_price = self._apply_price_adjustment(execution_price, price_meta)

                amount = execution_price * quantity
                commission = amount * self.commission_rate
                tax = amount * self.tax_rate

                profit = (execution_price - holding.entry_price) * quantity
                profit_rate = ((execution_price / holding.entry_price) - 1) * 100

                order = {
                    'order_id': f"ORD-S-{stock_code}-{trading_day}",
                    'order_date': trading_day,
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
                    'execution_id': f"EXE-S-{stock_code}-{trading_day}",
                    'order_id': order['order_id'],
                    'execution_date': trading_day,
                    'trade_date': trading_day,
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

        # 리밸런싱 시에는 보유 종목도 재평가해야 하므로 제외하지 않음
        # (기존 로직: tradeable_stocks = [s for s in tradeable_stocks if s not in holdings])
        # 포지션 사이징에서 available_slots로 신규 매수 수량 제한

        # 통합 모듈로 매수 조건 평가 (54개 팩터 사용)
        logger.info(f"🔍 조건 평가 시작 - 거래 가능 종목: {len(tradeable_stocks)}개, 조건 타입: {type(buy_conditions)}")
        logger.info(f"🔍 buy_conditions 내용: {buy_conditions}")

        selected_stocks = factor_integrator.evaluate_buy_conditions_with_factors(
            factor_data=factor_data,
            stock_codes=tradeable_stocks,
            buy_conditions=buy_conditions,
            trading_date=trading_ts
        )

        logger.info(f"🔍 조건 평가 완료 - 조건 만족 종목: {len(selected_stocks)}개 - {selected_stocks[:10]}")

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
        meta: Optional[Dict[str, Any]]
    ) -> Decimal:
        """매도가격 오프셋 적용"""
        if not meta:
            return price
        offset_pct = meta.get('sell_price_offset')
        if offset_pct is None:
            return price
        offset_value = offset_pct if isinstance(offset_pct, Decimal) else Decimal(str(offset_pct))
        return price * (Decimal("1") + (offset_value / Decimal("100")))

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

            current_price = Decimal(str(current_price_data.iloc[0]['close_price']))
            stock_name = current_price_data.iloc[0].get('stock_name', f"Stock_{stock_code}")

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

            # 매수 실행
            order = {
                'order_id': f"ORD-B-{stock_code}-{trading_day}",
                'order_date': trading_day,
                'stock_code': stock_code,
                'stock_name': stock_name,
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
                    stock_name=stock_name,
                    entry_date=trading_day,
                    entry_price=execution_price,
                    quantity=quantity,
                    current_price=execution_price,
                    current_value=execution_price * quantity
                )
                new_position_count += 1

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

            # 3. 통계 저장
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
