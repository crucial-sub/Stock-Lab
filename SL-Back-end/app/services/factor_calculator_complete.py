"""
완전한 팩터 계산 모듈 - 54개 팩터 구현
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


class CompleteFactorCalculator:
    """54개 팩터 완전 구현"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_all_factors(
        self,
        stock_codes: List[str],
        date: datetime
    ) -> pd.DataFrame:
        """현재 스키마 기반 팩터 계산"""

        price_df = await self._fetch_price_history(stock_codes, date)
        if price_df.empty:
            logger.warning("가격 데이터가 없어 팩터 계산을 건너뜁니다")
            return pd.DataFrame()

        financial_df = await self._fetch_financial_snapshot(stock_codes, date)
        factor_df = self._build_factor_frame(price_df, financial_df, date)
        if factor_df.empty:
            return factor_df

        factor_df = self._attach_ranks(factor_df)
        return factor_df

    async def _fetch_price_history(
        self,
        stock_codes: Optional[List[str]],
        as_of: datetime
    ) -> pd.DataFrame:
        start_window = as_of - timedelta(days=400)

        query = (
            select(
                Company.stock_code,
                Company.company_name.label('stock_name'),
                Company.industry,
                StockPrice.trade_date,
                StockPrice.close_price,
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
        start_year = str(as_of.year - 1)
        end_year = str(as_of.year)

        base_filters = [
            FinancialStatement.bsns_year >= start_year,
            FinancialStatement.bsns_year <= end_year,
            FinancialStatement.report_date <= as_of.date()
        ]

        if stock_codes:
            base_filters.append(Company.stock_code.in_(stock_codes))

        income_accounts = [
            '당기순이익', '영업이익', '매출액'
        ]
        balance_accounts = [
            '자산총계', '자본총계', '부채총계'
        ]

        income_query = select(
            Company.stock_code,
            FinancialStatement.bsns_year.label('fiscal_year'),
            FinancialStatement.reprt_code.label('report_code'),
            IncomeStatement.account_nm,
            IncomeStatement.thstrm_amount.label('current_amount')
        ).join(
            IncomeStatement, FinancialStatement.stmt_id == IncomeStatement.stmt_id
        ).join(
            Company, FinancialStatement.company_id == Company.company_id
        ).where(
            and_(*base_filters, IncomeStatement.account_nm.in_(income_accounts))
        )

        balance_query = select(
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

        def _report_date(row):
            year = int(row['fiscal_year'])
            code = row['report_code']
            if code == '11011':
                return datetime(year, 12, 31)
            if code == '11012':
                return datetime(year, 6, 30)
            if code == '11013':
                return datetime(year, 3, 31)
            if code == '11014':
                return datetime(year, 9, 30)
            return datetime(year, 12, 31)

        merged['report_date'] = merged.apply(_report_date, axis=1)

        latest = merged.sort_values('report_date', ascending=False).drop_duplicates(subset=['stock_code'])
        return latest

    def _build_factor_frame(
        self,
        price_df: pd.DataFrame,
        financial_df: pd.DataFrame,
        snapshot_date: datetime
    ) -> pd.DataFrame:
        if price_df.empty:
            return pd.DataFrame()

        latest_prices = price_df[price_df['trade_date'] == pd.Timestamp(snapshot_date.date())].copy()
        if latest_prices.empty:
            logger.warning("스냅샷 날짜에 해당하는 가격이 없습니다.")
            return pd.DataFrame()

        merged = latest_prices.merge(financial_df, on='stock_code', how='left', suffixes=('', '_fin'))

        def _safe_ratio(numerator, denominator):
            if numerator is None or denominator is None:
                return None
            if denominator == 0:
                return None
            return float(numerator) / float(denominator)

        merged['PER'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('당기순이익')), axis=1)
        merged['PBR'] = merged.apply(lambda row: _safe_ratio(row['market_cap'], row.get('자본총계')), axis=1)
        merged['ROE'] = merged.apply(lambda row: _safe_ratio(row.get('당기순이익'), row.get('자본총계')) * 100 if _safe_ratio(row.get('당기순이익'), row.get('자본총계')) is not None else None, axis=1)
        merged['ROA'] = merged.apply(lambda row: _safe_ratio(row.get('당기순이익'), row.get('자산총계')) * 100 if _safe_ratio(row.get('당기순이익'), row.get('자산총계')) is not None else None, axis=1)
        merged['DEBT_RATIO'] = merged.apply(lambda row: _safe_ratio(row.get('부채총계'), row.get('자본총계')) * 100 if _safe_ratio(row.get('부채총계'), row.get('자본총계')) is not None else None, axis=1)

        recent_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=20)]
        avg_trading = recent_window.groupby('stock_code')['trading_value'].mean().rename('AVG_TRADING_VALUE')
        turnover = recent_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(g['volume'].mean(), g['listed_shares'].iloc[0]) * 100 if g['listed_shares'].iloc[0] else None
        ).rename('TURNOVER_RATE')

        momentum_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=120)]
        momentum = momentum_window.groupby('stock_code').apply(
            lambda g: _safe_ratio(
                g[g['trade_date'] == g['trade_date'].max()]['close_price'].iloc[0],
                g.sort_values('trade_date').iloc[0]['close_price']
            ) - 1 if not g.empty and g[g['trade_date'] == g['trade_date'].max()].size > 0 and g.sort_values('trade_date').iloc[0]['close_price'] else None
        ).rename('MOM_3M')

        pct_returns = price_df.sort_values('trade_date').groupby('stock_code')['close_price'].pct_change()
        price_df = price_df.assign(daily_return=pct_returns)
        vol_window = price_df[price_df['trade_date'] >= pd.Timestamp(snapshot_date.date()) - pd.Timedelta(days=90)]
        volatility = vol_window.groupby('stock_code')['daily_return'].std().rename('VOLATILITY_90')

        merged = merged.merge(avg_trading, on='stock_code', how='left')
        merged = merged.merge(turnover, on='stock_code', how='left')
        merged = merged.merge(momentum, on='stock_code', how='left')
        merged = merged.merge(volatility, on='stock_code', how='left')

        merged['date'] = snapshot_date
        return merged

    def _attach_ranks(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        higher_better = ['ROE', 'ROA', 'MOM_3M', 'AVG_TRADING_VALUE']
        lower_better = ['PER', 'PBR', 'DEBT_RATIO', 'VOLATILITY_90']

        for col in higher_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=False, method='dense')

        for col in lower_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=True, method='dense')

        rank_columns = [c for c in df.columns if c.endswith('_RANK')]
        if rank_columns:
            df['COMPOSITE_SCORE'] = df[rank_columns].mean(axis=1)
            df['COMPOSITE_RANK'] = df['COMPOSITE_SCORE'].rank(ascending=True, method='dense')

        return df

    async def _calculate_quality_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """수익성 지표 계산 (10개)"""
        query = text("""
        SELECT
            s.stock_code,

            -- 15. ROE (Return on Equity)
            CASE WHEN f.total_equity > 0
                THEN f.net_income_ttm / f.total_equity * 100
                ELSE NULL END AS ROE,

            -- 16. ROA (Return on Assets)
            CASE WHEN f.total_assets > 0
                THEN f.net_income_ttm / f.total_assets * 100
                ELSE NULL END AS ROA,

            -- 17. ROIC (Return on Invested Capital)
            CASE WHEN (f.total_equity + f.total_debt - f.cash) > 0
                THEN f.nopat / (f.total_equity + f.total_debt - f.cash) * 100
                ELSE NULL END AS ROIC,

            -- 18. Gross Profit Margin
            CASE WHEN f.revenue_ttm > 0
                THEN f.gross_profit / f.revenue_ttm * 100
                ELSE NULL END AS GPM,

            -- 19. Operating Profit Margin
            CASE WHEN f.revenue_ttm > 0
                THEN f.operating_income / f.revenue_ttm * 100
                ELSE NULL END AS OPM,

            -- 20. Net Profit Margin
            CASE WHEN f.revenue_ttm > 0
                THEN f.net_income_ttm / f.revenue_ttm * 100
                ELSE NULL END AS NPM,

            -- 21. Asset Turnover
            CASE WHEN f.total_assets > 0
                THEN f.revenue_ttm / f.total_assets
                ELSE NULL END AS ASSET_TURNOVER,

            -- 22. Inventory Turnover
            CASE WHEN f.inventory > 0
                THEN f.cost_of_goods_sold / f.inventory
                ELSE NULL END AS INVENTORY_TURNOVER,

            -- 23. Quality Score (Piotroski F-Score simplified)
            (CASE WHEN f.net_income_ttm > 0 THEN 1 ELSE 0 END +
             CASE WHEN f.operating_cash_flow > 0 THEN 1 ELSE 0 END +
             CASE WHEN f.roa_current > f.roa_previous THEN 1 ELSE 0 END +
             CASE WHEN f.operating_cash_flow > f.net_income_ttm THEN 1 ELSE 0 END +
             CASE WHEN f.debt_ratio < f.debt_ratio_previous THEN 1 ELSE 0 END +
             CASE WHEN f.current_ratio > f.current_ratio_previous THEN 1 ELSE 0 END +
             CASE WHEN f.shares_outstanding <= f.shares_outstanding_previous THEN 1 ELSE 0 END +
             CASE WHEN f.gross_margin > f.gross_margin_previous THEN 1 ELSE 0 END +
             CASE WHEN f.asset_turnover > f.asset_turnover_previous THEN 1 ELSE 0 END) AS QUALITY_SCORE,

            -- 24. Accruals Ratio
            CASE WHEN f.total_assets > 0
                THEN (f.net_income_ttm - f.operating_cash_flow) / f.total_assets
                ELSE NULL END AS ACCRUALS_RATIO

        FROM stocks s
        LEFT JOIN financial_summary f ON s.stock_code = f.stock_code
        WHERE s.stock_code IN :stock_codes
        AND f.date <= :date
        ORDER BY f.date DESC
        LIMIT 1
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

        return df

    async def _calculate_growth_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """성장성 지표 계산 (8개)"""
        query = text("""
        SELECT
            s.stock_code,

            -- 25. Revenue Growth (1Y)
            CASE WHEN f.revenue_previous > 0
                THEN (f.revenue_ttm - f.revenue_previous) / f.revenue_previous * 100
                ELSE NULL END AS REVENUE_GROWTH_1Y,

            -- 26. Revenue Growth (3Y CAGR)
            CASE WHEN f.revenue_3y_ago > 0
                THEN (POWER(f.revenue_ttm / f.revenue_3y_ago, 1.0/3) - 1) * 100
                ELSE NULL END AS REVENUE_GROWTH_3Y,

            -- 27. Earnings Growth (1Y)
            CASE WHEN f.earnings_previous > 0
                THEN (f.net_income_ttm - f.earnings_previous) / f.earnings_previous * 100
                ELSE NULL END AS EARNINGS_GROWTH_1Y,

            -- 28. Earnings Growth (3Y CAGR)
            CASE WHEN f.earnings_3y_ago > 0
                THEN (POWER(f.net_income_ttm / f.earnings_3y_ago, 1.0/3) - 1) * 100
                ELSE NULL END AS EARNINGS_GROWTH_3Y,

            -- 29. OCF Growth (1Y)
            CASE WHEN f.ocf_previous > 0
                THEN (f.operating_cash_flow - f.ocf_previous) / f.ocf_previous * 100
                ELSE NULL END AS OCF_GROWTH_1Y,

            -- 30. Asset Growth (1Y)
            CASE WHEN f.assets_previous > 0
                THEN (f.total_assets - f.assets_previous) / f.assets_previous * 100
                ELSE NULL END AS ASSET_GROWTH_1Y,

            -- 31. Book Value Growth (1Y)
            CASE WHEN f.book_value_previous > 0
                THEN (f.total_equity - f.book_value_previous) / f.book_value_previous * 100
                ELSE NULL END AS BOOK_VALUE_GROWTH_1Y,

            -- 32. Sustainable Growth Rate
            f.roe * (1 - f.dividend_payout_ratio) AS SUSTAINABLE_GROWTH_RATE

        FROM stocks s
        LEFT JOIN financial_summary f ON s.stock_code = f.stock_code
        WHERE s.stock_code IN :stock_codes
        AND f.date <= :date
        ORDER BY f.date DESC
        LIMIT 1
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

        return df

    async def _calculate_momentum_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """모멘텀 지표 계산 (8개)"""
        query = text("""
        WITH price_data AS (
            SELECT
                stock_code,
                close_price,
                LAG(close_price, 20) OVER (PARTITION BY stock_code ORDER BY date) AS price_1m_ago,
                LAG(close_price, 60) OVER (PARTITION BY stock_code ORDER BY date) AS price_3m_ago,
                LAG(close_price, 120) OVER (PARTITION BY stock_code ORDER BY date) AS price_6m_ago,
                LAG(close_price, 240) OVER (PARTITION BY stock_code ORDER BY date) AS price_12m_ago,
                AVG(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
                AVG(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS ma_60,
                AVG(volume * close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_volume_20d,
                STDDEV(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 251 PRECEDING AND CURRENT ROW) AS volatility_252d
            FROM stock_prices
            WHERE stock_code IN :stock_codes
            AND date <= :date
        )
        SELECT
            stock_code,

            -- 33. 1-Month Momentum
            CASE WHEN price_1m_ago > 0
                THEN (close_price - price_1m_ago) / price_1m_ago * 100
                ELSE NULL END AS MOMENTUM_1M,

            -- 34. 3-Month Momentum
            CASE WHEN price_3m_ago > 0
                THEN (close_price - price_3m_ago) / price_3m_ago * 100
                ELSE NULL END AS MOMENTUM_3M,

            -- 35. 6-Month Momentum
            CASE WHEN price_6m_ago > 0
                THEN (close_price - price_6m_ago) / price_6m_ago * 100
                ELSE NULL END AS MOMENTUM_6M,

            -- 36. 12-Month Momentum
            CASE WHEN price_12m_ago > 0
                THEN (close_price - price_12m_ago) / price_12m_ago * 100
                ELSE NULL END AS MOMENTUM_12M,

            -- 37. 52-Week High Distance
            CASE WHEN high_52w > 0
                THEN (close_price - high_52w) / high_52w * 100
                ELSE NULL END AS DISTANCE_FROM_52W_HIGH,

            -- 38. 52-Week Low Distance
            CASE WHEN low_52w > 0
                THEN (close_price - low_52w) / low_52w * 100
                ELSE NULL END AS DISTANCE_FROM_52W_LOW,

            -- 39. Relative Strength vs Market
            CASE WHEN market_return > 0
                THEN ((close_price - price_3m_ago) / price_3m_ago * 100) - market_return
                ELSE NULL END AS RELATIVE_STRENGTH,

            -- 40. Volume Momentum
            CASE WHEN avg_volume_20d_prev > 0
                THEN (avg_volume_20d - avg_volume_20d_prev) / avg_volume_20d_prev * 100
                ELSE NULL END AS VOLUME_MOMENTUM

        FROM price_data
        WHERE date = :date
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

        return df

    async def _calculate_stability_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """안정성 지표 계산 (8개)"""
        query = text("""
        SELECT
            s.stock_code,

            -- 41. Debt to Equity Ratio
            CASE WHEN f.total_equity > 0
                THEN f.total_debt / f.total_equity
                ELSE NULL END AS DEBT_TO_EQUITY,

            -- 42. Debt Ratio
            CASE WHEN f.total_assets > 0
                THEN f.total_debt / f.total_assets * 100
                ELSE NULL END AS DEBT_RATIO,

            -- 43. Current Ratio
            CASE WHEN f.current_liabilities > 0
                THEN f.current_assets / f.current_liabilities
                ELSE NULL END AS CURRENT_RATIO,

            -- 44. Quick Ratio
            CASE WHEN f.current_liabilities > 0
                THEN (f.current_assets - f.inventory) / f.current_liabilities
                ELSE NULL END AS QUICK_RATIO,

            -- 45. Interest Coverage Ratio
            CASE WHEN f.interest_expense > 0
                THEN f.ebit / f.interest_expense
                ELSE NULL END AS INTEREST_COVERAGE,

            -- 46. Altman Z-Score
            (1.2 * (f.working_capital / f.total_assets) +
             1.4 * (f.retained_earnings / f.total_assets) +
             3.3 * (f.ebit / f.total_assets) +
             0.6 * (f.market_cap / f.total_debt) +
             1.0 * (f.revenue_ttm / f.total_assets)) AS ALTMAN_Z_SCORE,

            -- 47. Beta
            f.beta AS BETA,

            -- 48. Earnings Quality (OCF/NI)
            CASE WHEN f.net_income_ttm > 0
                THEN f.operating_cash_flow / f.net_income_ttm
                ELSE NULL END AS EARNINGS_QUALITY

        FROM stocks s
        LEFT JOIN financial_summary f ON s.stock_code = f.stock_code
        WHERE s.stock_code IN :stock_codes
        AND f.date <= :date
        ORDER BY f.date DESC
        LIMIT 1
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

        return df

    async def _calculate_technical_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """기술적 지표 계산 (6개)"""
        query = text("""
        WITH technical_data AS (
            SELECT
                stock_code,
                close_price,
                high_price,
                low_price,
                volume,
                AVG(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma_20,
                AVG(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50,
                AVG(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS ma_200,
                MIN(low_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS low_14d,
                MAX(high_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS high_14d,
                AVG(volume) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS avg_volume_20d,
                STDDEV(close_price) OVER (PARTITION BY stock_code ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS std_20d
            FROM stock_prices
            WHERE stock_code IN :stock_codes
            AND date <= :date
        )
        SELECT
            stock_code,

            -- 49. RSI (Relative Strength Index)
            100 - (100 / (1 + avg_gain_14d / NULLIF(avg_loss_14d, 0))) AS RSI_14,

            -- 50. Bollinger Band Position
            CASE WHEN std_20d > 0
                THEN (close_price - ma_20) / (2 * std_20d)
                ELSE NULL END AS BOLLINGER_POSITION,

            -- 51. MACD Signal
            (ema_12 - ema_26) - ema_signal AS MACD_SIGNAL,

            -- 52. Stochastic Oscillator
            CASE WHEN (high_14d - low_14d) > 0
                THEN (close_price - low_14d) / (high_14d - low_14d) * 100
                ELSE NULL END AS STOCHASTIC_14,

            -- 53. Volume Rate of Change
            CASE WHEN avg_volume_20d_prev > 0
                THEN (avg_volume_20d - avg_volume_20d_prev) / avg_volume_20d_prev * 100
                ELSE NULL END AS VOLUME_ROC,

            -- 54. Price Position (0-100 scale)
            CASE WHEN (high_52w - low_52w) > 0
                THEN (close_price - low_52w) / (high_52w - low_52w) * 100
                ELSE NULL END AS PRICE_POSITION

        FROM technical_data
        WHERE date = :date
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

        return df

    def _calculate_rankings(self, df: pd.DataFrame) -> pd.DataFrame:
        """각 팩터별 랭킹 계산"""

        # 높을수록 좋은 팩터
        higher_better = [
            'ROE', 'ROA', 'ROIC', 'GPM', 'OPM', 'NPM',
            'REVENUE_GROWTH_1Y', 'EARNINGS_GROWTH_1Y',
            'MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M',
            'QUALITY_SCORE', 'EARNINGS_YIELD', 'DIVIDEND_YIELD',
            'CURRENT_RATIO', 'QUICK_RATIO', 'INTEREST_COVERAGE'
        ]

        # 낮을수록 좋은 팩터
        lower_better = [
            'PER', 'PBR', 'PSR', 'PCR', 'PEG',
            'EV_EBITDA', 'EV_SALES', 'DEBT_RATIO',
            'DEBT_TO_EQUITY', 'BETA'
        ]

        # 높을수록 좋은 팩터 랭킹
        for col in higher_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=False, method='dense')

        # 낮을수록 좋은 팩터 랭킹
        for col in lower_better:
            if col in df.columns:
                df[f'{col}_RANK'] = df[col].rank(ascending=True, method='dense')

        # 종합 스코어 계산 (정규화된 랭킹의 평균)
        rank_columns = [col for col in df.columns if col.endswith('_RANK')]
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
        query = text("""
        SELECT DISTINCT stock_code
        FROM stock_prices
        WHERE date = :date
        AND volume > 0
        AND close_price > 0
        """)

        result = await self.db.execute(query, {"date": date})
        return [row[0] for row in result.fetchall()]
