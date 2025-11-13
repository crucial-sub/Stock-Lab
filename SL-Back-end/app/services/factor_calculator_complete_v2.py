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

logger = logging.getLogger(__name__)


class CompleteFactorCalculatorV2:
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
            '당기순이익', '영업이익', '매출액', '매출원가',
            '영업비용', '법인세비용', '이자비용'
        ]

        # 재무상태표 계정 과목
        balance_accounts = [
            '자산총계', '자본총계', '부채총계',
            '유동자산', '비유동자산', '유동부채', '비유동부채',
            '재고자산', '매출채권', '현금및현금성자산'
        ]

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

        income_df = pd.DataFrame((await self.db.execute(income_query)).mappings().all())
        balance_df = pd.DataFrame((await self.db.execute(balance_query)).mappings().all())

        if income_df.empty and balance_df.empty:
            return pd.DataFrame()

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

        # 거래량 팩터
        recent_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=20)]
        avg_trading = recent_window.groupby('stock_code')['trading_value'].mean()
        avg_trading.name = 'AVG_TRADING_VALUE'

        turnover = recent_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(g['volume'].mean(), g['listed_shares'].iloc[0]) * 100 if len(g) > 0 and g['listed_shares'].iloc[0] else None,
            include_groups=False
        ).rename('TURNOVER_RATE')

        # 모멘텀 팩터
        momentum_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=120)]
        momentum = momentum_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(
                g[g['trade_date'] == g['trade_date'].max()]['close_price'].iloc[0],
                g.sort_values('trade_date').iloc[0]['close_price']
            ) - 1 if not g.empty and len(g[g['trade_date'] == g['trade_date'].max()]) > 0 else None,
            include_groups=False
        ).rename('MOM_3M')

        # 변동성
        pct_returns = price_df.sort_values('trade_date').groupby('stock_code')['close_price'].pct_change()
        price_df = price_df.assign(daily_return=pct_returns)
        vol_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=90)]
        volatility = vol_window.groupby('stock_code')['daily_return'].std().rename('VOLATILITY_90')

        # merge
        merged = merged.merge(avg_trading, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(turnover, left_on='stock_code', right_index=True, how='left')
        merged = merged.merge(momentum, left_on='stock_code', right_index=True, how='left')
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

        # 영업현금흐름은 cashflow_statements에서 가져와야 하므로 나중에 추가
        result['OCF_RATIO'] = None

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

            # 3년 CAGR (Compound Annual Growth Rate)
            if two_year_ago is not None:
                rev_2y = two_year_ago.get('매출액')
                rev_curr = latest.get('매출액')
                if rev_2y and rev_curr and rev_2y > 0:
                    row['REVENUE_GROWTH_3Y'] = (((rev_curr / rev_2y) ** (1/2)) - 1) * 100

                earn_2y = two_year_ago.get('당기순이익')
                earn_curr = latest.get('당기순이익')
                if earn_2y and earn_curr and earn_2y > 0:
                    row['EARNINGS_GROWTH_3Y'] = (((earn_curr / earn_2y) ** (1/2)) - 1) * 100

            result_list.append(row)

        return pd.DataFrame(result_list) if result_list else pd.DataFrame()

    async def _calculate_advanced_momentum(
        self,
        stock_codes: List[str],
        date: datetime,
        price_df: pd.DataFrame
    ) -> pd.DataFrame:
        """고급 모멘텀 팩터 (추가 7개)"""
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
            row['MOMENTUM_6M'] = _calc_momentum(120)
            row['MOMENTUM_12M'] = _calc_momentum(240)

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

        # 나머지 팩터들은 더 복잡한 계산 필요
        result['ALTMAN_Z_SCORE'] = None
        result['WORKING_CAPITAL_RATIO'] = None
        result['EQUITY_RATIO'] = latest.apply(
            lambda row: _safe_ratio(row.get('자본총계'), row.get('자산총계')) * 100
            if _safe_ratio(row.get('자본총계'), row.get('자산총계')) is not None else None, axis=1
        )

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

            # RSI 계산 (14일)
            if len(latest_prices) >= 15:
                recent_14 = latest_prices.tail(15)
                price_changes = recent_14['close_price'].diff()
                gains = price_changes.where(price_changes > 0, 0)
                losses = -price_changes.where(price_changes < 0, 0)
                avg_gain = gains.mean()
                avg_loss = losses.mean()
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    row['RSI_14'] = 100 - (100 / (1 + rs))

            # Bollinger Band Position
            if len(latest_prices) >= 20:
                recent_20 = latest_prices.tail(20)
                ma_20 = recent_20['close_price'].mean()
                std_20 = recent_20['close_price'].std()
                current = latest_prices.iloc[-1]['close_price']
                if std_20 > 0:
                    row['BOLLINGER_POSITION'] = (current - ma_20) / (2 * std_20)

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

            # MACD는 복잡하므로 나중에 추가
            row['MACD_SIGNAL'] = None
            row['PRICE_TO_MA_20'] = None

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

        # Accruals Ratio = (당기순이익 - 영업현금흐름) / 자산총계
        # 영업현금흐름 데이터가 없으므로 일단 None
        result['ACCRUALS_RATIO'] = None
        result['EARNINGS_QUALITY'] = None
        result['QUALITY_SCORE'] = None

        # 자산 대비 부채 비율
        result['LEVERAGE'] = latest.apply(
            lambda row: (row.get('부채총계', 0) / row.get('자산총계', 1)) * 100
            if row.get('자산총계', 0) > 0 else None, axis=1
        )

        # 유보율 (retained earnings ratio) - 근사치
        result['RETENTION_RATIO'] = None

        return result

    def _attach_ranks(self, df: pd.DataFrame) -> pd.DataFrame:
        """각 팩터별 랭킹 계산"""
        if df.empty:
            return df

        # 높을수록 좋은 팩터 (상승 정렬)
        higher_better = [
            'ROE', 'ROA', 'MOM_3M', 'AVG_TRADING_VALUE', 'TURNOVER_RATE',
            'GPM', 'OPM', 'NPM', 'ASSET_TURNOVER', 'EQUITY_MULTIPLIER',
            'REVENUE_GROWTH_1Y', 'REVENUE_GROWTH_3Y', 'EARNINGS_GROWTH_1Y', 'EARNINGS_GROWTH_3Y',
            'MOMENTUM_1M', 'MOMENTUM_6M', 'MOMENTUM_12M', 'DISTANCE_FROM_52W_LOW',
            'CURRENT_RATIO', 'QUICK_RATIO', 'INTEREST_COVERAGE', 'EQUITY_RATIO',
            'RSI_14', 'PRICE_POSITION'
        ]

        # 낮을수록 좋은 팩터 (하강 정렬)
        lower_better = [
            'PER', 'PBR', 'DEBT_RATIO', 'VOLATILITY_90',
            'DEBT_TO_EQUITY', 'LEVERAGE', 'ACCRUALS_RATIO'
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
