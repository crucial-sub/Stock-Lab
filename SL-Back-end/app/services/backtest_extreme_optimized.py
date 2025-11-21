"""
백테스트 극한 최적화 모듈 (Extreme Performance)
목표: 8-10분 → 10-20초 (30-50배 개선!)

극한 최적화 기법:
1. JIT 워밍업 (첫 실행 시간 90% 단축)
2. 메모리 맵 파일 (I/O 제거)
3. 데이터 파이프라인 (스트리밍 처리)
4. 공격적 병렬 처리 (모든 CPU 코어 활용)
5. Redis 파이프라인 + Lua 스크립트
6. DB 커넥션 풀 최적화
7. Zero-copy 데이터 전송

⚠️ 중요: 새로운 재무 팩터 추가 시 주의사항
========================================
이 파일은 성능 최적화를 위해 factor_calculator_complete.py와 별도로 재무 팩터를 계산합니다.

**새로운 재무 팩터를 추가할 때는 반드시 두 곳에 모두 추가해야 합니다:**
1. factor_calculator_complete.py (표준 경로 - 상세 계산)
2. backtest_extreme_optimized.py (최적화 경로 - 이 파일의 _calculate_financial_factors_once() 메서드)

**추가 예시:**
```python
# _calculate_financial_factors_once() 메서드 내부 (Line 487-502):
financial_factors[stock_code] = {
    'PER': per_val,
    'PBR': pbr_val,
    'PSR': psr_val,              # ← 추가된 팩터
    'ROE': roe_val,
    'ROA': roa_val,
    'DEBT_RATIO': debt_ratio,    # ← 추가된 팩터
    'OPERATING_MARGIN': operating_margin,
    'NET_MARGIN': net_margin,
}
```

**참고 문서:** docs/2025-11-21-debt-ratio-root-cause-fix.md
"""

import logging
import numpy as np
import pandas as pd
import polars as pl
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import mmap
import pickle
from pathlib import Path
import hashlib

# Polars 멀티프로세싱 데드락 방지 (fork → spawn)
multiprocessing.set_start_method('spawn', force=True)

logger = logging.getLogger(__name__)

try:
    from numba import jit, prange, njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    njit = jit
    prange = range

# 🚀 전역 JIT 워밍업 플래그 (프로세스 전체에서 한 번만 실행)
_JIT_WARMED_GLOBAL = False


def _calculate_single_date_worker(
    price_df: pd.DataFrame,
    financial_df: pd.DataFrame,
    calc_date: date,
    stock_prices_df: Optional[pd.DataFrame] = None
) -> Dict[str, Dict[str, float]]:
    """
    멀티프로세싱 워커 함수 (모듈 최상위 레벨에 있어야 pickle 가능)

    각 프로세스에서 개별 날짜의 팩터를 계산
    """
    import polars as pl

    # pandas → Polars 변환
    price_pl = pl.from_pandas(price_df) if price_df is not None else None
    financial_pl = pl.from_pandas(financial_df) if financial_df is not None else None
    stock_prices_pl = pl.from_pandas(stock_prices_df) if stock_prices_df is not None else None

    # 임시 optimizer 생성 (각 프로세스마다)
    temp_optimizer = ExtremeOptimizer()

    # 팩터 계산
    result = temp_optimizer.calculate_all_indicators_extreme(
        price_pl, financial_pl, calc_date, stock_prices_pl
    )

    return result


class ExtremeOptimizer:
    """극한 최적화 엔진"""

    def __init__(self):
        # CPU 코어를 최대한 활용
        self.n_workers = multiprocessing.cpu_count()  # 모든 코어 사용!
        self.cache_dir = Path("/tmp/backtest_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # JIT 워밍업 상태
        self.jit_warmed = False

        logger.info(f"🔥 극한 최적화 엔진 초기화: {self.n_workers}개 워커 (모든 CPU 코어)")

    async def warmup_jit_functions(self):
        """
        JIT 워밍업 (첫 실행 시간 90% 단축)

        백그라운드에서 미리 JIT 컴파일하여
        사용자가 처음 실행할 때 빠르게 시작
        """
        global _JIT_WARMED_GLOBAL

        # 🚀 전역 플래그 확인: 이미 워밍업되었거나 Numba가 없으면 스킵
        if _JIT_WARMED_GLOBAL or not NUMBA_AVAILABLE:
            if _JIT_WARMED_GLOBAL:
                logger.debug("✅ JIT 이미 워밍업됨, 스킵")
            return

        logger.info("🔥 JIT 함수 워밍업 시작...")
        start = asyncio.get_event_loop().time()

        # 더미 데이터로 JIT 컴파일 트리거
        dummy_prices = np.random.randn(100, 50).astype(np.float32)
        dummy_dates = np.arange(50)

        # 모든 JIT 함수 워밍업
        _ = self._calculate_momentum_extreme(dummy_prices, dummy_dates, 20)
        _ = self._calculate_rsi_extreme(dummy_prices, 14)
        _ = self._calculate_bollinger_extreme(dummy_prices, 20)
        _ = self._calculate_ema_extreme(dummy_prices, 12)
        _ = self._calculate_macd_extreme(dummy_prices)

        elapsed = asyncio.get_event_loop().time() - start
        _JIT_WARMED_GLOBAL = True  # 전역 플래그 설정
        self.jit_warmed = True
        logger.info(f"✅ JIT 워밍업 완료: {elapsed:.2f}초")

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_momentum_extreme(
        prices: np.ndarray,
        dates: np.ndarray,
        lookback: int
    ) -> np.ndarray:
        """
        극한 최적화 모멘텀 계산

        최적화 기법:
        - fastmath=True (부동소수점 최적화)
        - 병렬 루프 (prange)
        - 메모리 접근 최적화
        """
        n_stocks, n_days = prices.shape
        momentum = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= lookback:
                    past_price = prices[i, j - lookback]
                    current_price = prices[i, j]

                    if past_price > 1e-8:  # fastmath 최적화
                        momentum[i, j] = (current_price / past_price - 1.0) * 100.0
                    else:
                        momentum[i, j] = np.nan
                else:
                    momentum[i, j] = np.nan

        return momentum

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_rsi_extreme(
        prices: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """극한 최적화 RSI"""
        n_stocks, n_days = prices.shape
        rsi = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            # Wilder's smoothing 방식
            avg_gain = 0.0
            avg_loss = 0.0

            # 초기 평균 계산
            for j in range(1, period + 1):
                if j < n_days:
                    change = prices[i, j] - prices[i, j - 1]
                    if change > 0:
                        avg_gain += change
                    else:
                        avg_loss -= change

            avg_gain /= period
            avg_loss /= period

            # RSI 계산
            for j in range(period, n_days):
                change = prices[i, j] - prices[i, j - 1]

                if change > 0:
                    avg_gain = (avg_gain * (period - 1) + change) / period
                    avg_loss = (avg_loss * (period - 1)) / period
                else:
                    avg_gain = (avg_gain * (period - 1)) / period
                    avg_loss = (avg_loss * (period - 1) - change) / period

                if avg_loss > 1e-8:
                    rs = avg_gain / avg_loss
                    rsi[i, j] = 100.0 - (100.0 / (1.0 + rs))
                else:
                    rsi[i, j] = 100.0 if avg_gain > 0 else 50.0

            # 초기 값은 NaN
            for j in range(period):
                rsi[i, j] = np.nan

        return rsi

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_bollinger_extreme(
        prices: np.ndarray,
        window: int = 20,
        num_std: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """극한 최적화 볼린저 밴드"""
        n_stocks, n_days = prices.shape
        upper = np.empty((n_stocks, n_days), dtype=np.float32)
        middle = np.empty((n_stocks, n_days), dtype=np.float32)
        lower = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(window - 1, n_days):
                # 이동 평균 및 표준편차 (Welford's 알고리즘)
                sum_val = 0.0
                sum_sq = 0.0
                count = 0

                for k in range(j - window + 1, j + 1):
                    val = prices[i, k]
                    if not np.isnan(val):
                        sum_val += val
                        sum_sq += val * val
                        count += 1

                if count > 0:
                    mean = sum_val / count
                    variance = (sum_sq / count) - (mean * mean)
                    std = np.sqrt(variance) if variance > 0 else 0.0

                    middle[i, j] = mean
                    upper[i, j] = mean + num_std * std
                    lower[i, j] = mean - num_std * std
                else:
                    middle[i, j] = np.nan
                    upper[i, j] = np.nan
                    lower[i, j] = np.nan

            # 초기 값은 NaN
            for j in range(window - 1):
                middle[i, j] = np.nan
                upper[i, j] = np.nan
                lower[i, j] = np.nan

        return upper, middle, lower

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_ema_extreme(
        prices: np.ndarray,
        span: int
    ) -> np.ndarray:
        """극한 최적화 EMA"""
        n_stocks, n_days = prices.shape
        alpha = 2.0 / (span + 1.0)
        ema = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            ema[i, 0] = prices[i, 0]
            for j in range(1, n_days):
                ema[i, j] = alpha * prices[i, j] + (1.0 - alpha) * ema[i, j - 1]

        return ema

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_macd_extreme(
        prices: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """극한 최적화 MACD (한 번에 계산)"""
        n_stocks, n_days = prices.shape

        # EMA 12, 26 계산
        alpha_12 = 2.0 / 13.0
        alpha_26 = 2.0 / 27.0
        alpha_9 = 2.0 / 10.0

        macd_line = np.empty((n_stocks, n_days), dtype=np.float32)
        signal_line = np.empty((n_stocks, n_days), dtype=np.float32)
        histogram = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            # EMA 12
            ema_12 = prices[i, 0]
            ema_26 = prices[i, 0]

            for j in range(n_days):
                ema_12 = alpha_12 * prices[i, j] + (1.0 - alpha_12) * ema_12
                ema_26 = alpha_26 * prices[i, j] + (1.0 - alpha_26) * ema_26
                macd_line[i, j] = ema_12 - ema_26

            # Signal line (MACD의 9일 EMA)
            signal = macd_line[i, 0]
            for j in range(n_days):
                signal = alpha_9 * macd_line[i, j] + (1.0 - alpha_9) * signal
                signal_line[i, j] = signal
                histogram[i, j] = macd_line[i, j] - signal

        return macd_line, signal_line, histogram

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_52w_high_low(
        prices: np.ndarray,
        dates: np.ndarray,
        lookback: int = 250
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        52주 고저점 계산

        Returns:
            high_52w: 52주 최고가
            low_52w: 52주 최저가
        """
        n_stocks, n_days = prices.shape
        high_52w = np.empty((n_stocks, n_days), dtype=np.float32)
        low_52w = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= lookback:
                    # 과거 lookback일간의 고저점
                    high_52w[i, j] = np.max(prices[i, j-lookback:j+1])
                    low_52w[i, j] = np.min(prices[i, j-lookback:j+1])
                else:
                    # 데이터가 부족하면 현재까지의 고저점
                    high_52w[i, j] = np.max(prices[i, :j+1])
                    low_52w[i, j] = np.min(prices[i, :j+1])

        return high_52w, low_52w

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_stochastic_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Stochastic Oscillator 계산 (%K)

        %K = (현재가 - 최저가) / (최고가 - 최저가) × 100
        """
        n_stocks, n_days = close.shape
        stochastic = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period:
                    # 과거 period일간의 최고/최저
                    period_high = np.max(high[i, j-period+1:j+1])
                    period_low = np.min(low[i, j-period+1:j+1])

                    if period_high - period_low > 1e-8:
                        stochastic[i, j] = ((close[i, j] - period_low) / (period_high - period_low)) * 100.0
                    else:
                        stochastic[i, j] = 50.0  # 변동이 없으면 중립값
                else:
                    stochastic[i, j] = np.nan

        return stochastic

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_volume_roc_extreme(
        volume: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """
        Volume Rate of Change 계산

        VROC = (현재거래량 - 과거거래량) / 과거거래량 × 100
        """
        n_stocks, n_days = volume.shape
        volume_roc = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period:
                    past_volume = volume[i, j - period]
                    current_volume = volume[i, j]

                    if past_volume > 1e-8:
                        volume_roc[i, j] = ((current_volume - past_volume) / past_volume) * 100.0
                    else:
                        volume_roc[i, j] = np.nan
                else:
                    volume_roc[i, j] = np.nan

        return volume_roc

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_moving_averages_extreme(
        prices: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Multiple Moving Averages 계산 (5, 20, 60, 120, 250일)

        Returns: MA_5, MA_20, MA_60, MA_120, MA_250
        """
        n_stocks, n_days = prices.shape
        ma_5 = np.empty((n_stocks, n_days), dtype=np.float32)
        ma_20 = np.empty((n_stocks, n_days), dtype=np.float32)
        ma_60 = np.empty((n_stocks, n_days), dtype=np.float32)
        ma_120 = np.empty((n_stocks, n_days), dtype=np.float32)
        ma_250 = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                # MA_5
                if j >= 4:
                    ma_5[i, j] = np.mean(prices[i, j-4:j+1])
                else:
                    ma_5[i, j] = np.nan

                # MA_20
                if j >= 19:
                    ma_20[i, j] = np.mean(prices[i, j-19:j+1])
                else:
                    ma_20[i, j] = np.nan

                # MA_60
                if j >= 59:
                    ma_60[i, j] = np.mean(prices[i, j-59:j+1])
                else:
                    ma_60[i, j] = np.nan

                # MA_120
                if j >= 119:
                    ma_120[i, j] = np.mean(prices[i, j-119:j+1])
                else:
                    ma_120[i, j] = np.nan

                # MA_250
                if j >= 249:
                    ma_250[i, j] = np.mean(prices[i, j-249:j+1])
                else:
                    ma_250[i, j] = np.nan

        return ma_5, ma_20, ma_60, ma_120, ma_250

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_atr_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Average True Range 계산

        TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = SMA(TR, period)
        """
        n_stocks, n_days = close.shape
        atr = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period:
                    tr_sum = 0.0
                    for k in range(j - period + 1, j + 1):
                        if k > 0:
                            hl = high[i, k] - low[i, k]
                            hc = abs(high[i, k] - close[i, k-1])
                            lc = abs(low[i, k] - close[i, k-1])
                            tr_sum += max(hl, max(hc, lc))
                    atr[i, j] = tr_sum / period
                else:
                    atr[i, j] = np.nan

        return atr

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_adx_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Average Directional Index 계산

        Simplified version using DX = abs(+DI - -DI) / (+DI + -DI) * 100
        """
        n_stocks, n_days = close.shape
        adx = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period * 2:
                    plus_dm_sum = 0.0
                    minus_dm_sum = 0.0
                    tr_sum = 0.0

                    for k in range(j - period + 1, j + 1):
                        if k > 0:
                            up_move = high[i, k] - high[i, k-1]
                            down_move = low[i, k-1] - low[i, k]

                            if up_move > down_move and up_move > 0:
                                plus_dm_sum += up_move
                            elif down_move > up_move and down_move > 0:
                                minus_dm_sum += down_move

                            hl = high[i, k] - low[i, k]
                            hc = abs(high[i, k] - close[i, k-1])
                            lc = abs(low[i, k] - close[i, k-1])
                            tr_sum += max(hl, max(hc, lc))

                    if tr_sum > 1e-8:
                        plus_di = (plus_dm_sum / tr_sum) * 100
                        minus_di = (minus_dm_sum / tr_sum) * 100

                        if (plus_di + minus_di) > 1e-8:
                            adx[i, j] = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
                        else:
                            adx[i, j] = np.nan
                    else:
                        adx[i, j] = np.nan
                else:
                    adx[i, j] = np.nan

        return adx

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_aroon_extreme(
        high: np.ndarray,
        low: np.ndarray,
        period: int = 25
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Aroon Up/Down 계산

        Aroon Up = ((period - periods since high) / period) * 100
        Aroon Down = ((period - periods since low) / period) * 100
        """
        n_stocks, n_days = high.shape
        aroon_up = np.empty((n_stocks, n_days), dtype=np.float32)
        aroon_down = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period - 1:
                    # Find highest high position
                    max_high = high[i, j - period + 1]
                    max_pos = 0
                    for k in range(1, period):
                        if high[i, j - period + 1 + k] >= max_high:
                            max_high = high[i, j - period + 1 + k]
                            max_pos = k

                    # Find lowest low position
                    min_low = low[i, j - period + 1]
                    min_pos = 0
                    for k in range(1, period):
                        if low[i, j - period + 1 + k] <= min_low:
                            min_low = low[i, j - period + 1 + k]
                            min_pos = k

                    periods_since_high = period - 1 - max_pos
                    periods_since_low = period - 1 - min_pos

                    aroon_up[i, j] = ((period - periods_since_high) / period) * 100
                    aroon_down[i, j] = ((period - periods_since_low) / period) * 100
                else:
                    aroon_up[i, j] = np.nan
                    aroon_down[i, j] = np.nan

        return aroon_up, aroon_down

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_cci_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """
        Commodity Channel Index 계산

        CCI = (TP - SMA(TP)) / (0.015 * Mean Deviation)
        """
        n_stocks, n_days = close.shape
        cci = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period - 1:
                    # Calculate typical prices
                    tp_sum = 0.0
                    for k in range(j - period + 1, j + 1):
                        tp = (high[i, k] + low[i, k] + close[i, k]) / 3
                        tp_sum += tp

                    sma_tp = tp_sum / period
                    current_tp = (high[i, j] + low[i, j] + close[i, j]) / 3

                    # Calculate mean deviation
                    mad_sum = 0.0
                    for k in range(j - period + 1, j + 1):
                        tp = (high[i, k] + low[i, k] + close[i, k]) / 3
                        mad_sum += abs(tp - sma_tp)

                    mean_deviation = mad_sum / period

                    if mean_deviation > 1e-8:
                        cci[i, j] = (current_tp - sma_tp) / (0.015 * mean_deviation)
                    else:
                        cci[i, j] = np.nan
                else:
                    cci[i, j] = np.nan

        return cci

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_mfi_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Money Flow Index 계산

        MFI = 100 - (100 / (1 + Money Ratio))
        """
        n_stocks, n_days = close.shape
        mfi = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period:
                    positive_flow = 0.0
                    negative_flow = 0.0

                    for k in range(j - period + 1, j + 1):
                        if k > 0:
                            tp_curr = (high[i, k] + low[i, k] + close[i, k]) / 3
                            tp_prev = (high[i, k-1] + low[i, k-1] + close[i, k-1]) / 3
                            money_flow = tp_curr * volume[i, k]

                            if tp_curr > tp_prev:
                                positive_flow += money_flow
                            elif tp_curr < tp_prev:
                                negative_flow += money_flow

                    if negative_flow > 1e-8:
                        money_ratio = positive_flow / negative_flow
                        mfi[i, j] = 100 - (100 / (1 + money_ratio))
                    else:
                        mfi[i, j] = 100.0 if positive_flow > 0 else 50.0
                else:
                    mfi[i, j] = np.nan

        return mfi

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_williams_r_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Williams %R 계산

        %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
        """
        n_stocks, n_days = close.shape
        williams_r = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period - 1:
                    highest_high = high[i, j - period + 1]
                    lowest_low = low[i, j - period + 1]

                    for k in range(j - period + 2, j + 1):
                        if high[i, k] > highest_high:
                            highest_high = high[i, k]
                        if low[i, k] < lowest_low:
                            lowest_low = low[i, k]

                    if highest_high - lowest_low > 1e-8:
                        williams_r[i, j] = ((highest_high - close[i, j]) / (highest_high - lowest_low)) * -100
                    else:
                        williams_r[i, j] = -50.0
                else:
                    williams_r[i, j] = np.nan

        return williams_r

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_cmf_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """
        Chaikin Money Flow 계산

        CMF = Sum(MF Volume, period) / Sum(Volume, period)
        """
        n_stocks, n_days = close.shape
        cmf = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            for j in range(n_days):
                if j >= period - 1:
                    mf_volume_sum = 0.0
                    volume_sum = 0.0

                    for k in range(j - period + 1, j + 1):
                        if high[i, k] - low[i, k] > 1e-8:
                            mf_multiplier = ((close[i, k] - low[i, k]) - (high[i, k] - close[i, k])) / (high[i, k] - low[i, k])
                            mf_volume_sum += mf_multiplier * volume[i, k]
                            volume_sum += volume[i, k]

                    if volume_sum > 1e-8:
                        cmf[i, j] = mf_volume_sum / volume_sum
                    else:
                        cmf[i, j] = 0.0
                else:
                    cmf[i, j] = np.nan

        return cmf

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_obv_extreme(
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """
        On-Balance Volume 계산

        OBV cumulative: If close > prev_close: OBV += volume, else OBV -= volume
        """
        n_stocks, n_days = close.shape
        obv = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            obv[i, 0] = volume[i, 0]
            for j in range(1, n_days):
                if close[i, j] > close[i, j-1]:
                    obv[i, j] = obv[i, j-1] + volume[i, j]
                elif close[i, j] < close[i, j-1]:
                    obv[i, j] = obv[i, j-1] - volume[i, j]
                else:
                    obv[i, j] = obv[i, j-1]

        return obv

    @staticmethod
    @njit(parallel=True, cache=True, fastmath=True)
    def _calculate_vwap_extreme(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """
        Volume Weighted Average Price 계산

        VWAP = Cumulative(TP * Volume) / Cumulative(Volume)
        """
        n_stocks, n_days = close.shape
        vwap = np.empty((n_stocks, n_days), dtype=np.float32)

        for i in prange(n_stocks):
            cum_tp_volume = 0.0
            cum_volume = 0.0

            for j in range(n_days):
                tp = (high[i, j] + low[i, j] + close[i, j]) / 3
                cum_tp_volume += tp * volume[i, j]
                cum_volume += volume[i, j]

                if cum_volume > 1e-8:
                    vwap[i, j] = cum_tp_volume / cum_volume
                else:
                    vwap[i, j] = close[i, j]

        return vwap

    def calculate_all_indicators_batch_extreme(
        self,
        price_pl: pl.DataFrame,
        financial_pl: pl.DataFrame,
        calc_dates: List[date],
        stock_prices_pl: Optional[pl.DataFrame] = None,
        compute_mask: Optional[Dict[str, bool]] = None
    ) -> Dict[date, Dict[str, Dict[str, float]]]:
        """
        🚀 OPTIMIZATION 4: 멀티프로세싱 병렬 팩터 계산 + 재무 팩터 캐싱

        날짜별로 병렬 처리하여 CPU 코어 최대 활용
        Before: 순차 계산 (244일 × 0.4초 = 97초)
        After: 병렬 계산 (97초 / 10 워커 = 10초) - 10배 빠름!

        🔥 CRITICAL OPTIMIZATION: 재무 팩터 한 번만 계산!
        재무 데이터는 분기별/연도별로만 바뀌므로 매 날짜마다 계산할 필요 없음
        Before: 244일 × 238종목 × 6팩터 = 349,344번 계산
        After: 238종목 × 6팩터 = 1,428번 계산 (244배 절감!)

        Args:
            compute_mask: 계산할 팩터 마스크 (조건 사전 분석으로 얻음)
        """
        logger.info(f"🚀🚀🚀 멀티프로세싱 배치 팩터 계산 시작 ({len(calc_dates)}개 날짜, {self.n_workers}개 워커)")

        # 마스크 통계 출력
        if compute_mask:
            enabled_count = sum(1 for v in compute_mask.values() if v)
            logger.info(f"⚡ 팩터 계산 최적화 활성화: {enabled_count}/{len(compute_mask)}개 팩터만 계산")

        # 🔥 CRITICAL: 재무 팩터를 한 번만 계산!
        financial_factors_cache = {}
        if financial_pl is not None and not financial_pl.is_empty():
            logger.info(f"💰 재무 팩터 사전 계산 시작 ({len(financial_pl)}건)")
            financial_factors_cache = self._calculate_financial_factors_once(
                financial_pl, stock_prices_pl, compute_mask
            )
            logger.info(f"✅ 재무 팩터 사전 계산 완료: {len(financial_factors_cache)}개 종목")

        # 병렬 처리 여부 결정 (5개 이상 날짜면 병렬 처리)
        if len(calc_dates) < 5:
            logger.info("날짜 수가 적어 순차 처리 사용")
            all_results = {}
            for calc_date in calc_dates:
                all_results[calc_date] = self.calculate_all_indicators_extreme(
                    price_pl, None, calc_date, None  # 재무 데이터 None (캐시 사용)
                )
                # 재무 팩터 병합
                for stock_code in all_results[calc_date]:
                    if stock_code in financial_factors_cache:
                        all_results[calc_date][stock_code].update(financial_factors_cache[stock_code])
            return all_results

        # 멀티프로세싱으로 병렬 처리
        import concurrent.futures

        # Polars DataFrame을 pickle 가능한 형태로 변환 (pandas 또는 dict)
        price_dict = price_pl.to_pandas() if price_pl is not None else None
        # 재무 데이터는 전달하지 않음 (이미 계산됨)
        financial_dict = None
        stock_prices_dict = None  # 더 이상 필요 없음

        all_results = {}

        # ProcessPoolExecutor 사용 (CPU 바운드 작업)
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            # 각 날짜에 대한 작업 제출
            future_to_date = {
                executor.submit(
                    _calculate_single_date_worker,
                    price_dict,
                    financial_dict,
                    calc_date,
                    stock_prices_dict
                ): calc_date
                for calc_date in calc_dates
            }

            # 결과 수집
            for future in concurrent.futures.as_completed(future_to_date):
                calc_date = future_to_date[future]
                try:
                    result = future.result()
                    # 재무 팩터 병합
                    for stock_code in result:
                        if stock_code in financial_factors_cache:
                            result[stock_code].update(financial_factors_cache[stock_code])
                    all_results[calc_date] = result
                except Exception as e:
                    logger.error(f"날짜 {calc_date} 계산 실패: {e}")
                    all_results[calc_date] = {}

        logger.info(f"✅ 멀티프로세싱 배치 팩터 계산 완료: {len(all_results)}개 날짜")
        return all_results

    def _calculate_financial_factors_once(
        self,
        financial_pl: pl.DataFrame,
        stock_prices_pl: Optional[pl.DataFrame] = None,
        compute_mask: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        🔥 재무 팩터를 한 번만 계산 (모든 날짜에서 재사용)

        재무 데이터는 분기별/연도별로만 바뀌므로 매 날짜마다 계산할 필요 없음
        이 함수는 전체 백테스트 기간 동안 딱 1번만 호출됨

        Args:
            financial_pl: 재무 데이터
            stock_prices_pl: 시가총액 데이터
            compute_mask: 계산할 팩터 마스크 (None이면 모든 팩터 계산)
        """
        financial_factors = {}

        # 마스크가 없으면 모든 팩터 계산
        if compute_mask is None:
            compute_mask = {}

        # 헬퍼 함수: 팩터 계산 필요 여부 확인
        def should_compute(factor_name: str) -> bool:
            """팩터를 계산해야 하는지 확인 (마스크가 비어있으면 모두 계산)"""
            if not compute_mask:  # 마스크 없음 = 모든 팩터 계산
                return True
            return compute_mask.get(factor_name, False)

        # 종목별 최신 재무 데이터
        stocks = financial_pl.select('stock_code').unique().to_numpy().flatten()

        # 시가총액 데이터 딕셔너리 생성
        stock_info_dict = {}
        if stock_prices_pl is not None and not stock_prices_pl.is_empty():
            # 각 종목별 최신 시가총액 (날짜 상관없이 최신값 사용)
            for row in stock_prices_pl.sort(by=['company_id', 'trade_date'], descending=[False, True]).iter_rows(named=True):
                stock_code = row.get('stock_code')
                if stock_code and stock_code not in stock_info_dict:
                    stock_info_dict[stock_code] = {
                        'listed_shares': row.get('listed_shares'),
                        'market_cap': row.get('market_cap')
                    }

        count = 0
        for stock_code in stocks:
            stock_financial = financial_pl.filter(pl.col('stock_code') == stock_code)

            if not stock_financial.is_empty():
                # 최신 2개 재무 데이터 (성장률 계산용)
                recent_data = stock_financial.sort(by='fiscal_year', descending=True).limit(2)

                if len(recent_data) > 0:
                    # 최신 데이터
                    row = recent_data.to_dicts()[0]

                    # 이전 연도 데이터 (성장률 계산용)
                    previous_row = recent_data.to_dicts()[1] if len(recent_data) > 1 else None

                    # 재무 데이터 추출 (한글 컬럼명)
                    net_income = row.get('당기순이익')
                    revenue = row.get('매출액')
                    operating_income = row.get('영업이익')
                    total_equity = row.get('자본총계')
                    total_assets = row.get('자산총계')
                    total_debt = row.get('부채총계')
                    gross_profit = row.get('매출총이익')

                    # ROE = 당기순이익 / 자본총계 × 100
                    roe_val = np.nan
                    if should_compute('ROE'):
                        if net_income is not None and total_equity is not None and total_equity > 0:
                            roe_val = (float(net_income) / float(total_equity)) * 100

                    # ROA = 당기순이익 / 자산총계 × 100
                    roa_val = np.nan
                    if should_compute('ROA'):
                        if net_income is not None and total_assets is not None and total_assets > 0:
                            roa_val = (float(net_income) / float(total_assets)) * 100

                    # 영업이익률 = 영업이익 / 매출액 × 100
                    operating_margin = np.nan
                    if should_compute('OPERATING_MARGIN'):
                        if operating_income is not None and revenue is not None and revenue > 0:
                            operating_margin = (float(operating_income) / float(revenue)) * 100

                    # 순이익률 = 당기순이익 / 매출액 × 100
                    net_margin = np.nan
                    if should_compute('NET_MARGIN') or should_compute('NPM'):
                        if net_income is not None and revenue is not None and revenue > 0:
                            net_margin = (float(net_income) / float(revenue)) * 100

                    # 부채비율 = 부채총계 / 자본총계 × 100
                    debt_ratio = np.nan
                    if total_debt is not None and total_equity is not None and total_equity > 0:
                        debt_ratio = (float(total_debt) / float(total_equity)) * 100

                    # === 성장률 계산 (이전 연도 데이터 필요) ===
                    operating_income_growth = np.nan
                    gross_profit_growth = np.nan
                    revenue_growth_1y = np.nan
                    earnings_growth_1y = np.nan

                    if previous_row is not None:
                        # OPERATING_INCOME_GROWTH: 영업이익 성장률
                        prev_operating_income = previous_row.get('영업이익')
                        if operating_income is not None and prev_operating_income is not None and prev_operating_income > 0:
                            operating_income_growth = ((float(operating_income) - float(prev_operating_income)) / float(prev_operating_income)) * 100

                        # GROSS_PROFIT_GROWTH: 매출총이익 성장률
                        prev_gross_profit = previous_row.get('매출총이익')
                        if gross_profit is not None and prev_gross_profit is not None and prev_gross_profit > 0:
                            gross_profit_growth = ((float(gross_profit) - float(prev_gross_profit)) / float(prev_gross_profit)) * 100

                        # REVENUE_GROWTH_1Y: 매출 성장률 (1년)
                        prev_revenue = previous_row.get('매출액')
                        if revenue is not None and prev_revenue is not None and prev_revenue > 0:
                            revenue_growth_1y = ((float(revenue) - float(prev_revenue)) / float(prev_revenue)) * 100

                        # EARNINGS_GROWTH_1Y: 순이익 성장률 (1년)
                        prev_net_income = previous_row.get('당기순이익')
                        if net_income is not None and prev_net_income is not None and prev_net_income > 0:
                            earnings_growth_1y = ((float(net_income) - float(prev_net_income)) / float(prev_net_income)) * 100

                    # PBR, PER 계산 (시가총액 활용)
                    pbr_val = np.nan
                    per_val = np.nan

                    stock_info = stock_info_dict.get(stock_code)
                    if stock_info:
                        market_cap = stock_info.get('market_cap')

                        if market_cap and market_cap > 0:
                            # PBR = 시가총액 / 자본총계
                            if total_equity is not None and total_equity > 0:
                                pbr_val = float(market_cap) / float(total_equity)

                            # PER = 시가총액 / 당기순이익
                            if net_income is not None and net_income > 0:
                                per_val = float(market_cap) / float(net_income)

                    # PSR: Price to Sales Ratio = 시가총액 / 매출액
                    psr_val = np.nan
                    revenue = row.get('매출액')
                    if market_cap is not None and revenue is not None and revenue > 0:
                        psr_val = float(market_cap) / float(revenue)

                    # === Phase 2-A 긴급 팩터 추가 ===

                    # FCF_YIELD: 잉여현금흐름 수익률 = (OCF - ICF) / 시가총액 * 100
                    fcf_yield = np.nan
                    ocf = row.get('영업활동현금흐름')
                    icf = row.get('투자활동현금흐름')
                    if market_cap is not None and ocf is not None and icf is not None and market_cap > 0:
                        fcf = float(ocf) - abs(float(icf))  # 투자는 보통 음수
                        fcf_yield = (fcf / float(market_cap)) * 100

                    # CURRENT_RATIO: 유동비율 = 유동자산 / 유동부채
                    current_ratio = np.nan
                    current_assets = row.get('유동자산')
                    current_liabilities = row.get('유동부채')
                    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
                        current_ratio = float(current_assets) / float(current_liabilities)

                    # === Phase 2: 추가 재무 팩터 (10개) ===

                    # GPM: 매출총이익률 = (매출액 - 매출원가) / 매출액 * 100
                    gpm = np.nan
                    revenue = row.get('매출액')
                    cogs = row.get('매출원가', 0)
                    if revenue is not None and revenue > 0:
                        gpm = ((float(revenue) - float(cogs)) / float(revenue)) * 100

                    # NPM: 순이익률 = 당기순이익 / 매출액 * 100
                    npm = np.nan
                    if revenue is not None and net_income is not None and revenue > 0:
                        npm = (float(net_income) / float(revenue)) * 100

                    # QUICK_RATIO: 당좌비율 = (유동자산 - 재고자산) / 유동부채
                    quick_ratio = np.nan
                    inventory = row.get('재고자산', 0)
                    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
                        quick_ratio = (float(current_assets) - float(inventory)) / float(current_liabilities)

                    # CASH_RATIO: 현금비율 = 현금및현금성자산 / 유동부채
                    cash_ratio = np.nan
                    cash = row.get('현금및현금성자산')
                    if cash is not None and current_liabilities is not None and current_liabilities > 0:
                        cash_ratio = float(cash) / float(current_liabilities)

                    # DEBT_TO_EQUITY: 부채자본비율 = 부채총계 / 자본총계
                    debt_to_equity = np.nan
                    total_debt = row.get('부채총계')
                    if total_debt is not None and total_equity is not None and total_equity > 0:
                        debt_to_equity = float(total_debt) / float(total_equity)

                    # EQUITY_RATIO: 자기자본비율 = 자본총계 / 자산총계 * 100
                    equity_ratio = np.nan
                    total_assets = row.get('자산총계')
                    if total_equity is not None and total_assets is not None and total_assets > 0:
                        equity_ratio = (float(total_equity) / float(total_assets)) * 100

                    # INTEREST_COVERAGE: 이자보상배율 = 영업이익 / 이자비용
                    interest_coverage = np.nan
                    operating_income = row.get('영업이익')
                    interest_expense = row.get('이자비용')
                    if operating_income is not None and interest_expense is not None and interest_expense > 0:
                        interest_coverage = float(operating_income) / float(interest_expense)

                    # WORKING_CAPITAL_RATIO: 운전자본비율 = (유동자산 - 유동부채) / 자산총계 * 100
                    working_capital_ratio = np.nan
                    if current_assets is not None and current_liabilities is not None and total_assets is not None and total_assets > 0:
                        working_capital_ratio = ((float(current_assets) - float(current_liabilities)) / float(total_assets)) * 100

                    # OCF_RATIO: 영업현금흐름비율 = 영업활동현금흐름 / 매출액 * 100
                    ocf_ratio = np.nan
                    if ocf is not None and revenue is not None and revenue > 0:
                        ocf_ratio = (float(ocf) / float(revenue)) * 100

                    # ASSET_TURNOVER: 자산회전율 = 매출액 / 자산총계
                    asset_turnover = np.nan
                    if revenue is not None and total_assets is not None and total_assets > 0:
                        asset_turnover = float(revenue) / float(total_assets)

                    # === Phase 2-B: 부분 구현 재무 팩터 (7개) ===

                    # OPM: 영업이익률 = 영업이익 / 매출액 * 100 (OPERATING_MARGIN과 동일)
                    opm = operating_margin  # 이미 위에서 계산됨

                    # QUALITY_SCORE: 품질점수 (Piotroski F-Score 간단 버전)
                    quality_score = 0
                    # 1. ROA > 0
                    if net_income is not None and total_assets is not None and total_assets > 0 and net_income > 0:
                        quality_score += 1
                    # 2. OCF > 0
                    if ocf is not None and ocf > 0:
                        quality_score += 1
                    # 3. ROA 증가 (이전 연도 데이터 필요)
                    if previous_row is not None:
                        prev_net_income = previous_row.get('당기순이익')
                        prev_total_assets = previous_row.get('자산총계')
                        if all(v is not None for v in [net_income, total_assets, prev_net_income, prev_total_assets]):
                            if prev_total_assets > 0 and total_assets > 0:
                                current_roa = float(net_income) / float(total_assets)
                                prev_roa = float(prev_net_income) / float(prev_total_assets)
                                if current_roa > prev_roa:
                                    quality_score += 1

                    # ACCRUALS_RATIO: 발생액 비율 = (당기순이익 - 영업활동현금흐름) / 자산총계 * 100
                    accruals_ratio = np.nan
                    if net_income is not None and ocf is not None and total_assets is not None and total_assets > 0:
                        accruals_ratio = ((float(net_income) - float(ocf)) / float(total_assets)) * 100

                    # ASSET_GROWTH_1Y: 자산증가율 = (당기자산 - 전기자산) / 전기자산 * 100
                    asset_growth_1y = np.nan
                    if previous_row is not None:
                        prev_total_assets = previous_row.get('자산총계')
                        if total_assets is not None and prev_total_assets is not None and prev_total_assets > 0:
                            asset_growth_1y = ((float(total_assets) - float(prev_total_assets)) / float(prev_total_assets)) * 100

                    # ALTMAN_Z_SCORE: Altman Z-Score (파산 예측 모델)
                    # Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
                    # X1 = 운전자본 / 자산총계
                    # X2 = 이익잉여금 / 자산총계
                    # X3 = 영업이익 / 자산총계
                    # X4 = 시가총액 / 부채총계
                    # X5 = 매출액 / 자산총계
                    altman_z_score = np.nan
                    working_capital = (row.get('유동자산', 0) or 0) - (row.get('유동부채', 0) or 0)
                    retained_earnings = row.get('이익잉여금', 0) or 0
                    total_debt = row.get('부채총계')

                    stock_info = stock_info_dict.get(stock_code)
                    market_cap = stock_info.get('market_cap') if stock_info else None

                    if total_assets is not None and total_assets > 0 and operating_income is not None and revenue is not None:
                        x1 = float(working_capital) / float(total_assets)
                        x2 = float(retained_earnings) / float(total_assets)
                        x3 = float(operating_income) / float(total_assets)
                        x4 = 0
                        if market_cap is not None and total_debt is not None and total_debt > 0:
                            x4 = float(market_cap) / float(total_debt)
                        x5 = float(revenue) / float(total_assets)
                        altman_z_score = 1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5

                    # EARNINGS_QUALITY: 이익품질 = 영업활동현금흐름 / 당기순이익 * 100
                    earnings_quality = np.nan
                    if ocf is not None and net_income is not None and net_income != 0:
                        earnings_quality = (float(ocf) / float(net_income)) * 100

                    # === NEW: 15 Missing Factors Implementation ===

                    # Part 1: 3-Year Growth Factors (2개) - Fix implementation
                    revenue_growth_3y = np.nan
                    earnings_growth_3y = np.nan
                    if len(recent_data) > 3:
                        # 3년 전 데이터 (4번째 row)
                        three_year_data = recent_data.to_dicts()[3]
                        rev_3y = three_year_data.get('매출액')
                        if revenue is not None and rev_3y is not None and rev_3y > 0:
                            revenue_growth_3y = ((float(revenue) - float(rev_3y)) / float(rev_3y)) * 100

                        earn_3y = three_year_data.get('당기순이익')
                        if net_income is not None and earn_3y is not None and earn_3y > 0:
                            earnings_growth_3y = ((float(net_income) - float(earn_3y)) / float(earn_3y)) * 100

                    # Part 2: Value Factors (5개)
                    # PEG: PER / earnings_growth_1y (calculated later after merging with growth data)
                    peg = np.nan
                    if per_val is not None and earnings_growth_1y is not None and earnings_growth_1y > 0:
                        peg = per_val / earnings_growth_1y

                    # EV_FCF: Enterprise Value / Free Cash Flow
                    ev_fcf = np.nan
                    if market_cap is not None and total_debt is not None and ocf is not None:
                        icf = row.get('투자활동현금흐름')
                        if icf is not None:
                            ev = float(market_cap) + float(total_debt) - float(cash or 0)
                            fcf = float(ocf) - abs(float(icf))
                            if fcf != 0:
                                ev_fcf = ev / fcf

                    # DIVIDEND_YIELD: 배당수익률 (데이터 없음)
                    dividend_yield = np.nan

                    # CAPE_RATIO: Cyclically Adjusted PE (3년 평균 EPS로 근사)
                    cape_ratio = np.nan
                    if market_cap is not None and len(recent_data) >= 3:
                        avg_eps = sum([d.get('당기순이익', 0) or 0 for d in recent_data.to_dicts()[:3]]) / 3
                        if avg_eps > 0:
                            cape_ratio = float(market_cap) / avg_eps

                    # PTBV: Price to Tangible Book Value
                    ptbv = np.nan
                    intangible_assets = row.get('무형자산', 0)
                    if market_cap is not None and total_equity is not None:
                        tangible_bv = float(total_equity) - float(intangible_assets or 0)
                        if tangible_bv > 0:
                            ptbv = float(market_cap) / tangible_bv

                    # Part 3: Profitability Factors (2개)
                    # ROIC: Return on Invested Capital
                    roic = np.nan
                    tax_expense = row.get('법인세비용')
                    if operating_income is not None and total_equity is not None:
                        tax_rate = 0
                        if tax_expense and net_income and (net_income + tax_expense) > 0:
                            tax_rate = float(tax_expense) / (float(net_income) + float(tax_expense))
                        nopat = float(operating_income) * (1 - tax_rate)
                        invested_capital = float(total_equity) + float(total_debt or 0)
                        if invested_capital > 0:
                            roic = (nopat / invested_capital) * 100

                    # INVENTORY_TURNOVER: 재고자산회전율
                    inventory_turnover = np.nan
                    cogs = row.get('매출원가')
                    inventory = row.get('재고자산')
                    if cogs is not None and inventory is not None and inventory > 0:
                        inventory_turnover = float(cogs) / float(inventory)

                    # Part 4: Growth Factors (3개)
                    # OCF_GROWTH_1Y: Operating Cash Flow 1-year growth
                    ocf_growth_1y = np.nan
                    if previous_row is not None and ocf is not None:
                        prev_ocf = previous_row.get('영업활동현금흐름')
                        if prev_ocf is not None and prev_ocf > 0:
                            ocf_growth_1y = ((float(ocf) - float(prev_ocf)) / float(prev_ocf)) * 100

                    # BOOK_VALUE_GROWTH_1Y: Book value per share 1-year growth
                    book_value_growth_1y = np.nan
                    if previous_row is not None and total_equity is not None:
                        prev_equity = previous_row.get('자본총계')
                        if prev_equity is not None and prev_equity > 0:
                            book_value_growth_1y = ((float(total_equity) - float(prev_equity)) / float(prev_equity)) * 100

                    # SUSTAINABLE_GROWTH_RATE: 지속가능성장률 = ROE * (1 - 배당성향)
                    sustainable_growth_rate = np.nan
                    if roe_val is not None and not np.isnan(roe_val):
                        sustainable_growth_rate = roe_val * 0.7  # 유보율 70% 가정

                    # Part 5: Momentum/Technical Factors (3개) - will be calculated in price data section
                    # RELATIVE_STRENGTH, VOLUME_MOMENTUM, BETA는 가격 데이터 필요
                    relative_strength = np.nan
                    volume_momentum = np.nan
                    beta = np.nan

                    # === NEW: 40 Additional Factors ===

                    # Valuation Factors (5개)
                    # GRAHAM_NUMBER: Graham Number = sqrt(22.5 * EPS * BVPS)
                    graham_number = np.nan
                    listed_shares = stock_info.get('listed_shares') if stock_info else None
                    if net_income is not None and total_equity is not None and listed_shares and listed_shares > 0:
                        eps = float(net_income) / float(listed_shares)
                        bvps = float(total_equity) / float(listed_shares)
                        if eps > 0 and bvps > 0:
                            graham_number = np.sqrt(22.5 * eps * bvps)

                    # GREENBLATT_RANK: Placeholder (requires ranking across all stocks)
                    greenblatt_rank = np.nan

                    # MAGIC_FORMULA: Placeholder (requires ranking across all stocks)
                    magic_formula = np.nan

                    # PRICE_TO_FCF: Price to FCF = Market Cap / Free Cash Flow
                    price_to_fcf = np.nan
                    if market_cap is not None and ocf is not None and icf is not None:
                        fcf = float(ocf) - abs(float(icf))
                        if fcf != 0:
                            price_to_fcf = float(market_cap) / fcf

                    # PS_RATIO: Same as PSR (duplicate)
                    ps_ratio = psr_val

                    # Composite Factors (3개)
                    # ENTERPRISE_YIELD: EBIT / EV * 100
                    enterprise_yield = np.nan
                    if market_cap is not None and total_debt is not None and operating_income is not None:
                        ev_calc = float(market_cap) + float(total_debt) - float(cash or 0)
                        if ev_calc != 0:
                            enterprise_yield = (float(operating_income) / ev_calc) * 100

                    # PIOTROSKI_F_SCORE: Piotroski F-Score (simplified 0-9)
                    piotroski_score = 0
                    if net_income and total_assets and float(net_income) > 0:
                        piotroski_score += 1
                    if ocf and float(ocf) > 0:
                        piotroski_score += 1
                    if ocf and net_income and float(ocf) > float(net_income):
                        piotroski_score += 1
                    if current_assets and current_liabilities and float(current_liabilities) > 0:
                        if float(current_assets) / float(current_liabilities) > 1:
                            piotroski_score += 1
                    if total_debt and total_assets:
                        if float(total_debt) / float(total_assets) < 0.5:
                            piotroski_score += 1
                    if net_income and float(net_income) > 0:
                        piotroski_score += 2

                    # SHAREHOLDER_YIELD: No data available
                    shareholder_yield = np.nan

                    # Dividend Factors (2개)
                    dividend_growth_3y = np.nan  # No data
                    dividend_growth_yoy = np.nan  # No data

                    # Duplicate/Alias Factors (9개)
                    debtratio = debt_ratio
                    dividendyield = dividend_yield
                    earnings_growth_alias = earnings_growth_1y
                    operating_income_growth_yoy = operating_income_growth
                    peg_ratio_alias = peg
                    revenue_growth_alias = revenue_growth_1y
                    sma = np.nan  # Will be calculated in price section as MA_20

                    # === Phase 3: 추가 가치/변동성 팩터 (10개) ===

                    # PCR: Price to Cashflow Ratio = 시가총액 / 영업활동현금흐름
                    pcr = np.nan
                    if market_cap is not None and ocf is not None and ocf > 0:
                        pcr = float(market_cap) / float(ocf)

                    # EARNINGS_YIELD: 이익수익률 = 당기순이익 / 시가총액 * 100
                    earnings_yield = np.nan
                    if net_income is not None and market_cap is not None and market_cap > 0:
                        earnings_yield = (float(net_income) / float(market_cap)) * 100

                    # BOOK_TO_MARKET: PBR의 역수 = 자본총계 / 시가총액
                    book_to_market = np.nan
                    if total_equity is not None and market_cap is not None and market_cap > 0:
                        book_to_market = float(total_equity) / float(market_cap)

                    # EV: Enterprise Value = 시가총액 + 부채총계 - 현금
                    ev = np.nan
                    total_debt = row.get('부채총계')
                    cash = row.get('현금및현금성자산', 0)
                    if market_cap is not None and total_debt is not None:
                        ev = float(market_cap) + float(total_debt) - float(cash or 0)

                    # EV_SALES: EV / 매출액
                    ev_sales = np.nan
                    if ev is not None and revenue is not None and revenue > 0:
                        ev_sales = ev / float(revenue)

                    # EV_EBITDA: EV / 영업이익 (EBITDA 근사)
                    ev_ebitda = np.nan
                    operating_income = row.get('영업이익')
                    if ev is not None and operating_income is not None and operating_income > 0:
                        ev_ebitda = ev / float(operating_income)

                    # VOLATILITY_20D, 60D, 90D는 기술적 지표 섹션에서 계산
                    # (여기서는 placeholder)
                    volatility_20d = np.nan
                    volatility_60d = np.nan
                    volatility_90d = np.nan

                    # VOLUME_RATIO_20D는 기술적 지표 섹션에서 계산
                    volume_ratio_20d = np.nan

                    # MARKET_CAP: 시가총액 (이미 있음)
                    market_cap_val = market_cap if market_cap is not None else np.nan

                    financial_factors[stock_code] = {
                        'PER': per_val,
                        'PBR': pbr_val,
                        'PSR': psr_val,
                        'ROE': roe_val,
                        'ROA': roa_val,
                        'DEBT_RATIO': debt_ratio,
                        'OPERATING_MARGIN': operating_margin,
                        'NET_MARGIN': net_margin,
                        # 성장률 팩터 (Phase 1 완료)
                        'OPERATING_INCOME_GROWTH': operating_income_growth,
                        'GROSS_PROFIT_GROWTH': gross_profit_growth,
                        'REVENUE_GROWTH_1Y': revenue_growth_1y,
                        'EARNINGS_GROWTH_1Y': earnings_growth_1y,
                        # Phase 2-A 긴급 팩터
                        'FCF_YIELD': fcf_yield,
                        'CURRENT_RATIO': current_ratio,
                        # Phase 2 재무 팩터
                        'GPM': gpm,
                        'NPM': npm,
                        'QUICK_RATIO': quick_ratio,
                        'CASH_RATIO': cash_ratio,
                        'DEBT_TO_EQUITY': debt_to_equity,
                        'EQUITY_RATIO': equity_ratio,
                        'INTEREST_COVERAGE': interest_coverage,
                        'WORKING_CAPITAL_RATIO': working_capital_ratio,
                        'OCF_RATIO': ocf_ratio,
                        'ASSET_TURNOVER': asset_turnover,
                        # Phase 3 팩터
                        'PCR': pcr,
                        'EARNINGS_YIELD': earnings_yield,
                        'BOOK_TO_MARKET': book_to_market,
                        'EV_SALES': ev_sales,
                        'EV_EBITDA': ev_ebitda,
                        'VOLATILITY_20D': volatility_20d,
                        'VOLATILITY_60D': volatility_60d,
                        'VOLATILITY_90D': volatility_90d,
                        'VOLUME_RATIO_20D': volume_ratio_20d,
                        'MARKET_CAP': market_cap_val,
                        # Phase 2-B: 부분 구현 재무 팩터 (7개)
                        'OPM': opm,
                        'QUALITY_SCORE': quality_score,
                        'ACCRUALS_RATIO': accruals_ratio,
                        'ASSET_GROWTH_1Y': asset_growth_1y,
                        'ALTMAN_Z_SCORE': altman_z_score,
                        'EARNINGS_QUALITY': earnings_quality,
                        # NEW: 15 Missing Factors
                        'REVENUE_GROWTH_3Y': revenue_growth_3y,
                        'EARNINGS_GROWTH_3Y': earnings_growth_3y,
                        'PEG': peg,
                        'EV_FCF': ev_fcf,
                        'DIVIDEND_YIELD': dividend_yield,
                        'CAPE_RATIO': cape_ratio,
                        'PTBV': ptbv,
                        'ROIC': roic,
                        'INVENTORY_TURNOVER': inventory_turnover,
                        'OCF_GROWTH_1Y': ocf_growth_1y,
                        'BOOK_VALUE_GROWTH_1Y': book_value_growth_1y,
                        'SUSTAINABLE_GROWTH_RATE': sustainable_growth_rate,
                        'RELATIVE_STRENGTH': relative_strength,
                        'VOLUME_MOMENTUM': volume_momentum,
                        'BETA': beta,
                        # === NEW: 40 Additional Factors ===
                        'GRAHAM_NUMBER': graham_number,
                        'GREENBLATT_RANK': greenblatt_rank,
                        'MAGIC_FORMULA': magic_formula,
                        'PRICE_TO_FCF': price_to_fcf,
                        'PS_RATIO': ps_ratio,
                        'ENTERPRISE_YIELD': enterprise_yield,
                        'PIOTROSKI_F_SCORE': piotroski_score,
                        'SHAREHOLDER_YIELD': shareholder_yield,
                        'DIVIDEND_GROWTH_3Y': dividend_growth_3y,
                        'DIVIDEND_GROWTH_YOY': dividend_growth_yoy,
                        'DEBTRATIO': debtratio,
                        'DIVIDENDYIELD': dividendyield,
                        'EARNINGS_GROWTH': earnings_growth_alias,
                        'OPERATING_INCOME_GROWTH_YOY': operating_income_growth_yoy,
                        'PEG_RATIO': peg_ratio_alias,
                        'REVENUE_GROWTH': revenue_growth_alias,
                        'SMA': sma,
                        # Momentum/price-based factors (calculated in price section):
                        # RETURN_1M, RETURN_3M, RETURN_6M, RETURN_12M, RET_3D, RET_8D
                        # DAYS_FROM_52W_HIGH, DAYS_FROM_52W_LOW, WEEK_52_POSITION
                        # Risk/Volatility factors (calculated in price section):
                        # HISTORICAL_VOLATILITY_20, HISTORICAL_VOLATILITY_60, PARKINSON_VOLATILITY
                        # DOWNSIDE_VOLATILITY, MAX_DRAWDOWN, SHARPE_RATIO, SORTINO_RATIO
                        # Microstructure factors (calculated in price section):
                        # AMIHUD_ILLIQUIDITY, EASE_OF_MOVEMENT, FORCE_INDEX, INTRADAY_VOLATILITY, VOLUME_PRICE_TREND
                    }

                    # === ADDITIONAL MISSING FACTORS ===

                    # Cash Flow Factors (8개)
                    # CAPEX_TO_OCF: CAPEX to Operating Cash Flow ratio
                    capex_to_ocf = np.nan
                    cfi = row.get('투자활동현금흐름')
                    if ocf is not None and cfi is not None and ocf != 0:
                        capex_to_ocf = abs(float(cfi)) / float(ocf)

                    # CAPEX_TO_SALES: CAPEX to Sales ratio
                    capex_to_sales = np.nan
                    if revenue is not None and cfi is not None and revenue > 0:
                        capex_to_sales = abs(float(cfi)) / float(revenue)

                    # CFI_TO_ASSETS: Investing Cash Flow to Assets ratio
                    cfi_to_assets = np.nan
                    if cfi is not None and total_assets is not None and total_assets > 0:
                        cfi_to_assets = float(cfi) / float(total_assets)

                    # CFO_TO_SALES: Operating Cash Flow to Sales ratio (same as OCF_RATIO)
                    cfo_to_sales = ocf_ratio

                    # FCF_MARGIN: Free Cash Flow Margin = FCF / Revenue * 100
                    fcf_margin = np.nan
                    if revenue is not None and ocf is not None and cfi is not None and revenue > 0:
                        fcf = float(ocf) - abs(float(cfi))
                        fcf_margin = (fcf / float(revenue)) * 100

                    # FCF_TO_SALES: Free Cash Flow to Sales (same as FCF_MARGIN)
                    fcf_to_sales = fcf_margin

                    # FREE_CASH_FLOW: Free Cash Flow = OCF - ICF
                    free_cash_flow = np.nan
                    if ocf is not None and cfi is not None:
                        free_cash_flow = float(ocf) - abs(float(cfi))

                    # CFF_RATIO: Financing Cash Flow ratio
                    cff_ratio = np.nan
                    cff = row.get('재무활동현금흐름')
                    if cff is not None and revenue is not None and revenue > 0:
                        cff_ratio = (float(cff) / float(revenue)) * 100

                    # Profitability/Efficiency Factors (9개)
                    # EBITDA_MARGIN: EBITDA Margin (영업이익 + 감가상각비로 근사)
                    ebitda_margin = np.nan
                    depreciation = row.get('감가상각비', 0)
                    if operating_income is not None and revenue is not None and revenue > 0:
                        ebitda = float(operating_income) + float(depreciation or 0)
                        ebitda_margin = (ebitda / float(revenue)) * 100

                    # DUPONT_ROE: DuPont ROE = Net Margin * Asset Turnover * Equity Multiplier
                    dupont_roe = np.nan
                    if npm is not None and asset_turnover is not None and total_equity is not None and total_assets is not None and total_equity > 0:
                        equity_mult = float(total_assets) / float(total_equity)
                        dupont_roe = (npm / 100) * asset_turnover * equity_mult * 100

                    # EQUITY_MULTIPLIER: already calculated above
                    equity_multiplier_val = np.nan
                    if total_assets is not None and total_equity is not None and total_equity > 0:
                        equity_multiplier_val = float(total_assets) / float(total_equity)

                    # FINANCIAL_LEVERAGE: same as EQUITY_MULTIPLIER
                    financial_leverage = equity_multiplier_val

                    # FIXED_ASSET_TURNOVER: Sales / Fixed Assets
                    fixed_asset_turnover = np.nan
                    fixed_assets = row.get('비유동자산')
                    if revenue is not None and fixed_assets is not None and fixed_assets > 0:
                        fixed_asset_turnover = float(revenue) / float(fixed_assets)

                    # OPERATING_LEVERAGE: % change in Operating Income / % change in Revenue
                    operating_leverage = np.nan
                    if previous_row is not None and operating_income_growth is not None and revenue_growth_1y is not None and revenue_growth_1y != 0:
                        operating_leverage = operating_income_growth / revenue_growth_1y

                    # RECEIVABLES_TURNOVER: Sales / Receivables
                    receivables_turnover = np.nan
                    receivables = row.get('매출채권')
                    if revenue is not None and receivables is not None and receivables > 0:
                        receivables_turnover = float(revenue) / float(receivables)

                    # WORKING_CAPITAL_TURNOVER: Sales / Working Capital
                    working_capital_turnover = np.nan
                    if revenue is not None and current_assets is not None and current_liabilities is not None:
                        working_capital = float(current_assets) - float(current_liabilities)
                        if working_capital > 0:
                            working_capital_turnover = float(revenue) / working_capital

                    # Growth Factors (8개 - some already implemented)
                    # ASSET_GROWTH_YOY: same as ASSET_GROWTH_1Y (already implemented)
                    asset_growth_yoy = asset_growth_1y

                    # EPS_GROWTH_YOY: EPS growth year over year
                    eps_growth_yoy = np.nan
                    if previous_row is not None and listed_shares and listed_shares > 0:
                        prev_net_income = previous_row.get('당기순이익')
                        if net_income is not None and prev_net_income is not None and prev_net_income > 0:
                            eps_curr = float(net_income) / float(listed_shares)
                            eps_prev = float(prev_net_income) / float(listed_shares)
                            eps_growth_yoy = ((eps_curr - eps_prev) / eps_prev) * 100

                    # NET_INCOME_GROWTH_YOY: same as EARNINGS_GROWTH_1Y
                    net_income_growth_yoy = earnings_growth_1y

                    # REVENUE_GROWTH_QOQ: Quarter over Quarter (need quarterly data - set to nan)
                    revenue_growth_qoq = np.nan

                    # REVENUE_GROWTH_YOY: same as REVENUE_GROWTH_1Y
                    revenue_growth_yoy = revenue_growth_1y

                    # Quality/Risk Score Factors (5개)
                    # ASSET_QUALITY: (Total Assets - Cash - Receivables - Inventory) / Total Assets
                    asset_quality = np.nan
                    if total_assets is not None and total_assets > 0:
                        tangible_assets = float(total_assets) - float(cash or 0) - float(receivables or 0) - float(inventory or 0)
                        asset_quality = tangible_assets / float(total_assets)

                    # CASH_CONVERSION_EFFICIENCY: OCF / Net Income
                    cash_conversion_efficiency = np.nan
                    if net_income is not None and ocf is not None and net_income != 0:
                        cash_conversion_efficiency = float(ocf) / float(net_income)

                    # PROFITABILITY_SCORE: Simple profitability score (0-5)
                    profitability_score = 0
                    if npm is not None and npm > 0:
                        profitability_score += 1
                    if opm is not None and opm > 10:
                        profitability_score += 1
                    if roe_val is not None and roe_val > 10:
                        profitability_score += 1
                    if roa_val is not None and roa_val > 5:
                        profitability_score += 1
                    if ocf_ratio is not None and ocf_ratio > 10:
                        profitability_score += 1

                    # STABILITY_SCORE: Simple stability score (0-5)
                    stability_score = 0
                    if current_ratio is not None and current_ratio > 1:
                        stability_score += 1
                    if debt_ratio is not None and debt_ratio < 100:
                        stability_score += 1
                    if interest_coverage is not None and interest_coverage > 2:
                        stability_score += 1
                    if equity_ratio is not None and equity_ratio > 40:
                        stability_score += 1
                    if cash_ratio is not None and cash_ratio > 0.5:
                        stability_score += 1

                    # ZMIJEWSKI_SCORE: Zmijewski bankruptcy prediction score
                    zmijewski_score = np.nan
                    if net_income is not None and total_assets is not None and total_debt is not None and total_assets > 0:
                        x1_roa = float(net_income) / float(total_assets)
                        x2_leverage = float(total_debt) / float(total_assets) if total_assets > 0 else 0
                        x3_liquidity = float(current_assets) / float(current_liabilities) if current_liabilities and current_liabilities > 0 else 1
                        zmijewski_score = -4.3 - 4.5*x1_roa + 5.7*x2_leverage - 0.004*x3_liquidity

                    # Microstructure Factors - add REINVESTMENT_RATE here
                    # REINVESTMENT_RATE: (CAPEX - Depreciation) / Net Income
                    reinvestment_rate = np.nan
                    if net_income is not None and cfi is not None and net_income > 0:
                        capex = abs(float(cfi))
                        reinvestment = capex - float(depreciation or 0)
                        reinvestment_rate = reinvestment / float(net_income)

                    # Update the financial_factors dict with all new factors
                    financial_factors[stock_code].update({
                        # Cash Flow Factors
                        'CAPEX_TO_OCF': capex_to_ocf,
                        'CAPEX_TO_SALES': capex_to_sales,
                        'CFI_TO_ASSETS': cfi_to_assets,
                        'CFO_TO_SALES': cfo_to_sales,
                        'FCF_MARGIN': fcf_margin,
                        'FCF_TO_SALES': fcf_to_sales,
                        'FREE_CASH_FLOW': free_cash_flow,
                        'CFF_RATIO': cff_ratio,
                        # Profitability/Efficiency Factors
                        'EBITDA_MARGIN': ebitda_margin,
                        'DUPONT_ROE': dupont_roe,
                        'EQUITY_MULTIPLIER': equity_multiplier_val,
                        'FINANCIAL_LEVERAGE': financial_leverage,
                        'FIXED_ASSET_TURNOVER': fixed_asset_turnover,
                        'OPERATING_LEVERAGE': operating_leverage,
                        'RECEIVABLES_TURNOVER': receivables_turnover,
                        'WORKING_CAPITAL_TURNOVER': working_capital_turnover,
                        # Growth Factors
                        'ASSET_GROWTH_YOY': asset_growth_yoy,
                        'EPS_GROWTH_YOY': eps_growth_yoy,
                        'NET_INCOME_GROWTH_YOY': net_income_growth_yoy,
                        'REVENUE_GROWTH_QOQ': revenue_growth_qoq,
                        'REVENUE_GROWTH_YOY': revenue_growth_yoy,
                        # Quality/Risk Score Factors
                        'ASSET_QUALITY': asset_quality,
                        'CASH_CONVERSION_EFFICIENCY': cash_conversion_efficiency,
                        'PROFITABILITY_SCORE': profitability_score,
                        'STABILITY_SCORE': stability_score,
                        'ZMIJEWSKI_SCORE': zmijewski_score,
                        # Microstructure
                        'REINVESTMENT_RATE': reinvestment_rate,
                    })

                    count += 1

        return financial_factors

    def calculate_all_indicators_extreme(
        self,
        price_pl: pl.DataFrame,
        financial_pl: pl.DataFrame,
        calc_date: date,
        stock_prices_pl: Optional[pl.DataFrame] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        극한 최적화 지표 계산 (단일 패스)

        모든 지표(기술적 + 재무)를 한 번에 계산하여 중복 제거
        stock_prices_pl: 상장주식수 및 시가총액 데이터 (PBR/PER 계산용)
        """
        try:
            # 1. 데이터 준비 (메모리 맵 사용 고려)
            lookback = 60
            min_date = calc_date - timedelta(days=lookback * 2)

            filtered_data = price_pl.filter(
                (pl.col('date') >= min_date) &
                (pl.col('date') <= calc_date)
            ).sort(by=['stock_code', 'date'])

            if filtered_data.is_empty():
                return {}

            # 2. Numpy 배열 변환 (Zero-copy)
            stocks = filtered_data.select('stock_code').unique().to_numpy().flatten()
            dates = filtered_data.select('date').unique().sort(by='date').to_numpy().flatten()

            n_stocks = len(stocks)
            n_days = len(dates)

            # 3. 가격/거래량 행렬 생성 (연속 메모리)
            price_matrix = np.zeros((n_stocks, n_days), dtype=np.float32, order='C')
            volume_matrix = np.zeros((n_stocks, n_days), dtype=np.float32, order='C')  # Phase 2-B
            high_matrix = np.zeros((n_stocks, n_days), dtype=np.float32, order='C')  # Phase 2-B (Stochastic용)
            low_matrix = np.zeros((n_stocks, n_days), dtype=np.float32, order='C')  # Phase 2-B (Stochastic용)

            stock_to_idx = {stock: idx for idx, stock in enumerate(stocks)}
            # numpy.datetime64를 Python date로 변환하여 매핑 생성
            def to_python_date(d):
                """numpy.datetime64 또는 datetime을 Python date로 변환"""
                if isinstance(d, np.datetime64):
                    # numpy.datetime64 -> datetime -> date
                    ts = pd.Timestamp(d)
                    return ts.date()
                elif hasattr(d, 'date'):
                    return d.date()
                else:
                    return d

            date_to_idx = {to_python_date(d): idx for idx, d in enumerate(dates)}

            # 빠른 채우기
            for row in filtered_data.iter_rows(named=True):
                stock_idx = stock_to_idx[row['stock_code']]
                # datetime을 date로 변환
                row_date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
                date_idx = date_to_idx.get(row_date)
                if date_idx is not None:
                    price_matrix[stock_idx, date_idx] = float(row['close_price'])
                    volume_matrix[stock_idx, date_idx] = float(row.get('volume', 0))  # Phase 2-B
                    high_matrix[stock_idx, date_idx] = float(row.get('high_price', row['close_price']))  # Phase 2-B
                    low_matrix[stock_idx, date_idx] = float(row.get('low_price', row['close_price']))  # Phase 2-B

            # 4. 모든 지표를 한 번에 계산 (병렬)
            logger.info(f"🔥 극한 최적화 계산 시작 ({n_stocks}개 × {n_days}일)")

            # 병렬 계산
            momentum_1m = self._calculate_momentum_extreme(price_matrix, dates, 20)
            momentum_3m = self._calculate_momentum_extreme(price_matrix, dates, 60)
            momentum_6m = self._calculate_momentum_extreme(price_matrix, dates, 120)  # Phase 2-B
            momentum_12m = self._calculate_momentum_extreme(price_matrix, dates, 250)  # Phase 2-B
            rsi = self._calculate_rsi_extreme(price_matrix, 14)
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_extreme(price_matrix, 20)
            macd_line, macd_signal, macd_hist = self._calculate_macd_extreme(price_matrix)

            # Phase 2-B: 52주 고저점 대비 거리
            high_52w, low_52w = self._calculate_52w_high_low(price_matrix, dates, 250)

            # Phase 2-B: 추가 기술적 지표
            stochastic_14 = self._calculate_stochastic_extreme(high_matrix, low_matrix, price_matrix, 14)
            volume_roc = self._calculate_volume_roc_extreme(volume_matrix, 20)

            # === 22개 기술적 지표 추가 계산 ===
            # Moving Averages (5개)
            ma_5, ma_20, ma_60, ma_120, ma_250 = self._calculate_moving_averages_extreme(price_matrix)

            # Trend Indicators (6개)
            atr = self._calculate_atr_extreme(high_matrix, low_matrix, price_matrix, 14)
            adx = self._calculate_adx_extreme(high_matrix, low_matrix, price_matrix, 14)
            aroon_up, aroon_down = self._calculate_aroon_extreme(high_matrix, low_matrix, 25)

            # Oscillators (6개)
            cci = self._calculate_cci_extreme(high_matrix, low_matrix, price_matrix, 20)
            mfi = self._calculate_mfi_extreme(high_matrix, low_matrix, price_matrix, volume_matrix, 14)
            williams_r = self._calculate_williams_r_extreme(high_matrix, low_matrix, price_matrix, 14)

            # Volume-based (3개)
            cmf = self._calculate_cmf_extreme(high_matrix, low_matrix, price_matrix, volume_matrix, 20)
            obv = self._calculate_obv_extreme(price_matrix, volume_matrix)
            vwap = self._calculate_vwap_extreme(high_matrix, low_matrix, price_matrix, volume_matrix)

            # 5. calc_date 인덱스
            calc_date_idx = date_to_idx.get(calc_date)
            logger.info(f"📅 calc_date: {calc_date}, calc_date_idx: {calc_date_idx}")
            if calc_date_idx is None:
                logger.warning(f"⚠️ calc_date {calc_date}를 date_to_idx에서 찾을 수 없습니다!")
                return {}

            # 6. 상장주식수 및 시가총액 데이터 (PBR/PER 계산용)
            stock_info_dict = {}
            if stock_prices_pl is not None and not stock_prices_pl.is_empty():
                logger.info(f"💹 상장주식수 데이터 있음: {len(stock_prices_pl)}건")
                # calc_date에 가장 가까운 날짜의 상장주식수 및 시가총액 가져오기
                stock_info_filtered = stock_prices_pl.filter(
                    pl.col('trade_date') <= calc_date
                ).sort(by=['company_id', 'trade_date'], descending=[False, True])

                # 각 종목별 최신 데이터
                count_loaded = 0
                for row in stock_info_filtered.iter_rows(named=True):
                    stock_code = row.get('stock_code')
                    if stock_code and stock_code not in stock_info_dict:
                        stock_info_dict[stock_code] = {
                            'listed_shares': row.get('listed_shares'),
                            'market_cap': row.get('market_cap')
                        }
                        count_loaded += 1
                        if count_loaded <= 3:
                            logger.info(f"💹 [{stock_code}] listed_shares = {row.get('listed_shares')}, market_cap = {row.get('market_cap')}")
                logger.debug(f"💹 상장주식수 매핑 완료: {len(stock_info_dict)}개 종목")
            # 🚀 최적화: 경고 로그 제거 (멀티프로세싱 시 수백 번 반복됨)

            # 7. 재무 팩터 계산 (벡터화)
            financial_factors = {}
            logger.debug(f"💰 재무 팩터 계산 시작")
            if financial_pl is not None and not financial_pl.is_empty():
                # 재무 데이터 필터링
                financial_filtered = financial_pl.filter(pl.col('stock_code').is_in(stocks))

                count_with_financial = 0
                first_row_logged = False
                for stock_code in stocks:
                    stock_financial = financial_filtered.filter(pl.col('stock_code') == stock_code)

                    if not stock_financial.is_empty():
                        # 최신 재무 데이터 가져오기
                        latest = stock_financial.sort(by='fiscal_year', descending=True).limit(1)

                        if len(latest) > 0:
                            row = latest.to_dicts()[0]

                            # 첫 번째 row의 키 출력 (디버깅)
                            if not first_row_logged:
                                logger.debug(f"🔍 첫 번째 재무 데이터 row 키: {list(row.keys())}")
                                logger.debug(f"🔍 첫 번째 재무 데이터 샘플: {row}")
                                first_row_logged = True

                            # 현재 주가
                            stock_idx = stock_to_idx.get(stock_code)
                            if stock_idx is not None:
                                current_price = float(price_matrix[stock_idx, calc_date_idx])

                                # 재무 데이터 추출 (한글 컬럼명)
                                net_income = row.get('당기순이익')  # 당기순이익
                                revenue = row.get('매출액')  # 매출액
                                operating_income = row.get('영업이익')  # 영업이익
                                total_equity = row.get('자본총계')  # 자본총계
                                total_assets = row.get('자산총계')  # 자산총계

                                # 재무 팩터 계산
                                # ROE = 당기순이익 / 자본총계 × 100
                                roe_val = np.nan
                                if net_income is not None and total_equity is not None and total_equity > 0:
                                    roe_val = (float(net_income) / float(total_equity)) * 100

                                # ROA = 당기순이익 / 자산총계 × 100
                                roa_val = np.nan
                                if net_income is not None and total_assets is not None and total_assets > 0:
                                    roa_val = (float(net_income) / float(total_assets)) * 100

                                # 영업이익률 = 영업이익 / 매출액 × 100
                                operating_margin = np.nan
                                if operating_income is not None and revenue is not None and revenue > 0:
                                    operating_margin = (float(operating_income) / float(revenue)) * 100

                                # 순이익률 = 당기순이익 / 매출액 × 100
                                net_margin = np.nan
                                if net_income is not None and revenue is not None and revenue > 0:
                                    net_margin = (float(net_income) / float(revenue)) * 100

                                # PBR, PER 계산 (시가총액 활용)
                                pbr_val = np.nan
                                per_val = np.nan

                                stock_info = stock_info_dict.get(stock_code)
                                if stock_info:
                                    market_cap = stock_info.get('market_cap')

                                    if market_cap and market_cap > 0:
                                        # PBR = 시가총액 / 자본총계
                                        if total_equity is not None and total_equity > 0:
                                            pbr_val = float(market_cap) / float(total_equity)

                                        # PER = 시가총액 / 당기순이익
                                        if net_income is not None and net_income > 0:
                                            per_val = float(market_cap) / float(net_income)

                                financial_factors[stock_code] = {
                                    'PER': per_val,
                                    'PBR': pbr_val,
                                    'ROE': roe_val,
                                    'ROA': roa_val,
                                    'OPERATING_MARGIN': operating_margin,
                                    'NET_MARGIN': net_margin,
                                }
                                count_with_financial += 1

                logger.debug(f"✅ 재무 팩터 계산 완료: {count_with_financial}개 종목")

            # 7. 결과 Dict 변환 (기술적 + 재무 팩터 통합)
            result_dict = {}
            for stock_idx, stock_code in enumerate(stocks):
                # 볼린저 포지션 계산
                bb_width = (bb_upper[stock_idx, calc_date_idx] - bb_lower[stock_idx, calc_date_idx])
                bb_pos = (price_matrix[stock_idx, calc_date_idx] - bb_middle[stock_idx, calc_date_idx]) / (bb_width + 1e-10)

                # 52주 고저점 대비 거리 계산
                current_price = price_matrix[stock_idx, calc_date_idx]
                high_52 = high_52w[stock_idx, calc_date_idx]
                low_52 = low_52w[stock_idx, calc_date_idx]

                # DISTANCE_FROM_52W_HIGH: 52주 최고가 대비 현재가 위치 (%)
                distance_from_high = ((current_price - high_52) / high_52 * 100) if high_52 > 0 else np.nan

                # DISTANCE_FROM_52W_LOW: 52주 최저가 대비 현재가 위치 (%)
                distance_from_low = ((current_price - low_52) / low_52 * 100) if low_52 > 0 else np.nan

                # PRICE_POSITION: 볼린저 중심선(20일 이동평균) 대비 현재가 위치 (%)
                bb_middle_val = bb_middle[stock_idx, calc_date_idx]
                price_position = ((current_price - bb_middle_val) / bb_middle_val * 100) if bb_middle_val > 0 else np.nan

                # PRICE_VS_MA20 계산
                ma_20_val = ma_20[stock_idx, calc_date_idx]
                price_vs_ma20 = ((current_price - ma_20_val) / ma_20_val * 100) if ma_20_val > 0 and not np.isnan(ma_20_val) else np.nan

                # 기술적 지표
                factors = {
                    'MOMENTUM_1M': float(momentum_1m[stock_idx, calc_date_idx]),
                    'MOMENTUM_3M': float(momentum_3m[stock_idx, calc_date_idx]),
                    'MOMENTUM_6M': float(momentum_6m[stock_idx, calc_date_idx]),  # Phase 2-B
                    'MOMENTUM_12M': float(momentum_12m[stock_idx, calc_date_idx]),  # Phase 2-B
                    'RSI': float(rsi[stock_idx, calc_date_idx]),
                    'RSI_14': float(rsi[stock_idx, calc_date_idx]),  # Phase 2-B (RSI와 동일)
                    'BOLLINGER_POSITION': float(bb_pos),
                    'BOLLINGER_WIDTH': float(bb_width / bb_middle[stock_idx, calc_date_idx] * 100),
                    'MACD': float(macd_line[stock_idx, calc_date_idx]),
                    'MACD_SIGNAL': float(macd_signal[stock_idx, calc_date_idx]),
                    'MACD_HISTOGRAM': float(macd_hist[stock_idx, calc_date_idx]),
                    # Phase 2-B: 52주 고저점 대비 거리
                    'DISTANCE_FROM_52W_HIGH': float(distance_from_high),
                    'DISTANCE_FROM_52W_LOW': float(distance_from_low),
                    # Phase 2-B: 추가 기술적 지표
                    'STOCHASTIC_14': float(stochastic_14[stock_idx, calc_date_idx]),
                    'VOLUME_ROC': float(volume_roc[stock_idx, calc_date_idx]),
                    'PRICE_POSITION': float(price_position),
                    # === 22개 기술적 지표 추가 ===
                    # Moving Averages (5개)
                    'MA_5': float(ma_5[stock_idx, calc_date_idx]),
                    'MA_20': float(ma_20[stock_idx, calc_date_idx]),
                    'MA_60': float(ma_60[stock_idx, calc_date_idx]),
                    'MA_120': float(ma_120[stock_idx, calc_date_idx]),
                    'MA_250': float(ma_250[stock_idx, calc_date_idx]),
                    # Trend Indicators (7개)
                    'ADX': float(adx[stock_idx, calc_date_idx]),
                    'AROON_UP': float(aroon_up[stock_idx, calc_date_idx]),
                    'AROON_DOWN': float(aroon_down[stock_idx, calc_date_idx]),
                    'ATR': float(atr[stock_idx, calc_date_idx]),
                    'PRICE_VS_MA20': float(price_vs_ma20),
                    # MACD, MACD_HISTOGRAM은 위에 이미 있음
                    # Oscillators (6개)
                    'CCI': float(cci[stock_idx, calc_date_idx]),
                    'MFI': float(mfi[stock_idx, calc_date_idx]),
                    'ULTIMATE_OSCILLATOR': np.nan,  # 복잡한 계산으로 인해 나중에 구현
                    'WILLIAMS_R': float(williams_r[stock_idx, calc_date_idx]),
                    'TRIX': np.nan,  # Triple EMA로 인해 나중에 구현
                    # Volume-based (3개)
                    'CMF': float(cmf[stock_idx, calc_date_idx]),
                    'OBV': float(obv[stock_idx, calc_date_idx]),
                    'VWAP': float(vwap[stock_idx, calc_date_idx]),
                    # === NEW: 40 Additional Price-Based Factors ===
                    # Momentum factors (aliases + new)
                    'RETURN_1M': float(momentum_1m[stock_idx, calc_date_idx]),
                    'RETURN_3M': float(momentum_3m[stock_idx, calc_date_idx]),
                    'RETURN_6M': float(momentum_6m[stock_idx, calc_date_idx]),
                    'RETURN_12M': float(momentum_12m[stock_idx, calc_date_idx]),
                    'RET_3D': np.nan,  # Would need 3-day momentum calculation
                    'RET_8D': np.nan,  # Would need 8-day momentum calculation
                    'DAYS_FROM_52W_HIGH': np.nan,  # Would need date tracking
                    'DAYS_FROM_52W_LOW': np.nan,  # Would need date tracking
                    'WEEK_52_POSITION': float(price_position),  # Alias to PRICE_POSITION
                    # Risk/Volatility factors (calculated from price data)
                    'HISTORICAL_VOLATILITY_20': np.nan,  # Would need 20-day std calculation
                    'HISTORICAL_VOLATILITY_60': np.nan,  # Would need 60-day std calculation
                    'PARKINSON_VOLATILITY': np.nan,  # Would need high/low-based calc
                    'DOWNSIDE_VOLATILITY': np.nan,  # Would need negative returns std
                    'MAX_DRAWDOWN': np.nan,  # Would need drawdown calculation
                    'SHARPE_RATIO': np.nan,  # Would need returns/volatility calc
                    'SORTINO_RATIO': np.nan,  # Would need downside deviation calc
                    # Microstructure factors
                    'AMIHUD_ILLIQUIDITY': np.nan,  # Would need abs(return)/dollar_volume
                    'EASE_OF_MOVEMENT': np.nan,  # Would need distance_moved/box_ratio
                    'FORCE_INDEX': np.nan,  # Would need price_change * volume
                    'INTRADAY_VOLATILITY': ((high_matrix[stock_idx, calc_date_idx] - low_matrix[stock_idx, calc_date_idx]) / current_price * 100) if current_price > 0 else np.nan,
                    'VOLUME_PRICE_TREND': np.nan,  # Would need cumulative vpt calc
                }

                # === ADD MISSING VOLUME/TRADING FACTORS ===
                # Calculate volume-based factors from volume_matrix
                current_volume = volume_matrix[stock_idx, calc_date_idx] if calc_date_idx < volume_matrix.shape[1] else 0

                # ACCUMULATION_DISTRIBUTION: Cumulative (close - low) - (high - close) / (high - low) * volume
                accumulation_distribution = np.nan
                if calc_date_idx >= 1:
                    ad_sum = 0
                    for i in range(max(0, calc_date_idx - 20), calc_date_idx + 1):
                        if i < price_matrix.shape[1]:
                            h = high_matrix[stock_idx, i]
                            l = low_matrix[stock_idx, i]
                            c = price_matrix[stock_idx, i]
                            v = volume_matrix[stock_idx, i]
                            if h != l:
                                mf_multiplier = ((c - l) - (h - c)) / (h - l)
                                ad_sum += mf_multiplier * v
                    accumulation_distribution = ad_sum

                # AVG_TRADING_VALUE: Average trading value (price * volume) over 20 days
                avg_trading_value = np.nan
                if calc_date_idx >= 19:
                    trading_values = []
                    for i in range(calc_date_idx - 19, calc_date_idx + 1):
                        if i >= 0 and i < price_matrix.shape[1]:
                            trading_values.append(price_matrix[stock_idx, i] * volume_matrix[stock_idx, i])
                    if trading_values:
                        avg_trading_value = np.mean(trading_values)

                # VOLUME_MA_5: 5-day volume moving average
                volume_ma_5 = np.nan
                if calc_date_idx >= 4:
                    volumes = volume_matrix[stock_idx, max(0, calc_date_idx - 4):calc_date_idx + 1]
                    volume_ma_5 = np.mean(volumes) if len(volumes) > 0 else np.nan

                # VOLUME_MA_20: 20-day volume moving average
                volume_ma_20 = np.nan
                if calc_date_idx >= 19:
                    volumes = volume_matrix[stock_idx, max(0, calc_date_idx - 19):calc_date_idx + 1]
                    volume_ma_20 = np.mean(volumes) if len(volumes) > 0 else np.nan

                # VOLUME_PRICE_TREND: Already in factors dict above, but calculate properly here
                volume_price_trend_calc = np.nan
                if calc_date_idx >= 20:
                    vpt = 0
                    for i in range(max(0, calc_date_idx - 20), calc_date_idx):
                        if i + 1 < price_matrix.shape[1]:
                            prev_close = price_matrix[stock_idx, i]
                            curr_close = price_matrix[stock_idx, i + 1]
                            vol = volume_matrix[stock_idx, i + 1]
                            if prev_close > 0:
                                pct_change = (curr_close - prev_close) / prev_close
                                vpt += vol * pct_change
                    volume_price_trend_calc = vpt

                # VOLUME_RATIO_20D: Current volume / 20-day average volume (already calculated earlier, but ensure it's available)
                volume_ratio_20d_calc = np.nan
                if volume_ma_20 is not None and volume_ma_20 > 0 and current_volume > 0:
                    volume_ratio_20d_calc = (current_volume / volume_ma_20) * 100

                # VOLUME_SURGE: Volume surge detection (current > 2x average)
                volume_surge = 0
                if volume_ma_20 is not None and volume_ma_20 > 0 and current_volume > (2 * volume_ma_20):
                    volume_surge = 1

                # TURNOVER_RATE_20D: Average turnover rate over 20 days (volume / listed_shares * 100)
                turnover_rate_20d = np.nan
                # Would need listed_shares from stock_info_dict - implement if available

                # Update factors dict with volume/trading factors
                factors.update({
                    'ACCUMULATION_DISTRIBUTION': accumulation_distribution,
                    'AVG_TRADING_VALUE': avg_trading_value,
                    'VOLUME_MA_5': volume_ma_5,
                    'VOLUME_MA_20': volume_ma_20,
                    'VOLUME_PRICE_TREND': volume_price_trend_calc,
                    'VOLUME_RATIO_20D': volume_ratio_20d_calc,
                    'VOLUME_SURGE': volume_surge,
                    'TURNOVER_RATE_20D': turnover_rate_20d,
                })

                # === IMPROVE TECHNICAL FACTORS (VOLATILITY) ===
                # Calculate proper volatility measures
                # VOLATILITY_20D: 20-day standard deviation of returns
                volatility_20d_calc = np.nan
                if calc_date_idx >= 20:
                    returns = []
                    for i in range(max(0, calc_date_idx - 20), calc_date_idx):
                        if i + 1 < price_matrix.shape[1] and i >= 0:
                            prev_price = price_matrix[stock_idx, i]
                            curr_price = price_matrix[stock_idx, i + 1]
                            if prev_price > 0:
                                ret = (curr_price - prev_price) / prev_price
                                returns.append(ret)
                    if len(returns) > 0:
                        volatility_20d_calc = np.std(returns) * np.sqrt(252)  # Annualized

                # VOLATILITY_60D: 60-day standard deviation of returns
                volatility_60d_calc = np.nan
                if calc_date_idx >= 60:
                    returns = []
                    for i in range(max(0, calc_date_idx - 60), calc_date_idx):
                        if i + 1 < price_matrix.shape[1] and i >= 0:
                            prev_price = price_matrix[stock_idx, i]
                            curr_price = price_matrix[stock_idx, i + 1]
                            if prev_price > 0:
                                ret = (curr_price - prev_price) / prev_price
                                returns.append(ret)
                    if len(returns) > 0:
                        volatility_60d_calc = np.std(returns) * np.sqrt(252)  # Annualized

                # VOLATILITY_90D: 90-day standard deviation of returns
                volatility_90d_calc = np.nan
                if calc_date_idx >= 90:
                    returns = []
                    for i in range(max(0, calc_date_idx - 90), calc_date_idx):
                        if i + 1 < price_matrix.shape[1] and i >= 0:
                            prev_price = price_matrix[stock_idx, i]
                            curr_price = price_matrix[stock_idx, i + 1]
                            if prev_price > 0:
                                ret = (curr_price - prev_price) / prev_price
                                returns.append(ret)
                    if len(returns) > 0:
                        volatility_90d_calc = np.std(returns) * np.sqrt(252)  # Annualized

                # Update volatility factors
                factors.update({
                    'VOLATILITY_20D': volatility_20d_calc,
                    'VOLATILITY_60D': volatility_60d_calc,
                    'VOLATILITY_90D': volatility_90d_calc,
                })

                # 재무 팩터 추가
                if stock_code in financial_factors:
                    factors.update(financial_factors[stock_code])

                result_dict[stock_code] = factors

            logger.debug(f"✅ 극한 최적화 완료: {len(result_dict)}개 종목")
            return result_dict

        except Exception as e:
            logger.error(f"극한 최적화 실패: {e}", exc_info=True)
            return {}

    async def calculate_factors_streaming(
        self,
        price_pl: pl.DataFrame,
        dates: List[date],
        batch_size: int = 50
    ) -> Dict[date, Dict[str, Dict[str, float]]]:
        """
        스트리밍 파이프라인 (메모리 효율)

        대용량 데이터를 배치로 처리하여
        메모리 사용량 최소화
        """
        all_results = {}

        # 날짜를 배치로 분할
        for i in range(0, len(dates), batch_size):
            batch_dates = dates[i:i + batch_size]

            # 배치 처리
            batch_results = await self._process_batch_parallel(
                price_pl, batch_dates
            )

            all_results.update(batch_results)

        return all_results

    async def _process_batch_parallel(
        self,
        price_pl: pl.DataFrame,
        batch_dates: List[date]
    ) -> Dict[date, Dict[str, Dict[str, float]]]:
        """배치를 병렬로 처리"""
        loop = asyncio.get_event_loop()

        # ProcessPoolExecutor로 병렬 처리
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            futures = []

            for calc_date in batch_dates:
                future = loop.run_in_executor(
                    executor,
                    self.calculate_all_indicators_extreme,
                    price_pl,
                    calc_date
                )
                futures.append((calc_date, future))

            # 결과 수집
            results = {}
            for calc_date, future in futures:
                result = await future
                results[calc_date] = result

            return results


# Redis Lua 스크립트 (원자적 배치 연산)
REDIS_BATCH_GET_SCRIPT = """
local results = {}
for i, key in ipairs(KEYS) do
    results[i] = redis.call('GET', key)
end
return results
"""

REDIS_BATCH_SET_SCRIPT = """
for i = 1, #KEYS do
    redis.call('SETEX', KEYS[i], ARGV[1], ARGV[i + 1])
end
return #KEYS
"""


class ExtremeRedisOptimizer:
    """극한 Redis 최적화"""

    def __init__(self, redis_client):
        self.redis = redis_client
        # Lua 스크립트 등록
        self.batch_get_script = None
        self.batch_set_script = None

    async def batch_get_lua(self, keys: List[str]) -> List[bytes]:
        """Lua 스크립트로 배치 GET (네트워크 왕복 1회)"""
        if not self.batch_get_script:
            self.batch_get_script = await self.redis.script_load(REDIS_BATCH_GET_SCRIPT)

        return await self.redis.evalsha(self.batch_get_script, len(keys), *keys)

    async def batch_set_lua(self, data: Dict[str, bytes], ttl: int = 3600):
        """Lua 스크립트로 배치 SET (네트워크 왕복 1회)"""
        if not self.batch_set_script:
            self.batch_set_script = await self.redis.script_load(REDIS_BATCH_SET_SCRIPT)

        keys = list(data.keys())
        values = list(data.values())

        return await self.redis.evalsha(
            self.batch_set_script,
            len(keys),
            *keys,
            ttl,
            *values
        )


# 싱글톤
extreme_optimizer = ExtremeOptimizer()
