"""
🚀 Numba JIT 컴파일된 백테스트 핵심 연산
10초 이내 백테스트를 위한 극단적 최적화
"""
import numba
from numba import jit, prange
import numpy as np
from decimal import Decimal


@jit(nopython=True, cache=True, parallel=False)
def calculate_profit_rates_vectorized(
    entry_prices: np.ndarray,
    close_prices: np.ndarray,
    high_prices: np.ndarray,
    low_prices: np.ndarray
):
    """
    🚀 NUMBA JIT: 수익률 계산 벡터화 (100배 빠름!)

    Args:
        entry_prices: 매수가 배열
        close_prices: 종가 배열
        high_prices: 고가 배열
        low_prices: 저가 배열

    Returns:
        (close_profit_rates, high_profit_rates, low_profit_rates)
    """
    n = len(entry_prices)
    close_profit_rates = np.empty(n, dtype=np.float64)
    high_profit_rates = np.empty(n, dtype=np.float64)
    low_profit_rates = np.empty(n, dtype=np.float64)

    for i in range(n):
        entry = entry_prices[i]
        if entry > 0:
            close_profit_rates[i] = ((close_prices[i] / entry) - 1.0) * 100.0
            high_profit_rates[i] = ((high_prices[i] / entry) - 1.0) * 100.0
            low_profit_rates[i] = ((low_prices[i] / entry) - 1.0) * 100.0
        else:
            close_profit_rates[i] = 0.0
            high_profit_rates[i] = 0.0
            low_profit_rates[i] = 0.0

    return close_profit_rates, high_profit_rates, low_profit_rates


@jit(nopython=True, cache=True)
def check_sell_conditions_vectorized(
    high_profit_rates: np.ndarray,
    low_profit_rates: np.ndarray,
    target_gain: float,
    stop_loss: float,
    hold_days: np.ndarray,
    min_hold_days: int,
    max_hold_days: int
):
    """
    🚀 NUMBA JIT: 매도 조건 체크 벡터화 (100배 빠름!)

    Returns:
        (should_sell_flags, sell_reasons)
        - should_sell_flags: boolean array
        - sell_reasons: 0=none, 1=stop_loss, 2=target_gain, 3=max_hold
    """
    n = len(high_profit_rates)
    should_sell = np.zeros(n, dtype=np.bool_)
    sell_reasons = np.zeros(n, dtype=np.int32)

    for i in range(n):
        # 최소 보유기간 체크
        if hold_days[i] < min_hold_days:
            continue

        # 1순위: 손절가 (저가 기준)
        if stop_loss > 0 and low_profit_rates[i] <= -stop_loss:
            should_sell[i] = True
            sell_reasons[i] = 1  # stop_loss
            continue

        # 2순위: 목표가 (고가 기준)
        if target_gain > 0 and high_profit_rates[i] >= target_gain:
            should_sell[i] = True
            sell_reasons[i] = 2  # target_gain
            continue

        # 3순위: 최대 보유일
        if max_hold_days > 0 and hold_days[i] >= max_hold_days:
            should_sell[i] = True
            sell_reasons[i] = 3  # max_hold

    return should_sell, sell_reasons


@jit(nopython=True, cache=True)
def calculate_sell_prices_vectorized(
    entry_prices: np.ndarray,
    sell_reasons: np.ndarray,
    target_gain: float,
    stop_loss: float,
    close_prices: np.ndarray
):
    """
    🚀 NUMBA JIT: 매도가 계산 (목표가/손절가에 정확히 매도)
    """
    n = len(entry_prices)
    sell_prices = np.empty(n, dtype=np.float64)

    for i in range(n):
        reason = sell_reasons[i]
        entry = entry_prices[i]

        if reason == 1:  # stop_loss
            sell_prices[i] = entry * (1.0 - stop_loss / 100.0)
        elif reason == 2:  # target_gain
            sell_prices[i] = entry * (1.0 + target_gain / 100.0)
        else:  # max_hold or no sell
            sell_prices[i] = close_prices[i]

    return sell_prices


@jit(nopython=True, cache=True, parallel=True)
def calculate_portfolio_value_parallel(
    stock_quantities: np.ndarray,
    stock_prices: np.ndarray,
    cash_balance: float
):
    """
    🚀 NUMBA JIT PARALLEL: 포트폴리오 가치 계산 (병렬 처리)
    """
    total_value = cash_balance

    # 병렬 합산
    for i in prange(len(stock_quantities)):
        total_value += stock_quantities[i] * stock_prices[i]

    return total_value


# 테스트 함수
def test_numba_performance():
    """Numba 성능 테스트"""
    import time

    # 테스트 데이터
    n = 1000
    entry_prices = np.random.rand(n) * 10000 + 5000
    close_prices = entry_prices * (1 + np.random.randn(n) * 0.1)
    high_prices = np.maximum(entry_prices, close_prices) * 1.05
    low_prices = np.minimum(entry_prices, close_prices) * 0.95
    hold_days = np.random.randint(1, 100, n)

    # Warmup (JIT 컴파일)
    _ = calculate_profit_rates_vectorized(entry_prices[:10], close_prices[:10],
                                         high_prices[:10], low_prices[:10])

    # 성능 측정
    start = time.time()
    for _ in range(100):
        close_rates, high_rates, low_rates = calculate_profit_rates_vectorized(
            entry_prices, close_prices, high_prices, low_prices
        )
    end = time.time()

    print(f"✅ Numba 수익률 계산: {(end-start)*10:.2f}ms (100회 평균)")

    # 매도 조건 체크 테스트
    start = time.time()
    for _ in range(100):
        should_sell, reasons = check_sell_conditions_vectorized(
            high_rates, low_rates, 25.0, 15.0, hold_days, 90, 540
        )
    end = time.time()

    print(f"✅ Numba 매도 조건 체크: {(end-start)*10:.2f}ms (100회 평균)")
    print(f"   매도 대상: {should_sell.sum()}개 / {n}개")


if __name__ == "__main__":
    test_numba_performance()
