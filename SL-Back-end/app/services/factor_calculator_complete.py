"""
완전한 팩터 계산 모듈 V2 - 현재 스키마에 맞게 재구현
54개 팩터 완전 구현
"""
from typing import Dict, List, Optional
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
import logging

from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.models.income_statement import IncomeStatement
from app.models.balance_sheet import BalanceSheet
from app.models.cashflow_statement import CashflowStatement

logger = logging.getLogger(__name__)


class CompleteFactorCalculator:
    """
    54개 팩터 완전 구현 V2
    현재 데이터베이스 스키마에 맞게 재설계

    팩터 분류:
    - 가치 팩터 (5개): PER, PBR, ROE, ROA, DEBT_RATIO
    - 거래량 팩터 (2개): AVG_TRADING_VALUE, TURNOVER_RATE
    - 모멘텀 팩터 (2개): MOM_3M, VOLATILITY_90
    - 수익성 팩터 (10개): GPM, OPM, NPM, ROIC, ASSET_TURNOVER, etc.
    - 성장성 팩터 (8개): REVENUE_GROWTH, EARNINGS_GROWTH, etc.
    - 안정성 팩터 (8개): CURRENT_RATIO, QUICK_RATIO, INTEREST_COVERAGE, etc.
    - 모멘텀 추가 (8개): 1M/3M/6M/12M 모멘텀, 52주 고저점 거리, etc.
    - 기술적 팩터 (6개): RSI, BOLLINGER, STOCHASTIC, etc.
    - 품질 팩터 (5개): Quality Score, Accruals Ratio, Earnings Quality, etc.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_all_factors(
        self,
        stock_codes: List[str],
        date: datetime,
        include_advanced: bool = True
    ) -> pd.DataFrame:
        """
        모든 팩터 계산

        Args:
            stock_codes: 종목 코드 리스트
            date: 기준 날짜
            include_advanced: 고급 팩터 포함 여부 (기본값: True)

        Returns:
            모든 팩터가 계산된 DataFrame
        """
        # 1. 기본 팩터 계산 (9개)
        price_df = await self._fetch_price_history(stock_codes, date)
        if price_df.empty:
            logger.warning("가격 데이터가 없어 팩터 계산을 건너뜁니다")
            return pd.DataFrame()

        financial_df = await self._fetch_financial_snapshot(stock_codes, date)
        factor_df = self._build_basic_factors(price_df, financial_df, date)

        if factor_df.empty:
            return factor_df

        if not include_advanced:
            return self._attach_ranks(factor_df)

        # 2. 고급 팩터 계산 (45개)
        try:
            # 수익성 팩터 (추가 6개)
            profitability_df = await self._calculate_profitability_factors(stock_codes, date, financial_df)
            if not profitability_df.empty:
                factor_df = factor_df.merge(profitability_df, on='stock_code', how='left')

            # 성장성 팩터 (8개)
            growth_df = await self._calculate_growth_factors(stock_codes, date)
            if not growth_df.empty:
                factor_df = factor_df.merge(growth_df, on='stock_code', how='left')

            # 모멘텀 팩터 (추가 7개)
            momentum_df = await self._calculate_advanced_momentum(stock_codes, date, price_df)
            if not momentum_df.empty:
                factor_df = factor_df.merge(momentum_df, on='stock_code', how='left')

            # 안정성 팩터 (8개)
            stability_df = await self._calculate_stability_factors(stock_codes, date, financial_df)
            if not stability_df.empty:
                factor_df = factor_df.merge(stability_df, on='stock_code', how='left')

            # 기술적 팩터 (6개)
            technical_df = await self._calculate_technical_factors(stock_codes, date, price_df)
            if not technical_df.empty:
                factor_df = factor_df.merge(technical_df, on='stock_code', how='left')

            # 품질 팩터 (5개)
            quality_df = await self._calculate_quality_factors(stock_codes, date, financial_df)
            if not quality_df.empty:
                factor_df = factor_df.merge(quality_df, on='stock_code', how='left')

            # PEG 계산: PER / EARNINGS_GROWTH_1Y (성장률이 양수일 때만 유효)
            # PEG = 주가수익비율 / 순이익성장률
            if 'PER' in factor_df.columns and 'EARNINGS_GROWTH_1Y' in factor_df.columns:
                def calc_peg(row):
                    per = row.get('PER')
                    growth = row.get('EARNINGS_GROWTH_1Y')
                    # PER이 양수이고 성장률이 양수일 때만 PEG 계산
                    if pd.notnull(per) and pd.notnull(growth) and growth > 0 and per > 0:
                        return per / growth
                    return None
                factor_df['PEG'] = factor_df.apply(calc_peg, axis=1)
                logger.info(f"PEG 팩터 계산 완료: {factor_df['PEG'].notna().sum()}개 종목")

        except Exception as e:
            logger.error(f"고급 팩터 계산 중 에러: {e}")
            logger.exception(e)

        # 3. 랭킹 계산
        factor_df = self._attach_ranks(factor_df)

        return factor_df

    async def _fetch_price_history(
        self,
        stock_codes: Optional[List[str]],
        as_of: datetime
    ) -> pd.DataFrame:
        """주가 데이터 조회"""
        start_window = as_of - timedelta(days=400)

        query = (
            select(
                Company.stock_code,
                Company.company_name.label('stock_name'),
                Company.industry,
                StockPrice.trade_date,
                StockPrice.close_price,
                StockPrice.high_price,
                StockPrice.low_price,
                StockPrice.open_price,
                StockPrice.market_cap,
                StockPrice.trading_value,
                StockPrice.volume,
                StockPrice.listed_shares
            )
            .join(Company, StockPrice.company_id == Company.company_id)
            .where(
                and_(
                    StockPrice.trade_date >= start_window.date(),
                    StockPrice.trade_date <= as_of.date()
                )
            )
            .order_by(StockPrice.trade_date)
        )

        if stock_codes:
            query = query.where(Company.stock_code.in_(stock_codes))

        result = await self.db.execute(query)
        rows = result.mappings().all()
        df = pd.DataFrame(rows)
        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df

    async def _fetch_financial_snapshot(
        self,
        stock_codes: Optional[List[str]],
        as_of: datetime
    ) -> pd.DataFrame:
        """재무제표 데이터 조회"""
        start_year = str(as_of.year - 2)  # 3년치 데이터
        end_year = str(as_of.year)

        base_filters = [
            FinancialStatement.bsns_year >= start_year,
            FinancialStatement.bsns_year <= end_year
        ]

        if stock_codes:
            base_filters.append(Company.stock_code.in_(stock_codes))

        # 손익계산서 계정 과목
        income_accounts = [
            '당기순이익', '당기순이익(손실)',  # 2023년에는 "당기순이익(손실)" 사용
            '영업이익', '매출액', '매출원가', '매출총이익',  # 2023은 매출총이익 사용
            '영업비용', '법인세비용', '이자비용'
        ]

        # 재무상태표 계정 과목
        balance_accounts = [
            '자산총계', '자본총계', '부채총계',
            '유동자산', '비유동자산', '유동부채', '비유동부채',
            '재고자산', '매출채권', '현금및현금성자산'
        ]

        # 현금흐름표 계정 과목 (패턴 매칭)
        # - 영업활동현금흐름은 다양한 표기가 있음: "영업활동현금흐름", "영업활동으로 인한 현금흐름" 등

        # 손익계산서 데이터
        income_query = select(
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            IncomeStatement.account_nm,
            IncomeStatement.thstrm_amount.label('current_amount'),
            IncomeStatement.frmtrm_amount.label('previous_amount')
        ).join(
            IncomeStatement, FinancialStatement.stmt_id == IncomeStatement.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(*base_filters, IncomeStatement.account_nm.in_(income_accounts))
        )

        # 재무상태표 데이터
        balance_query = select(
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            BalanceSheet.account_nm,
            BalanceSheet.thstrm_amount.label('current_amount'),
            BalanceSheet.frmtrm_amount.label('previous_amount')
        ).join(
            BalanceSheet, FinancialStatement.stmt_id == BalanceSheet.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(*base_filters, BalanceSheet.account_nm.in_(balance_accounts))
        )

        # 현금흐름표 데이터 (영업활동현금흐름 찾기)
        cashflow_query = select(
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            CashflowStatement.account_nm,
            CashflowStatement.thstrm_amount.label('current_amount')
        ).join(
            CashflowStatement, FinancialStatement.stmt_id == CashflowStatement.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(
                *base_filters,
                CashflowStatement.account_nm.like('%영업활동%현금%')
            )
        )

        income_df = pd.DataFrame((await self.db.execute(income_query)).mappings().all())
        balance_df = pd.DataFrame((await self.db.execute(balance_query)).mappings().all())
        cashflow_df = pd.DataFrame((await self.db.execute(cashflow_query)).mappings().all())

        if income_df.empty and balance_df.empty and cashflow_df.empty:
            return pd.DataFrame()

        # 계정 과목 정규화 (연도별 차이 해결)
        if not income_df.empty:
            income_df['account_nm'] = income_df['account_nm'].str.replace('당기순이익(손실)', '당기순이익', regex=False)

        def _pivot(df: pd.DataFrame) -> pd.DataFrame:
            if df.empty:
                return pd.DataFrame()
            pivoted = df.pivot_table(
                index=['stock_code', 'fiscal_year', 'report_code'],
                columns='account_nm',
                values='current_amount',
                aggfunc='first'
            ).reset_index()
            numeric_cols = [col for col in pivoted.columns if col not in ('stock_code', 'fiscal_year', 'report_code')]
            pivoted[numeric_cols] = pivoted[numeric_cols].apply(pd.to_numeric, errors='coerce')
            return pivoted

        income_pivot = _pivot(income_df)
        balance_pivot = _pivot(balance_df)

        # 현금흐름표 피벗 (영업활동현금흐름만 추출)
        cashflow_pivot = pd.DataFrame()
        if not cashflow_df.empty:
            # 영업활동현금흐름 값 추출 (다양한 표기 중 첫 번째 값 사용)
            cashflow_grouped = cashflow_df.groupby(['stock_code', 'fiscal_year', 'report_code']).agg({
                'current_amount': 'first'  # 첫 번째 매칭되는 값 사용
            }).reset_index()
            cashflow_grouped.rename(columns={'current_amount': '영업활동현금흐름'}, inplace=True)
            cashflow_pivot = cashflow_grouped

        # merge income and balance
        if income_pivot.empty:
            merged = balance_pivot
        elif balance_pivot.empty:
            merged = income_pivot
        else:
            merged = pd.merge(
                income_pivot,
                balance_pivot,
                on=['stock_code', 'fiscal_year', 'report_code'],
                how='outer'
            )

        # merge cashflow
        if not cashflow_pivot.empty and not merged.empty:
            merged = pd.merge(
                merged,
                cashflow_pivot,
                on=['stock_code', 'fiscal_year', 'report_code'],
                how='left'
            )

        if merged.empty:
            return merged

        # 최신 데이터만 선택 (각 종목별로 가장 최근 보고서)
        def _report_date(row):
            year = int(row['fiscal_year'])
            code = row['report_code']
            if code == '11011':  # 사업보고서
                return datetime(year, 12, 31)
            if code == '11012':  # 반기보고서
                return datetime(year, 6, 30)
            if code == '11013':  # 1분기보고서
                return datetime(year, 3, 31)
            if code == '11014':  # 3분기보고서
                return datetime(year, 9, 30)
            return datetime(year, 12, 31)

        merged['report_date'] = merged.apply(_report_date, axis=1)

        # 매출액 계산 (2023년처럼 직접 제공되지 않는 경우)
        # Revenue = Cost of Goods Sold + Gross Profit
        if '매출액' in merged.columns and '매출원가' in merged.columns and '매출총이익' in merged.columns:
            merged['매출액'] = merged.apply(
                lambda row: row['매출원가'] + row['매출총이익']
                if pd.isna(row.get('매출액')) and pd.notna(row.get('매출원가')) and pd.notna(row.get('매출총이익'))
                else row.get('매출액'),
                axis=1
            )

        # 성장률 계산을 위해 연간 보고서(11011)를 우선적으로 사용
        # 연간 보고서가 가장 완전한 데이터를 포함
        annual_only = merged[merged['report_code'] == '11011'].copy()

        # 연간 보고서가 있으면 그것만 사용, 없으면 전체 사용
        if not annual_only.empty and len(annual_only) >= 2:
            merged = annual_only

        # 각 종목별로 최신 데이터와 이전 연도 데이터 모두 유지 (성장률 계산용)
        merged = merged.sort_values(['stock_code', 'report_date'], ascending=[True, False])

        return merged

    def _build_basic_factors(
        self,
        price_df: pd.DataFrame,
        financial_df: pd.DataFrame,
        snapshot_date: datetime
    ) -> pd.DataFrame:
        """기본 팩터 계산 (9개)"""
        if price_df.empty:
            return pd.DataFrame()

        latest_prices = price_df[price_df['trade_date'] == pd.Timestamp(snapshot_date.date())].copy()
        if latest_prices.empty:
            logger.warning(f"스냅샷 날짜({snapshot_date.date()})에 해당하는 가격이 없습니다.")
            return pd.DataFrame()

        # 최신 재무 데이터만 선택
        if not financial_df.empty:
            latest_financial = financial_df.sort_values('report_date', ascending=False).drop_duplicates(subset=['stock_code'])
            merged = latest_prices.merge(latest_financial, on='stock_code', how='left', suffixes=('', '_fin'))
        else:
            merged = latest_prices.copy()

        def _safe_ratio(numerator, denominator):
            if numerator is None or denominator is None:
                return None
            if pd.isna(numerator) or pd.isna(denominator):
                return None
            if denominator == 0:
                return None
            return float(numerator) / float(denominator)

        # 기본 가치 팩터
        merged['PER'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('당기순이익')), axis=1)
        merged['PBR'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('자본총계')), axis=1)
        merged['ROE'] = merged.apply(lambda row: _safe_ratio(row.get('당기순이익'), row.get('자본총계')) * 100 if _safe_ratio(row.get('당기순이익'), row.get('자본총계')) is not None else None, axis=1)
        merged['ROA'] = merged.apply(lambda row: _safe_ratio(row.get('당기순이익'), row.get('자산총계')) * 100 if _safe_ratio(row.get('당기순이익'), row.get('자산총계')) is not None else None, axis=1)
        merged['DEBT_RATIO'] = merged.apply(lambda row: _safe_ratio(row.get('부채총계'), row.get('자본총계')) * 100 if _safe_ratio(row.get('부채총계'), row.get('자본총계')) is not None else None, axis=1)
        # PSR: Price to Sales Ratio = 시가총액 / 매출액
        merged['PSR'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('매출액')), axis=1)

        # Phase 3 가치 팩터
        # PCR: Price to Cashflow Ratio = 시가총액 / 영업활동현금흐름
        merged['PCR'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('영업활동현금흐름')), axis=1)
        # EARNINGS_YIELD: 이익수익률 = 1/PER = 당기순이익 / 시가총액 * 100
        merged['EARNINGS_YIELD'] = merged.apply(
            lambda row: _safe_ratio(row.get('당기순이익'), row['market_cap']) * 100
            if _safe_ratio(row.get('당기순이익'), row['market_cap']) is not None else None, axis=1
        )
        # BOOK_TO_MARKET: PBR의 역수 = 자본총계 / 시가총액
        merged['BOOK_TO_MARKET'] = merged.apply(lambda row: _safe_ratio(row.get('자본총계'), row['market_cap']), axis=1)
        # MARKET_CAP: 시가총액 (이미 있음)
        merged['MARKET_CAP'] = merged['market_cap']

        # EV 관련 팩터 (Enterprise Value = 시가총액 + 부채 - 현금)
        def _calc_ev_factors(row):
            market_cap = row.get('market_cap')
            total_debt = row.get('부채총계')
            cash = row.get('현금및현금성자산', 0)
            if market_cap is None or total_debt is None:
                return None, None
            ev = float(market_cap) + float(total_debt) - float(cash or 0)
            return ev, ev

        merged['EV_SALES'] = merged.apply(
            lambda row: _safe_ratio(_calc_ev_factors(row)[0], row.get('매출액'))
            if _calc_ev_factors(row)[0] is not None else None, axis=1
        )
        # EV_EBITDA: EV / EBITDA (EBITDA = 영업이익 + 감가상각비, 단순화: 영업이익으로 근사)
        merged['EV_EBITDA'] = merged.apply(
            lambda row: _safe_ratio(_calc_ev_factors(row)[0], row.get('영업이익'))
            if _calc_ev_factors(row)[0] is not None else None, axis=1
        )

        # 추가 가치 팩터 (5개)
        # PEG: PER / earnings_growth_1y ratio
        # 성장률 데이터는 growth_factors에서 계산되므로 여기서는 placeholder
        merged['PEG'] = None  # Will be calculated later with growth data

        # EV_FCF: Enterprise Value / Free Cash Flow
        merged['EV_FCF'] = merged.apply(
            lambda row: self._calculate_ev_fcf(row, _calc_ev_factors), axis=1
        )

        # DIVIDEND_YIELD: 배당수익률 = (주당배당금 / 현재가) * 100
        # 배당 데이터 없으므로 None
        merged['DIVIDEND_YIELD'] = None

        # CAPE_RATIO: Cyclically Adjusted PE (Shiller PE)
        # 10년 평균 EPS 대신 3년 평균으로 근사
        merged['CAPE_RATIO'] = None  # Will be calculated with multi-year data

        # PTBV: Price to Tangible Book Value = 시가총액 / (자본총계 - 무형자산)
        merged['PTBV'] = merged.apply(
            lambda row: self._calculate_ptbv(row), axis=1
        )

        # 거래량 팩터
        recent_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=20)]
        avg_trading = recent_window.groupby('stock_code')['trading_value'].mean()
        avg_trading.name = 'AVG_TRADING_VALUE'

        turnover = recent_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(g['volume'].mean(), g['listed_shares'].iloc[0]) * 100 if len(g) > 0 and g['listed_shares'].iloc[0] else None,
            include_groups=False
        )
        turnover.name = 'TURNOVER_RATE'

        # 모멘텀 팩터
        momentum_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=120)]
        momentum = momentum_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(
                g[g['trade_date'] == g['trade_date'].max()]['close_price'].iloc[0],
                g.sort_values('trade_date').iloc[0]['close_price']
            ) - 1 if not g.empty and len(g[g['trade_date'] == g['trade_date'].max()]) > 0 else None,
            include_groups=False
        )
        momentum.name = 'MOM_3M'

        # CHANGE_RATE: 일별 변화율 (전일 대비)
        latest_prices = price_df[price_df['trade_date'] == pd.Timestamp(snapshot_date.date())]
        prev_date = pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=1)
        previous_prices = price_df[price_df['trade_date'] <= prev_date].sort_values('trade_date').groupby('stock_code').tail(1)

        change_rate = latest_prices.merge(
            previous_prices[['stock_code', 'close_price']],
            on='stock_code',
            how='left',
            suffixes=('_curr', '_prev')
        )
        change_rate['CHANGE_RATE'] = change_rate.apply(
            lambda row: ((row['close_price_curr'] - row['close_price_prev']) / row['close_price_prev']) * 100
            if pd.notna(row.get('close_price_prev')) and row.get('close_price_prev', 0) > 0 else None,
            axis=1
        )
        change_rate_series = change_rate.set_index('stock_code')['CHANGE_RATE']

        # 변동성
        pct_returns = price_df.sort_values('trade_date').groupby('stock_code')['close_price'].pct_change()
        price_df = price_df.assign(daily_return=pct_returns)

        # Phase 3: Multiple volatility windows
        vol_window_20 = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=20)]
        volatility_20 = vol_window_20.groupby('stock_code')['daily_return'].std().rename('VOLATILITY_20D')

        vol_window_60 = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=60)]
        volatility_60 = vol_window_60.groupby('stock_code')['daily_return'].std().rename('VOLATILITY_60D')

        vol_window_90 = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=90)]
        volatility = vol_window_90.groupby('stock_code')['daily_return'].std().rename('VOLATILITY_90D')

        # merge
        merged = merged.merge(avg_trading, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(turnover, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(momentum, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(change_rate_series, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(volatility_20, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(volatility_60, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(volatility, left_on='stock_code', right_index=True, how='left')

        merged['date'] = snapshot_date
        return merged

    async def _calculate_profitability_factors(
        self,
        stock_codes: List[str],
        date: datetime,
        financial_df: pd.DataFrame
    ) -> pd.DataFrame:
        """수익성 팩터 계산 (추가 6개)"""
        if financial_df.empty:
            return pd.DataFrame()

        latest = financial_df.sort_values('report_date', ascending=False).drop_duplicates(subset=['stock_code'])

        def _safe_ratio(num, den):
            if num is None or den is None or pd.isna(num) or pd.isna(den) or den == 0:
                return None
            return float(num) / float(den)

        result = pd.DataFrame()
        result['stock_code'] = latest['stock_code']

        # GPM: 매출총이익률 = (매출액 - 매출원가) / 매출액 * 100
        result['GPM'] = latest.apply(
            lambda row: ((row.get('매출액', 0) - row.get('매출원가', 0)) / row.get('매출액', 1)) * 100
            if row.get('매출액', 0) > 0 else None, axis=1
        )

        # OPM: 영업이익률 = 영업이익 / 매출액 * 100
        result['OPM'] = latest.apply(
            lambda row: _safe_ratio(row.get('영업이익'), row.get('매출액')) * 100
            if _safe_ratio(row.get('영업이익'), row.get('매출액')) is not None else None, axis=1
        )

        # NPM: 순이익률 = 당기순이익 / 매출액 * 100
        result['NPM'] = latest.apply(
            lambda row: _safe_ratio(row.get('당기순이익'), row.get('매출액')) * 100
            if _safe_ratio(row.get('당기순이익'), row.get('매출액')) is not None else None, axis=1
        )

        # ASSET_TURNOVER: 자산회전율 = 매출액 / 자산총계
        result['ASSET_TURNOVER'] = latest.apply(
            lambda row: _safe_ratio(row.get('매출액'), row.get('자산총계')), axis=1
        )

        # EQUITY_MULTIPLIER: 자기자본승수 = 자산총계 / 자본총계
        result['EQUITY_MULTIPLIER'] = latest.apply(
            lambda row: _safe_ratio(row.get('자산총계'), row.get('자본총계')), axis=1
        )

        # OCF_RATIO: 영업현금흐름비율 = 영업활동현금흐름 / 매출액 * 100
        result['OCF_RATIO'] = latest.apply(
            lambda row: _safe_ratio(row.get('영업활동현금흐름'), row.get('매출액')) * 100
            if _safe_ratio(row.get('영업활동현금흐름'), row.get('매출액')) is not None else None, axis=1
        )

        # ROIC: Return on Invested Capital = (NOPAT / 투하자본) * 100
        # NOPAT = 영업이익 * (1 - 세율), 세율 = 법인세비용 / (당기순이익 + 법인세비용)
        # 투하자본 = 자본총계 + 유무이자부채 (간소화: 자본총계 + 부채총계)
        result['ROIC'] = latest.apply(
            lambda row: self._calculate_roic(row), axis=1
        )

        # INVENTORY_TURNOVER: 재고자산회전율 = 매출원가 / 평균재고자산
        # 평균재고자산이 없으므로 현재 재고자산으로 근사
        result['INVENTORY_TURNOVER'] = latest.apply(
            lambda row: _safe_ratio(row.get('매출원가'), row.get('재고자산')), axis=1
        )

        # === NEW: Valuation Factors (5개) ===

        # GRAHAM_NUMBER: Graham Number = sqrt(22.5 * EPS * BVPS)
        result['GRAHAM_NUMBER'] = latest.apply(
            lambda row: self._calculate_graham_number(row), axis=1
        )

        # GREENBLATT_RANK: Greenblatt Rank (placeholder - needs ranking data)
        result['GREENBLATT_RANK'] = None

        # MAGIC_FORMULA: Magic Formula (placeholder - needs ranking data)
        result['MAGIC_FORMULA'] = None

        # PRICE_TO_FCF: Price to FCF = Market Cap / Free Cash Flow
        result['PRICE_TO_FCF'] = latest.apply(
            lambda row: self._calculate_price_to_fcf(row), axis=1
        )

        # PS_RATIO: Same as PSR (already exists)
        result['PS_RATIO'] = latest.apply(
            lambda row: _safe_ratio(row.get('시가총액'), row.get('매출액')), axis=1
        )

        # === NEW: Composite Factors (3개) ===

        # ENTERPRISE_YIELD: Enterprise Yield = EBIT / EV * 100
        result['ENTERPRISE_YIELD'] = latest.apply(
            lambda row: self._calculate_enterprise_yield(row), axis=1
        )

        # PIOTROSKI_F_SCORE: Piotroski F-Score (9 criteria, 0-9 points)
        result['PIOTROSKI_F_SCORE'] = latest.apply(
            lambda row: self._calculate_piotroski_score(row), axis=1
        )

        # SHAREHOLDER_YIELD: Shareholder Yield = (Dividend Yield + Buyback Yield) * 100
        result['SHAREHOLDER_YIELD'] = None  # No dividend/buyback data

        # === NEW: Dividend Factors (2개) ===

        # DIVIDEND_GROWTH_3Y: 3-year dividend growth (CAGR)
        result['DIVIDEND_GROWTH_3Y'] = None  # No dividend data

        # DIVIDEND_GROWTH_YOY: YoY dividend growth
        result['DIVIDEND_GROWTH_YOY'] = None  # No dividend data

        return result

    async def _calculate_growth_factors(
        self,
        stock_codes: List[str],
        date: datetime
    ) -> pd.DataFrame:
        """성장성 팩터 계산 (8개)"""
        # 다년간 재무 데이터 필요
        financial_df = await self._fetch_financial_snapshot(stock_codes, date)
        if financial_df.empty:
            return pd.DataFrame()

        # 각 종목별로 연도별 데이터 정리
        result_list = []

        for stock_code in financial_df['stock_code'].unique():
            stock_data = financial_df[financial_df['stock_code'] == stock_code].sort_values('report_date', ascending=False)

            if len(stock_data) < 2:
                continue

            latest = stock_data.iloc[0]
            previous = stock_data.iloc[1] if len(stock_data) > 1 else None
            two_year_ago = stock_data.iloc[2] if len(stock_data) > 2 else None

            row = {'stock_code': stock_code}

            def _calc_growth(current, previous):
                if previous is None or pd.isna(previous) or previous == 0:
                    return None
                if pd.isna(current):
                    return None
                return ((current - previous) / previous) * 100

            # 매출 성장률 (1년)
            if previous is not None:
                row['REVENUE_GROWTH_1Y'] = _calc_growth(latest.get('매출액'), previous.get('매출액'))
                row['EARNINGS_GROWTH_1Y'] = _calc_growth(latest.get('당기순이익'), previous.get('당기순이익'))
                row['ASSET_GROWTH_1Y'] = _calc_growth(latest.get('자산총계'), previous.get('자산총계'))
                row['EQUITY_GROWTH_1Y'] = _calc_growth(latest.get('자본총계'), previous.get('자본총계'))
                # OPERATING_INCOME_GROWTH: 영업이익 성장률
                row['OPERATING_INCOME_GROWTH'] = _calc_growth(latest.get('영업이익'), previous.get('영업이익'))
                # GROSS_PROFIT_GROWTH: 매출총이익 성장률 = (매출액 - 매출원가) 성장률
                latest_gp = (latest.get('매출액', 0) or 0) - (latest.get('매출원가', 0) or 0)
                previous_gp = (previous.get('매출액', 0) or 0) - (previous.get('매출원가', 0) or 0)
                row['GROSS_PROFIT_GROWTH'] = _calc_growth(latest_gp if latest_gp > 0 else None, previous_gp if previous_gp > 0 else None)

            # 3년 CAGR (Compound Annual Growth Rate) - 3년 데이터 사용
            three_year_ago = stock_data.iloc[3] if len(stock_data) > 3 else None
            if three_year_ago is not None:
                # REVENUE_GROWTH_3Y: 3년 매출 성장률 = ((현재 - 3년전) / 3년전) * 100
                rev_3y = three_year_ago.get('매출액')
                rev_curr = latest.get('매출액')
                if rev_3y and rev_curr and rev_3y > 0:
                    row['REVENUE_GROWTH_3Y'] = ((rev_curr - rev_3y) / rev_3y) * 100

                # EARNINGS_GROWTH_3Y: 3년 순이익 성장률 = ((현재 - 3년전) / 3년전) * 100
                earn_3y = three_year_ago.get('당기순이익')
                earn_curr = latest.get('당기순이익')
                if earn_3y and earn_curr and earn_3y > 0:
                    row['EARNINGS_GROWTH_3Y'] = ((earn_curr - earn_3y) / earn_3y) * 100

            # OCF_GROWTH_1Y: Operating Cash Flow 1-year growth
            if previous is not None:
                row['OCF_GROWTH_1Y'] = _calc_growth(latest.get('영업활동현금흐름'), previous.get('영업활동현금흐름'))

                # BOOK_VALUE_GROWTH_1Y: Book value per share 1-year growth
                # BPS = 자본총계 / 발행주식수 (간소화: 자본총계 성장률로 근사)
                row['BOOK_VALUE_GROWTH_1Y'] = _calc_growth(latest.get('자본총계'), previous.get('자본총계'))

            # SUSTAINABLE_GROWTH_RATE: 지속가능성장률 = ROE * (1 - 배당성향)
            # 배당 데이터가 없으므로 ROE * 0.7로 근사 (유보율 70% 가정)
            net_income = latest.get('당기순이익')
            total_equity = latest.get('자본총계')
            if net_income and total_equity and total_equity > 0:
                roe = (float(net_income) / float(total_equity)) * 100
                # 배당성향 30% 가정 (유보율 70%)
                row['SUSTAINABLE_GROWTH_RATE'] = roe * 0.7

            result_list.append(row)

        return pd.DataFrame(result_list) if result_list else pd.DataFrame()

    async def _calculate_advanced_momentum(
        self,
        stock_codes: List[str],
        date: datetime,
        price_df: pd.DataFrame
    ) -> pd.DataFrame:
        """고급 모멘텀 팩터 (추가 7개) + 추가 기술적 지표 (22개) + 40개 신규 팩터"""
        if price_df.empty:
            return pd.DataFrame()

        result_list = []

        for stock_code in stock_codes:
            stock_prices = price_df[price_df['stock_code'] == stock_code].sort_values('trade_date')

            if stock_prices.empty:
                continue

            latest = stock_prices[stock_prices['trade_date'] == pd.Timestamp(date.date())]
            if latest.empty:
                continue

            current_price = latest.iloc[0]['close_price']
            latest_prices = stock_prices[stock_prices['trade_date'] <= pd.Timestamp(date.date())]

            def _calc_momentum(days_ago):
                target_date = pd.Timestamp(date.date()) - pd.Timedelta(days=days_ago)
                past = stock_prices[stock_prices['trade_date'] <= target_date]
                if past.empty:
                    return None
                past_price = past.iloc[-1]['close_price']
                if past_price == 0:
                    return None
                return ((current_price - past_price) / past_price) * 100

            row = {'stock_code': stock_code}
            row['MOMENTUM_1M'] = _calc_momentum(20)
            row['MOMENTUM_3M'] = _calc_momentum(60)
            row['MOMENTUM_6M'] = _calc_momentum(120)
            row['MOMENTUM_12M'] = _calc_momentum(240)

            # === 40 NEW FACTORS ===

            # Momentum factors (6개): RETURN_1M, RETURN_3M, RETURN_6M, RETURN_12M, RET_3D, RET_8D
            row['RETURN_1M'] = _calc_momentum(20)  # Same as MOMENTUM_1M
            row['RETURN_3M'] = _calc_momentum(60)  # Same as MOMENTUM_3M
            row['RETURN_6M'] = _calc_momentum(120)  # Same as MOMENTUM_6M
            row['RETURN_12M'] = _calc_momentum(240)  # Same as MOMENTUM_12M
            row['RET_3D'] = _calc_momentum(3)  # 3-day return
            row['RET_8D'] = _calc_momentum(8)  # 8-day return

            # 52주 고가/저가 대비 거리
            week_52 = stock_prices[stock_prices['trade_date'] >= pd.Timestamp(date.date()) - pd.Timedelta(days=365)]
            if not week_52.empty:
                high_52w = week_52['high_price'].max()
                low_52w = week_52['low_price'].min()

                if high_52w > 0:
                    row['DISTANCE_FROM_52W_HIGH'] = ((current_price - high_52w) / high_52w) * 100
                if low_52w > 0:
                    row['DISTANCE_FROM_52W_LOW'] = ((current_price - low_52w) / low_52w) * 100
                if high_52w > low_52w:
                    row['PRICE_POSITION'] = ((current_price - low_52w) / (high_52w - low_52w)) * 100
                    row['WEEK_52_POSITION'] = ((current_price - low_52w) / (high_52w - low_52w)) * 100  # NEW: same as PRICE_POSITION

                # NEW: DAYS_FROM_52W_HIGH and DAYS_FROM_52W_LOW
                high_52w_date = week_52[week_52['high_price'] == high_52w]['trade_date'].max()
                low_52w_date = week_52[week_52['low_price'] == low_52w]['trade_date'].max()
                row['DAYS_FROM_52W_HIGH'] = (pd.Timestamp(date.date()) - high_52w_date).days if pd.notna(high_52w_date) else None
                row['DAYS_FROM_52W_LOW'] = (pd.Timestamp(date.date()) - low_52w_date).days if pd.notna(low_52w_date) else None

            # === 22개 기술적 지표 추가 ===

            # Moving Averages (5개)
            if len(latest_prices) >= 5:
                row['MA_5'] = latest_prices.tail(5)['close_price'].mean()
            if len(latest_prices) >= 20:
                row['MA_20'] = latest_prices.tail(20)['close_price'].mean()
            if len(latest_prices) >= 60:
                row['MA_60'] = latest_prices.tail(60)['close_price'].mean()
            if len(latest_prices) >= 120:
                row['MA_120'] = latest_prices.tail(120)['close_price'].mean()
            if len(latest_prices) >= 250:
                row['MA_250'] = latest_prices.tail(250)['close_price'].mean()

            # PRICE_VS_MA20: 주가 vs 20일선 괴리율
            if len(latest_prices) >= 20:
                ma_20 = latest_prices.tail(20)['close_price'].mean()
                if ma_20 > 0:
                    row['PRICE_VS_MA20'] = ((current_price - ma_20) / ma_20) * 100

            # ATR (Average True Range) - 14일
            if len(latest_prices) >= 15:
                recent_14 = latest_prices.tail(15)
                high = recent_14['high_price'].values
                low = recent_14['low_price'].values
                close = recent_14['close_price'].values

                # True Range 계산
                tr_list = []
                for i in range(1, len(high)):
                    hl = high[i] - low[i]
                    hc = abs(high[i] - close[i-1])
                    lc = abs(low[i] - close[i-1])
                    tr_list.append(max(hl, hc, lc))

                if tr_list:
                    row['ATR'] = sum(tr_list) / len(tr_list)

            # ADX (Average Directional Index) - 14일
            if len(latest_prices) >= 28:
                recent_28 = latest_prices.tail(28)
                high = recent_28['high_price'].values
                low = recent_28['low_price'].values
                close = recent_28['close_price'].values

                # +DM, -DM 계산
                plus_dm = []
                minus_dm = []
                for i in range(1, len(high)):
                    up_move = high[i] - high[i-1]
                    down_move = low[i-1] - low[i]

                    if up_move > down_move and up_move > 0:
                        plus_dm.append(up_move)
                        minus_dm.append(0)
                    elif down_move > up_move and down_move > 0:
                        plus_dm.append(0)
                        minus_dm.append(down_move)
                    else:
                        plus_dm.append(0)
                        minus_dm.append(0)

                # ATR 계산
                tr_list = []
                for i in range(1, len(high)):
                    hl = high[i] - low[i]
                    hc = abs(high[i] - close[i-1])
                    lc = abs(low[i] - close[i-1])
                    tr_list.append(max(hl, hc, lc))

                if tr_list and len(plus_dm) >= 14:
                    avg_plus_dm = sum(plus_dm[-14:]) / 14
                    avg_minus_dm = sum(minus_dm[-14:]) / 14
                    atr = sum(tr_list[-14:]) / 14

                    if atr > 0:
                        plus_di = (avg_plus_dm / atr) * 100
                        minus_di = (avg_minus_dm / atr) * 100

                        if (plus_di + minus_di) > 0:
                            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
                            row['ADX'] = dx  # 간소화 버전 (실제로는 DX의 이동평균)

            # Aroon Up/Down (25일)
            if len(latest_prices) >= 25:
                recent_25 = latest_prices.tail(25)
                high_prices = recent_25['high_price'].values
                low_prices = recent_25['low_price'].values

                # 최고가 위치
                periods_since_high = 24 - np.argmax(high_prices)
                row['AROON_UP'] = ((25 - periods_since_high) / 25) * 100

                # 최저가 위치
                periods_since_low = 24 - np.argmin(low_prices)
                row['AROON_DOWN'] = ((25 - periods_since_low) / 25) * 100

            # CCI (Commodity Channel Index) - 20일
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                typical_price = (recent_20['high_price'] + recent_20['low_price'] + recent_20['close_price']) / 3
                sma_tp = typical_price.mean()
                mean_deviation = (typical_price - sma_tp).abs().mean()

                if mean_deviation > 0:
                    current_tp = (latest.iloc[0]['high_price'] + latest.iloc[0]['low_price'] + current_price) / 3
                    row['CCI'] = (current_tp - sma_tp) / (0.015 * mean_deviation)

            # MFI (Money Flow Index) - 14일
            if len(latest_prices) >= 15 and 'volume' in latest_prices.columns:
                recent_15 = latest_prices.tail(15)
                typical_price = (recent_15['high_price'] + recent_15['low_price'] + recent_15['close_price']) / 3
                money_flow = typical_price * recent_15['volume']

                positive_flow = 0
                negative_flow = 0
                for i in range(1, len(typical_price)):
                    if typical_price.iloc[i] > typical_price.iloc[i-1]:
                        positive_flow += money_flow.iloc[i]
                    elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                        negative_flow += money_flow.iloc[i]

                if negative_flow > 0:
                    money_ratio = positive_flow / negative_flow
                    row['MFI'] = 100 - (100 / (1 + money_ratio))

            # Williams %R - 14일
            if len(latest_prices) >= 14:
                recent_14 = latest_prices.tail(14)
                highest_high = recent_14['high_price'].max()
                lowest_low = recent_14['low_price'].min()

                if highest_high > lowest_low:
                    row['WILLIAMS_R'] = ((highest_high - current_price) / (highest_high - lowest_low)) * -100

            # Ultimate Oscillator (7, 14, 28일)
            if len(latest_prices) >= 29:
                def calc_bp_tr(prices):
                    bp_list = []
                    tr_list = []
                    for i in range(1, len(prices)):
                        close_curr = prices.iloc[i]['close_price']
                        low_curr = prices.iloc[i]['low_price']
                        high_curr = prices.iloc[i]['high_price']
                        close_prev = prices.iloc[i-1]['close_price']

                        bp = close_curr - min(low_curr, close_prev)
                        tr = max(high_curr, close_prev) - min(low_curr, close_prev)

                        bp_list.append(bp)
                        tr_list.append(tr)

                    return bp_list, tr_list

                recent_29 = latest_prices.tail(29)
                bp_list, tr_list = calc_bp_tr(recent_29)

                if len(bp_list) >= 28 and len(tr_list) >= 28:
                    avg7_bp = sum(bp_list[-7:]) if sum(tr_list[-7:]) == 0 else sum(bp_list[-7:]) / sum(tr_list[-7:])
                    avg14_bp = sum(bp_list[-14:]) if sum(tr_list[-14:]) == 0 else sum(bp_list[-14:]) / sum(tr_list[-14:])
                    avg28_bp = sum(bp_list[-28:]) if sum(tr_list[-28:]) == 0 else sum(bp_list[-28:]) / sum(tr_list[-28:])

                    row['ULTIMATE_OSCILLATOR'] = 100 * ((4*avg7_bp + 2*avg14_bp + avg28_bp) / 7)

            # TRIX (14일)
            if len(latest_prices) >= 42:  # 14*3 for triple EMA
                prices = latest_prices.tail(42)['close_price']

                # First EMA
                ema1 = prices.ewm(span=14, adjust=False).mean()
                # Second EMA
                ema2 = ema1.ewm(span=14, adjust=False).mean()
                # Third EMA
                ema3 = ema2.ewm(span=14, adjust=False).mean()

                if len(ema3) >= 2:
                    trix = ((ema3.iloc[-1] - ema3.iloc[-2]) / ema3.iloc[-2]) * 100
                    row['TRIX'] = trix

            # CMF (Chaikin Money Flow) - 20일
            if len(latest_prices) >= 20 and 'volume' in latest_prices.columns:
                recent_20 = latest_prices.tail(20)

                mf_volume_list = []
                for idx, price_row in recent_20.iterrows():
                    high = price_row['high_price']
                    low = price_row['low_price']
                    close = price_row['close_price']
                    volume = price_row['volume']

                    if high != low:
                        mf_multiplier = ((close - low) - (high - close)) / (high - low)
                        mf_volume = mf_multiplier * volume
                        mf_volume_list.append(mf_volume)

                if mf_volume_list and recent_20['volume'].sum() > 0:
                    row['CMF'] = sum(mf_volume_list) / recent_20['volume'].sum()

            # OBV (On-Balance Volume)
            if len(latest_prices) >= 2 and 'volume' in latest_prices.columns:
                obv = 0
                for i in range(1, len(latest_prices)):
                    if latest_prices.iloc[i]['close_price'] > latest_prices.iloc[i-1]['close_price']:
                        obv += latest_prices.iloc[i]['volume']
                    elif latest_prices.iloc[i]['close_price'] < latest_prices.iloc[i-1]['close_price']:
                        obv -= latest_prices.iloc[i]['volume']

                row['OBV'] = obv

            # VWAP (Volume Weighted Average Price)
            if len(latest_prices) >= 1 and 'volume' in latest_prices.columns:
                typical_price = (latest_prices['high_price'] + latest_prices['low_price'] + latest_prices['close_price']) / 3
                vwap_data = (typical_price * latest_prices['volume']).sum() / latest_prices['volume'].sum()
                row['VWAP'] = vwap_data

            # === NEW: Risk & Volatility Factors (10개) ===

            # Historical Volatility (2개)
            if len(latest_prices) >= 20:
                returns_20 = latest_prices.tail(20)['close_price'].pct_change()
                row['HISTORICAL_VOLATILITY_20'] = returns_20.std() * np.sqrt(252)

            if len(latest_prices) >= 60:
                returns_60 = latest_prices.tail(60)['close_price'].pct_change()
                row['HISTORICAL_VOLATILITY_60'] = returns_60.std() * np.sqrt(252)

            # Parkinson Volatility
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                parkinson_var = np.mean(np.log(recent_20['high_price'] / recent_20['low_price'])**2)
                row['PARKINSON_VOLATILITY'] = np.sqrt(parkinson_var / (4 * np.log(2))) if parkinson_var > 0 else None

            # Downside Volatility (negative returns only)
            if len(latest_prices) >= 20:
                returns = latest_prices.tail(20)['close_price'].pct_change()
                negative_returns = returns[returns < 0]
                row['DOWNSIDE_VOLATILITY'] = negative_returns.std() if len(negative_returns) > 0 else 0

            # Max Drawdown
            if len(latest_prices) >= 20:
                prices = latest_prices.tail(20)['close_price']
                cummax = prices.expanding().max()
                drawdown = (prices - cummax) / cummax
                row['MAX_DRAWDOWN'] = drawdown.min() * 100 if len(drawdown) > 0 else 0

            # Sharpe Ratio (assume risk-free rate = 2%)
            if len(latest_prices) >= 20:
                returns = latest_prices.tail(20)['close_price'].pct_change()
                avg_return = returns.mean() * 252  # Annualized
                volatility = returns.std() * np.sqrt(252)
                risk_free_rate = 0.02
                row['SHARPE_RATIO'] = (avg_return - risk_free_rate) / volatility if volatility > 0 else None

            # Sortino Ratio (using downside volatility)
            if len(latest_prices) >= 20:
                returns = latest_prices.tail(20)['close_price'].pct_change()
                avg_return = returns.mean() * 252
                negative_returns = returns[returns < 0]
                downside_std = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else None
                risk_free_rate = 0.02
                row['SORTINO_RATIO'] = (avg_return - risk_free_rate) / downside_std if downside_std and downside_std > 0 else None

            # === NEW: Microstructure Factors (5개) ===

            # Amihud Illiquidity
            if len(latest_prices) >= 20 and 'volume' in latest_prices.columns:
                recent_20 = latest_prices.tail(20)
                returns = recent_20['close_price'].pct_change()
                dollar_volume = recent_20['close_price'] * recent_20['volume']
                illiquidity = (returns.abs() / dollar_volume).mean()
                row['AMIHUD_ILLIQUIDITY'] = illiquidity * 1e6  # Scale up for readability

            # Ease of Movement (EMV)
            if len(latest_prices) >= 2 and 'volume' in latest_prices.columns:
                recent = latest_prices.tail(2)
                if len(recent) == 2:
                    curr = recent.iloc[1]
                    prev = recent.iloc[0]
                    mid_point = (curr['high_price'] + curr['low_price']) / 2
                    prev_mid = (prev['high_price'] + prev['low_price']) / 2
                    distance_moved = mid_point - prev_mid
                    box_ratio = (curr['volume'] / 1e6) / (curr['high_price'] - curr['low_price']) if (curr['high_price'] - curr['low_price']) > 0 else 0
                    row['EASE_OF_MOVEMENT'] = distance_moved / box_ratio if box_ratio > 0 else 0

            # Force Index
            if len(latest_prices) >= 2 and 'volume' in latest_prices.columns:
                recent = latest_prices.tail(2)
                if len(recent) == 2:
                    price_change = recent.iloc[1]['close_price'] - recent.iloc[0]['close_price']
                    volume = recent.iloc[1]['volume']
                    row['FORCE_INDEX'] = price_change * volume

            # Intraday Volatility
            if 'high_price' in latest.iloc[0] and 'low_price' in latest.iloc[0]:
                row['INTRADAY_VOLATILITY'] = ((latest.iloc[0]['high_price'] - latest.iloc[0]['low_price']) / latest.iloc[0]['close_price']) * 100

            # Volume Price Trend
            if len(latest_prices) >= 20 and 'volume' in latest_prices.columns:
                vpt = 0
                for i in range(1, len(latest_prices.tail(20))):
                    prev_close = latest_prices.iloc[i-1]['close_price']
                    curr_close = latest_prices.iloc[i]['close_price']
                    volume = latest_prices.iloc[i]['volume']
                    pct_change = (curr_close - prev_close) / prev_close if prev_close > 0 else 0
                    vpt += volume * pct_change
                row['VOLUME_PRICE_TREND'] = vpt

            # === NEW: Composite Factors (3개) ===
            # Will be calculated in financial factors section

            # === NEW: Duplicate/Alias Factors (9개) ===
            row['DEBTRATIO'] = row.get('DEBT_RATIO')  # Alias
            row['DIVIDENDYIELD'] = row.get('DIVIDEND_YIELD')  # Alias
            row['EARNINGS_GROWTH'] = row.get('EARNINGS_GROWTH_1Y')  # Alias
            row['OPERATING_INCOME_GROWTH_YOY'] = row.get('OPERATING_INCOME_GROWTH')  # Alias (already exists)
            row['PEG_RATIO'] = row.get('PEG')  # Alias
            row['REVENUE_GROWTH'] = row.get('REVENUE_GROWTH_1Y')  # Alias
            row['SMA'] = row.get('MA_20')  # Alias to MA_20

            result_list.append(row)

        return pd.DataFrame(result_list) if result_list else pd.DataFrame()

    async def _calculate_stability_factors(
        self,
        stock_codes: List[str],
        date: datetime,
        financial_df: pd.DataFrame
    ) -> pd.DataFrame:
        """안정성 팩터 계산 (8개)"""
        if financial_df.empty:
            return pd.DataFrame()

        latest = financial_df.sort_values('report_date', ascending=False).drop_duplicates(subset=['stock_code'])

        def _safe_ratio(num, den):
            if num is None or den is None or pd.isna(num) or pd.isna(den) or den == 0:
                return None
            return float(num) / float(den)

        result = pd.DataFrame()
        result['stock_code'] = latest['stock_code']

        # CURRENT_RATIO: 유동비율 = 유동자산 / 유동부채
        result['CURRENT_RATIO'] = latest.apply(
            lambda row: _safe_ratio(row.get('유동자산'), row.get('유동부채')), axis=1
        )

        # QUICK_RATIO: 당좌비율 = (유동자산 - 재고자산) / 유동부채
        result['QUICK_RATIO'] = latest.apply(
            lambda row: _safe_ratio(
                (row.get('유동자산', 0) - row.get('재고자산', 0)),
                row.get('유동부채')
            ) if row.get('유동부채', 0) > 0 else None, axis=1
        )

        # DEBT_TO_EQUITY: 부채비율 = 부채총계 / 자본총계
        result['DEBT_TO_EQUITY'] = latest.apply(
            lambda row: _safe_ratio(row.get('부채총계'), row.get('자본총계')), axis=1
        )

        # INTEREST_COVERAGE: 이자보상비율 = 영업이익 / 이자비용
        result['INTEREST_COVERAGE'] = latest.apply(
            lambda row: _safe_ratio(row.get('영업이익'), row.get('이자비용')), axis=1
        )

        # CASH_RATIO: 현금비율 = 현금및현금성자산 / 유동부채
        result['CASH_RATIO'] = latest.apply(
            lambda row: _safe_ratio(row.get('현금및현금성자산'), row.get('유동부채')), axis=1
        )

        # WORKING_CAPITAL_RATIO: 운전자본비율 = (유동자산 - 유동부채) / 자산총계 * 100
        def calc_working_capital(row):
            ratio = _safe_ratio(
                (row.get('유동자산', 0) - row.get('유동부채', 0)),
                row.get('자산총계')
            )
            return ratio * 100 if ratio is not None else None

        result['WORKING_CAPITAL_RATIO'] = latest.apply(calc_working_capital, axis=1)

        # EQUITY_RATIO: 자기자본비율 = 자본총계 / 자산총계 * 100
        def calc_equity_ratio(row):
            ratio = _safe_ratio(row.get('자본총계'), row.get('자산총계'))
            return ratio * 100 if ratio is not None else None

        result['EQUITY_RATIO'] = latest.apply(calc_equity_ratio, axis=1)

        # ALTMAN_Z_SCORE: 알트만 Z스코어 (간소화 버전)
        # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        # X1 = 운전자본/자산총계, X2 = 이익잉여금/자산총계, X3 = 영업이익/자산총계
        # X4 = 시가총액/부채총계, X5 = 매출액/자산총계
        # 이익잉여금 데이터가 없으므로 간소화된 버전 사용
        result['ALTMAN_Z_SCORE'] = None  # 이익잉여금 데이터 필요

        return result

    async def _calculate_technical_factors(
        self,
        stock_codes: List[str],
        date: datetime,
        price_df: pd.DataFrame
    ) -> pd.DataFrame:
        """기술적 팩터 계산 (6개)"""
        if price_df.empty:
            return pd.DataFrame()

        result_list = []

        for stock_code in stock_codes:
            stock_prices = price_df[price_df['stock_code'] == stock_code].sort_values('trade_date')

            if stock_prices.empty:
                continue

            latest_prices = stock_prices[stock_prices['trade_date'] <= pd.Timestamp(date.date())]
            if latest_prices.empty:
                continue

            row = {'stock_code': stock_code}

            # RSI 계산 (14일) - RSI_14와 동일
            if len(latest_prices) >= 15:
                recent_14 = latest_prices.tail(15)
                price_changes = recent_14['close_price'].diff()
                gains = price_changes.where(price_changes > 0, 0)
                losses = -price_changes.where(price_changes < 0, 0)
                avg_gain = gains.mean()
                avg_loss = losses.mean()
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    rsi_val = 100 - (100 / (1 + rs))
                    row['RSI_14'] = rsi_val
                    row['RSI'] = rsi_val  # RSI와 RSI_14는 동일

            # Bollinger Band Position
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                ma_20 = recent_20['close_price'].mean()
                std_20 = recent_20['close_price'].std()
                current = latest_prices.iloc[-1]['close_price']
                if std_20 > 0:
                    row['BOLLINGER_POSITION'] = (current - ma_20) / (2 * std_20)
                    # Phase 3: BOLLINGER_WIDTH = (upper - lower) / ma = (4 * std) / ma
                    row['BOLLINGER_WIDTH'] = (4 * std_20 / ma_20) * 100 if ma_20 > 0 else None

            # Stochastic Oscillator (14일)
            if len(latest_prices) >= 14:
                recent_14 = latest_prices.tail(14)
                high_14 = recent_14['high_price'].max()
                low_14 = recent_14['low_price'].min()
                current = latest_prices.iloc[-1]['close_price']
                if high_14 > low_14:
                    row['STOCHASTIC_14'] = ((current - low_14) / (high_14 - low_14)) * 100

            # Volume ROC
            if len(latest_prices) >= 40:
                recent_20 = latest_prices.tail(20)
                prev_20 = latest_prices.tail(40).head(20)
                avg_vol_recent = recent_20['volume'].mean()
                avg_vol_prev = prev_20['volume'].mean()
                if avg_vol_prev > 0:
                    row['VOLUME_ROC'] = ((avg_vol_recent - avg_vol_prev) / avg_vol_prev) * 100

            # Phase 3: VOLUME_RATIO_20D: 현재 거래량 / 20일 평균 거래량
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                avg_vol = recent_20['volume'].mean()
                current_vol = latest_prices.iloc[-1]['volume']
                if avg_vol > 0:
                    row['VOLUME_RATIO_20D'] = (current_vol / avg_vol) * 100

            # PRICE_TO_MA_20: 주가 / 20일 이동평균
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                ma_20 = recent_20['close_price'].mean()
                current = latest_prices.iloc[-1]['close_price']
                if ma_20 > 0:
                    row['PRICE_TO_MA_20'] = (current / ma_20) * 100

            # Phase 3: MACD (간소화된 버전, SMA 사용)
            if len(latest_prices) >= 26:
                ema_12 = latest_prices.tail(26)['close_price'].ewm(span=12, adjust=False).mean().iloc[-1]
                ema_26 = latest_prices.tail(26)['close_price'].ewm(span=26, adjust=False).mean().iloc[-1]
                macd_line = ema_12 - ema_26
                row['MACD'] = macd_line

                # MACD Signal (9-day EMA of MACD)
                if len(latest_prices) >= 34:  # Need more data for signal line
                    macd_series = latest_prices.tail(34)['close_price'].ewm(span=12, adjust=False).mean() - \
                                  latest_prices.tail(34)['close_price'].ewm(span=26, adjust=False).mean()
                    signal_line = macd_series.ewm(span=9, adjust=False).mean().iloc[-1]
                    row['MACD_SIGNAL'] = signal_line
                    row['MACD_HISTOGRAM'] = macd_line - signal_line
                else:
                    row['MACD_SIGNAL'] = None
                    row['MACD_HISTOGRAM'] = None
            else:
                row['MACD_SIGNAL'] = None
                row['MACD_HISTOGRAM'] = None

            # RELATIVE_STRENGTH: Relative strength vs market (3개월 기준)
            # 시장 데이터가 없으므로 절대 수익률로 근사 (3개월)
            if len(latest_prices) >= 60:
                price_3m_ago = latest_prices.iloc[-60]['close_price'] if len(latest_prices) >= 60 else latest_prices.iloc[0]['close_price']
                current_price = latest_prices.iloc[-1]['close_price']
                if price_3m_ago > 0:
                    stock_return = ((current_price - price_3m_ago) / price_3m_ago) * 100
                    row['RELATIVE_STRENGTH'] = stock_return  # 절대 수익률로 근사

            # VOLUME_MOMENTUM: Volume trend = (최근20일 평균거래량 / 과거60일 평균거래량) * 100
            if len(latest_prices) >= 60:
                recent_20_vol = latest_prices.tail(20)['volume'].mean()
                past_60_vol = latest_prices.tail(60)['volume'].mean()
                if past_60_vol > 0:
                    row['VOLUME_MOMENTUM'] = (recent_20_vol / past_60_vol) * 100

            # BETA: Market beta (volatility vs market)
            # 시장 데이터가 없으므로 None
            row['BETA'] = None  # Requires market index data

            result_list.append(row)

        return pd.DataFrame(result_list) if result_list else pd.DataFrame()

    async def _calculate_quality_factors(
        self,
        stock_codes: List[str],
        date: datetime,
        financial_df: pd.DataFrame
    ) -> pd.DataFrame:
        """품질 팩터 계산 (5개)"""
        if financial_df.empty:
            return pd.DataFrame()

        latest = financial_df.sort_values('report_date', ascending=False).drop_duplicates(subset=['stock_code'])

        result = pd.DataFrame()
        result['stock_code'] = latest['stock_code']

        def _safe_ratio(num, den):
            if num is None or den is None or pd.isna(num) or pd.isna(den) or den == 0:
                return None
            return float(num) / float(den)

        # ACCRUALS_RATIO: 발생액비율 = (당기순이익 - 영업활동현금흐름) / 자산총계
        result['ACCRUALS_RATIO'] = latest.apply(
            lambda row: _safe_ratio(
                (row.get('당기순이익', 0) - row.get('영업활동현금흐름', 0)),
                row.get('자산총계')
            ) if row.get('영업활동현금흐름') is not None else None, axis=1
        )

        # EARNINGS_QUALITY: 이익품질 = 영업활동현금흐름 / 당기순이익
        result['EARNINGS_QUALITY'] = latest.apply(
            lambda row: _safe_ratio(row.get('영업활동현금흐름'), row.get('당기순이익'))
            if row.get('영업활동현금흐름') is not None and row.get('당기순이익') is not None else None, axis=1
        )

        # QUALITY_SCORE: 간단한 품질 점수 (0-5 점)
        result['QUALITY_SCORE'] = latest.apply(
            lambda row: (
                (1 if row.get('당기순이익', 0) > 0 else 0) +
                (1 if row.get('영업활동현금흐름', 0) > 0 else 0) +
                (1 if row.get('영업활동현금흐름', 0) > row.get('당기순이익', 0) else 0) +
                (1 if row.get('자본총계', 0) > row.get('부채총계', 0) else 0) +
                (1 if row.get('유동자산', 0) > row.get('유동부채', 1) else 0)
            ), axis=1
        )

        # LEVERAGE: 레버리지 = 부채총계 / 자산총계 * 100
        result['LEVERAGE'] = latest.apply(
            lambda row: _safe_ratio(row.get('부채총계'), row.get('자산총계')) * 100
            if _safe_ratio(row.get('부채총계'), row.get('자산총계')) is not None else None, axis=1
        )

        # RETENTION_RATIO: 유보율 (배당 데이터 필요)
        result['RETENTION_RATIO'] = None

        # FCF_YIELD: 잉여현금흐름 수익률 = FCF / 시가총액 * 100
        # FCF = 영업활동현금흐름 - 투자활동현금흐름
        result['FCF_YIELD'] = latest.apply(
            lambda row: self._calculate_fcf_yield(row), axis=1
        )

        return result

    def _calculate_fcf_yield(self, row) -> float:
        """FCF_YIELD 계산 헬퍼"""
        try:
            ocf = row.get('영업활동현금흐름')
            icf = row.get('투자활동현금흐름')
            market_cap = row.get('market_cap')

            if ocf is None or icf is None or market_cap is None or market_cap == 0:
                return None

            # FCF = 영업활동현금흐름 - 투자활동현금흐름 (투자는 음수이므로 빼기)
            # 투자활동현금흐름이 음수면 절댓값 취해서 빼기
            fcf = float(ocf) - abs(float(icf))
            fcf_yield = (fcf / float(market_cap)) * 100

            return fcf_yield
        except:
            return None

    def _calculate_roic(self, row) -> float:
        """ROIC 계산 헬퍼"""
        try:
            operating_income = row.get('영업이익')
            net_income = row.get('당기순이익')
            tax_expense = row.get('법인세비용')
            total_equity = row.get('자본총계')
            total_debt = row.get('부채총계')

            if operating_income is None or total_equity is None:
                return None

            # 세율 계산: 법인세비용 / (당기순이익 + 법인세비용)
            tax_rate = 0
            if tax_expense and net_income and (net_income + tax_expense) > 0:
                tax_rate = float(tax_expense) / (float(net_income) + float(tax_expense))

            # NOPAT = 영업이익 * (1 - 세율)
            nopat = float(operating_income) * (1 - tax_rate)

            # 투하자본 = 자본총계 + 부채총계
            invested_capital = float(total_equity)
            if total_debt:
                invested_capital += float(total_debt)

            if invested_capital == 0:
                return None

            return (nopat / invested_capital) * 100
        except:
            return None

    def _calculate_ev_fcf(self, row, ev_calc_func) -> float:
        """EV_FCF 계산 헬퍼"""
        try:
            ev, _ = ev_calc_func(row)
            if ev is None:
                return None

            ocf = row.get('영업활동현금흐름')
            icf = row.get('투자활동현금흐름')

            if ocf is None or icf is None:
                return None

            # FCF = 영업활동현금흐름 - 투자활동현금흐름
            fcf = float(ocf) - abs(float(icf))

            if fcf == 0:
                return None

            return ev / fcf
        except:
            return None

    def _calculate_ptbv(self, row) -> float:
        """PTBV 계산 헬퍼"""
        try:
            market_cap = row.get('market_cap')
            total_equity = row.get('자본총계')
            intangible_assets = row.get('무형자산', 0)

            if market_cap is None or total_equity is None:
                return None

            # 유형자산 = 자본총계 - 무형자산
            tangible_book_value = float(total_equity) - float(intangible_assets or 0)

            if tangible_book_value == 0:
                return None

            return float(market_cap) / tangible_book_value
        except:
            return None

    def _calculate_graham_number(self, row) -> float:
        """Graham Number 계산 헬퍼"""
        try:
            net_income = row.get('당기순이익')
            total_equity = row.get('자본총계')
            listed_shares = row.get('listed_shares', 1)

            if net_income is None or total_equity is None or listed_shares == 0:
                return None

            eps = float(net_income) / float(listed_shares)
            bvps = float(total_equity) / float(listed_shares)

            if eps > 0 and bvps > 0:
                return np.sqrt(22.5 * eps * bvps)
            return None
        except:
            return None

    def _calculate_price_to_fcf(self, row) -> float:
        """Price to FCF 계산 헬퍼"""
        try:
            market_cap = row.get('market_cap')
            ocf = row.get('영업활동현금흐름')
            icf = row.get('투자활동현금흐름')

            if market_cap is None or ocf is None or icf is None:
                return None

            fcf = float(ocf) - abs(float(icf))
            if fcf == 0:
                return None

            return float(market_cap) / fcf
        except:
            return None

    def _calculate_enterprise_yield(self, row) -> float:
        """Enterprise Yield 계산 헬퍼"""
        try:
            market_cap = row.get('market_cap')
            total_debt = row.get('부채총계')
            cash = row.get('현금및현금성자산', 0)
            operating_income = row.get('영업이익')

            if market_cap is None or total_debt is None or operating_income is None:
                return None

            ev = float(market_cap) + float(total_debt) - float(cash or 0)
            if ev == 0:
                return None

            return (float(operating_income) / ev) * 100
        except:
            return None

    def _calculate_piotroski_score(self, row) -> int:
        """Piotroski F-Score 계산 헬퍼 (9 criteria, 0-9 points)"""
        try:
            score = 0

            # 1. ROA > 0
            net_income = row.get('당기순이익')
            total_assets = row.get('자산총계')
            if net_income and total_assets and float(net_income) > 0 and float(total_assets) > 0:
                score += 1

            # 2. Operating Cash Flow > 0
            ocf = row.get('영업활동현금흐름')
            if ocf and float(ocf) > 0:
                score += 1

            # 3. OCF > Net Income (quality of earnings)
            if ocf and net_income and float(ocf) > float(net_income):
                score += 1

            # 4. Current Ratio increasing (need previous data - simplified)
            current_assets = row.get('유동자산')
            current_liabilities = row.get('유동부채')
            if current_assets and current_liabilities and float(current_liabilities) > 0:
                if float(current_assets) / float(current_liabilities) > 1:
                    score += 1

            # 5. Debt/Assets decreasing (need previous data - simplified)
            total_debt = row.get('부채총계')
            if total_debt and total_assets:
                debt_ratio = float(total_debt) / float(total_assets)
                if debt_ratio < 0.5:
                    score += 1

            # 6-9. Simplified criteria (need multi-year data)
            # For now, give partial score if company is profitable
            if net_income and float(net_income) > 0:
                score += 2  # Simplified for missing historical data

            return score
        except:
            return 0

    def _attach_ranks(self, df: pd.DataFrame) -> pd.DataFrame:
        """각 팩터별 랭킹 계산"""
        if df.empty:
            return df

        # 높을수록 좋은 팩터 (상승 정렬)
        higher_better = [
            'ROE', 'ROA', 'MOM_3M', 'AVG_TRADING_VALUE', 'TURNOVER_RATE',
            'GPM', 'OPM', 'NPM', 'ASSET_TURNOVER', 'EQUITY_MULTIPLIER',
            'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y',
            'MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M', 'DISTANCE_FROM_52W_LOW',
            'CURRENT_RATIO', 'QUICK_RATIO', 'INTEREST_COVERAGE', 'EQUITY_RATIO',
            'RSI_14', 'PRICE_POSITION',
            # 15개 추가 팩터
            'ROIC', 'INVENTORY_TURNOVER', 'OCF_GROWTH_1Y', 'BOOK_VALUE_GROWTH_1Y',
            'SUSTAINABLE_GROWTH_RATE', 'RELATIVE_STRENGTH', 'VOLUME_MOMENTUM', 'DIVIDEND_YIELD'
        ]

        # 낮을수록 좋은 팩터 (하강 정렬)
        lower_better = [
            'PER', 'PBR', 'DEBT_RATIO', 'VOLATILITY_90',
            'DEBT_TO_EQUITY', 'LEVERAGE', 'ACCRUALS_RATIO',
            # 15개 추가 팩터 중 낮을수록 좋은 것
            'PEG', 'EV_FCF', 'CAPE_RATIO', 'PTBV'
        ]

        for col in higher_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=False, method='dense', na_option='bottom')

        for col in lower_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=True, method='dense', na_option='bottom')

        # 종합 점수 계산
        rank_columns = [c for c in df.columns if c.endswith('_RANK')]
        if rank_columns:
            df['COMPOSITE_SCORE'] = df[rank_columns].mean(axis=1)
            df['COMPOSITE_RANK'] = df['COMPOSITE_SCORE'].rank(ascending=True, method='dense')

        return df

    async def get_factor_data_for_date(
        self,
        date: datetime,
        factor_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """특정 날짜의 팩터 데이터 조회"""

        # 모든 활성 종목 가져오기
        stock_codes = await self._get_active_stocks(date)

        # 모든 팩터 계산
        all_factors = await self.calculate_all_factors(stock_codes, date)

        # 특정 팩터만 필터링 (요청된 경우)
        if factor_names:
            columns_to_keep = ['stock_code', 'stock_name'] + factor_names
            columns_to_keep = [col for col in columns_to_keep if col in all_factors.columns]
            all_factors = all_factors[columns_to_keep]

        # 날짜 컬럼 추가
        all_factors['date'] = date

        return all_factors

    async def _get_active_stocks(self, date: datetime) -> List[str]:
        """활성 종목 리스트 조회"""
        from sqlalchemy import text

        query = text("""
        SELECT DISTINCT c.stock_code
        FROM stock_prices sp
        JOIN companies c ON sp.company_id = c.company_id
        WHERE sp.trade_date = :date
        AND sp.volume > 0
        AND sp.close_price > 0
        """)

        result = await self.db.execute(query, {"date": date.date()})
        return [row[0] for row in result.fetchall()]
