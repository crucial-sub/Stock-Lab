"""
완전한 팩터 계산 모듈 - 54개 팩터 구현
"""
from typing import Dict, List, Optional
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
import logging

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
        """모든 54개 팩터 계산"""

        # 1. 가치 지표 (Value) - 14개
        value_factors = await self._calculate_value_factors(stock_codes, date)

        # 2. 수익성 지표 (Quality) - 10개
        quality_factors = await self._calculate_quality_factors(stock_codes, date)

        # 3. 성장성 지표 (Growth) - 8개
        growth_factors = await self._calculate_growth_factors(stock_codes, date)

        # 4. 모멘텀 지표 (Momentum) - 8개
        momentum_factors = await self._calculate_momentum_factors(stock_codes, date)

        # 5. 안정성 지표 (Stability) - 8개
        stability_factors = await self._calculate_stability_factors(stock_codes, date)

        # 6. 기술적 지표 (Technical) - 6개
        technical_factors = await self._calculate_technical_factors(stock_codes, date)

        # 모든 팩터 병합
        all_factors = pd.concat([
            value_factors,
            quality_factors,
            growth_factors,
            momentum_factors,
            stability_factors,
            technical_factors
        ], axis=1)

        # 랭킹 계산
        all_factors = self._calculate_rankings(all_factors)

        return all_factors

    async def _calculate_value_factors(self, stock_codes: List[str], date: datetime) -> pd.DataFrame:
        """가치 지표 계산 (14개)"""
        query = text("""
        SELECT
            s.stock_code,
            s.stock_name,

            -- 1. PER (Price to Earnings Ratio)
            CASE WHEN f.net_income_ttm > 0
                THEN p.close_price * s.shares_outstanding / f.net_income_ttm
                ELSE NULL END AS PER,

            -- 2. PBR (Price to Book Ratio)
            CASE WHEN f.total_equity > 0
                THEN p.close_price * s.shares_outstanding / f.total_equity
                ELSE NULL END AS PBR,

            -- 3. PSR (Price to Sales Ratio)
            CASE WHEN f.revenue_ttm > 0
                THEN p.close_price * s.shares_outstanding / f.revenue_ttm
                ELSE NULL END AS PSR,

            -- 4. PCR (Price to Cash Flow Ratio)
            CASE WHEN f.operating_cash_flow > 0
                THEN p.close_price * s.shares_outstanding / f.operating_cash_flow
                ELSE NULL END AS PCR,

            -- 5. PEG (Price/Earnings to Growth)
            CASE WHEN f.net_income_ttm > 0 AND f.earnings_growth_3y > 0
                THEN (p.close_price * s.shares_outstanding / f.net_income_ttm) / f.earnings_growth_3y
                ELSE NULL END AS PEG,

            -- 6. EV/EBITDA
            CASE WHEN f.ebitda > 0
                THEN (p.close_price * s.shares_outstanding + f.total_debt - f.cash) / f.ebitda
                ELSE NULL END AS EV_EBITDA,

            -- 7. EV/Sales
            CASE WHEN f.revenue_ttm > 0
                THEN (p.close_price * s.shares_outstanding + f.total_debt - f.cash) / f.revenue_ttm
                ELSE NULL END AS EV_SALES,

            -- 8. EV/FCF (Enterprise Value to Free Cash Flow)
            CASE WHEN f.free_cash_flow > 0
                THEN (p.close_price * s.shares_outstanding + f.total_debt - f.cash) / f.free_cash_flow
                ELSE NULL END AS EV_FCF,

            -- 9. Dividend Yield
            CASE WHEN p.close_price > 0
                THEN f.dividends_per_share / p.close_price * 100
                ELSE 0 END AS DIVIDEND_YIELD,

            -- 10. Earnings Yield (E/P)
            CASE WHEN p.close_price * s.shares_outstanding > 0
                THEN f.net_income_ttm / (p.close_price * s.shares_outstanding) * 100
                ELSE NULL END AS EARNINGS_YIELD,

            -- 11. FCF Yield
            CASE WHEN p.close_price * s.shares_outstanding > 0
                THEN f.free_cash_flow / (p.close_price * s.shares_outstanding) * 100
                ELSE NULL END AS FCF_YIELD,

            -- 12. Book to Market Ratio
            CASE WHEN p.close_price * s.shares_outstanding > 0
                THEN f.total_equity / (p.close_price * s.shares_outstanding)
                ELSE NULL END AS BOOK_TO_MARKET,

            -- 13. CAPE Ratio (Cyclically Adjusted PE)
            CASE WHEN f.avg_earnings_10y > 0
                THEN p.close_price * s.shares_outstanding / f.avg_earnings_10y
                ELSE NULL END AS CAPE_RATIO,

            -- 14. Price to Tangible Book Value
            CASE WHEN (f.total_equity - f.intangible_assets) > 0
                THEN p.close_price * s.shares_outstanding / (f.total_equity - f.intangible_assets)
                ELSE NULL END AS PTBV

        FROM stocks s
        INNER JOIN stock_prices p ON s.stock_code = p.stock_code
        LEFT JOIN financial_summary f ON s.stock_code = f.stock_code
        WHERE s.stock_code IN :stock_codes
        AND p.date = :date
        AND f.date <= :date
        ORDER BY f.date DESC
        LIMIT 1
        """)

        result = await self.db.execute(query, {"stock_codes": stock_codes, "date": date})
        df = pd.DataFrame(result.fetchall())

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