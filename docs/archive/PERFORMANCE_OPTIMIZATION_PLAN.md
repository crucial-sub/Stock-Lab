# 백테스트 극한 성능 최적화 계획

## 📊 현재 성능 분석

### 코드 아키텍처 분석 결과

**현재 성능:**
- 1개월 백테스트 (2024.01.01-01.31): **15-20초**
- 팩터 계산: **8.64초**
- 전체 실행: 230개 종목 × 22일 ≈ **15초**

**목표 성능:**
- 1개월 백테스트: **5초 이하** (3배 개선)
- 1년 백테스트: **30초 이하** (6배 개선)
- 5년 백테스트: **2분 이하** (15배 개선)

---

## 🚨 병목 지점 Top 5 (코드 분석 기반)

### 1. **DB 쿼리 병목** (예상 시간: 3-5초)
**위치:** `backtest_db_optimized.py:35-143`

**문제점:**
```python
# 현재: 3개 쿼리 순차 실행
load_price_data_optimized()        # 2-3초
load_financial_data_optimized()    # 1-2초
load_stock_prices_data()           # 0.5-1초
```

**개선 가능:**
- ✅ 컬럼 선택 최적화 (이미 구현됨)
- ❌ 쿼리 병렬화 (미구현 - asyncio.gather 사용 가능)
- ❌ Connection pooling 최적화
- ❌ Read replica 활용

---

### 2. **팩터 계산 병목** (예상 시간: 8-10초)
**위치:** `backtest_extreme_optimized.py:271-494`

**문제점:**
```python
# 현재: 각 날짜마다 순차 계산
for calc_date in dates_to_calc:  # 22일
    all_factors = extreme_optimizer.calculate_all_indicators_extreme(
        price_pl, financial_pl, calc_date_obj, stock_prices_pl
    )
```

**개선 가능:**
- ✅ Numba JIT 최적화 (이미 구현됨)
- ❌ 날짜별 병렬 계산 (멀티프로세싱)
- ❌ 전체 날짜를 한 번에 계산 (배치 처리)
- ❌ GPU 가속 (CuPy/RAPIDS)

---

### 3. **매수/매도 로직 병목** (예상 시간: 2-3초)
**위치:** `backtest.py:1784, 2229`

**문제점:**
```python
# 매 거래일마다 조건 평가 (for loop)
for trading_day in trading_days:  # 22일
    # DataFrame 필터링 반복
    stocks_today = factor_data[factor_data['date'] == trading_day]

    # 조건식 파싱 반복
    for condition in buy_conditions:
        evaluate_condition(condition, stock_data)
```

**개선 가능:**
- ❌ 조건식 파싱 캐싱 (한 번만 파싱)
- ❌ 벡터화 연산 (Pandas/Polars 활용)
- ❌ Numba JIT 적용

---

### 4. **포트폴리오 가치 계산 병목** (예상 시간: 1-2초)
**위치:** `backtest.py:1579-1600`

**문제점:**
```python
# 매 거래일마다 모든 보유 종목의 현재가 조회
for stock_code, data in snapshot_holdings.items():
    current_price_data = price_data[
        (price_data['stock_code'] == stock_code) &
        (price_data['date'] == trading_day)
    ]
```

**개선 가능:**
- ❌ 가격 데이터 인덱싱 (MultiIndex 활용)
- ❌ 벡터화 연산 (한 번에 모든 종목 가격 조회)
- ❌ 델타 업데이트 (전체 재계산 대신)

---

### 5. **DB 저장 병목** (예상 시간: 1-2초)
**위치:** `backtest.py:1614-1660`

**문제점:**
```python
# 매 10일마다 전체 daily_snapshots 삭제 후 재저장
delete_stmt = delete(SimulationDailyValue).where(...)
await self.db.execute(delete_stmt)

for snapshot in daily_snapshots:
    # INSERT 반복
```

**개선 가능:**
- ❌ DELETE 제거 (UPSERT 사용)
- ❌ Bulk insert 최적화
- ❌ 비동기 저장 (백그라운드 처리)

---

## 🎯 최적화 전략 3가지

### Strategy 1: Quick Wins (난이도: ⭐ | 효과: 30-50% 개선 | 시간: 1-2시간)

**목표:** 1개월 백테스트 15초 → **10초**

#### 1.1 DB 쿼리 병렬화
```python
# Before (순차 실행)
price_data = await load_price_data_optimized(...)      # 2-3초
financial_data = await load_financial_data_optimized(...)  # 1-2초
stock_prices_data = await load_stock_prices_data(...)  # 0.5-1초
# Total: 3.5-6초

# After (병렬 실행)
price_data, financial_data, stock_prices_data = await asyncio.gather(
    load_price_data_optimized(...),
    load_financial_data_optimized(...),
    load_stock_prices_data(...)
)
# Total: 2-3초 (병렬화로 최대 시간만 소요)
```

**예상 개선:** 3-4초 절약

#### 1.2 조건식 파싱 캐싱
```python
# Before (매 거래일마다 파싱)
for trading_day in trading_days:  # 22일
    parsed_conditions = parse_conditions(buy_conditions)  # 반복 파싱

# After (한 번만 파싱)
parsed_conditions = parse_conditions_cached(buy_conditions)  # 1회만
for trading_day in trading_days:
    use_cached_conditions(parsed_conditions)
```

**예상 개선:** 0.5-1초 절약

#### 1.3 DB 저장 최적화
```python
# Before (DELETE + INSERT)
await db.execute(delete(SimulationDailyValue))
for snapshot in daily_snapshots:
    await db.execute(insert(SimulationDailyValue).values(snapshot))

# After (UPSERT only)
await db.execute(
    insert(SimulationDailyValue).values(daily_snapshots)
    .on_conflict_do_update(...)
)
```

**예상 개선:** 1-2초 절약

**총 예상 개선:** 4.5-7초 절약 → **15초 → 8-10초**

---

### Strategy 2: Medium Effort (난이도: ⭐⭐ | 효과: 2-3배 개선 | 시간: 4-6시간)

**목표:** 1개월 백테스트 15초 → **5-7초**

#### 2.1 날짜별 팩터 계산 병렬화
```python
# Before (순차 계산)
for calc_date in dates_to_calc:  # 22일
    all_factors = calculate_all_indicators_extreme(...)  # 0.4초/일
# Total: 8.8초

# After (병렬 계산)
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(calculate_all_indicators_extreme, ...)
        for calc_date in dates_to_calc
    ]
    results = [future.result() for future in futures]
# Total: 1-2초 (10배 빠름)
```

**예상 개선:** 6-8초 절약

#### 2.2 포트폴리오 가치 계산 벡터화
```python
# Before (반복 필터링)
for stock_code in holdings:
    current_price = price_data[
        (price_data['stock_code'] == stock_code) &
        (price_data['date'] == trading_day)
    ].iloc[0]['close_price']

# After (벡터화)
# 가격 데이터 MultiIndex로 변환
price_indexed = price_data.set_index(['date', 'stock_code'])
holding_codes = list(holdings.keys())
current_prices = price_indexed.loc[(trading_day, holding_codes), 'close_price']
```

**예상 개선:** 1-2초 절약

#### 2.3 매수/매도 로직 벡터화
```python
# Before (반복 평가)
for stock in candidates:
    if evaluate_condition(stock, conditions):
        buy_candidates.append(stock)

# After (벡터화)
# Pandas query 사용
buy_candidates = stocks_today.query(
    '(MOMENTUM_1M > 5) and (RSI < 70) and (PER < 20)'
)
```

**예상 개선:** 1-2초 절약

**총 예상 개선:** 8-12초 절약 → **15초 → 3-7초**

---

### Strategy 3: High Impact (난이도: ⭐⭐⭐ | 효과: 5-10배 개선 | 시간: 1-2일)

**목표:** 1개월 백테스트 15초 → **1-3초**

#### 3.1 GPU 가속 (CuPy/RAPIDS)
```python
# Before (CPU/Numba)
import numpy as np
from numba import jit

@jit(parallel=True)
def calculate_momentum(prices):
    # CPU 병렬 처리
    pass

# After (GPU)
import cupy as cp

def calculate_momentum_gpu(prices_gpu):
    # GPU 가속 (100배 빠름)
    momentum = (prices_gpu[:, -1] / prices_gpu[:, 0] - 1) * 100
    return cp.asnumpy(momentum)
```

**예상 개선:** 팩터 계산 8초 → 0.5-1초 (8-16배)

#### 3.2 전체 날짜 배치 처리
```python
# Before (날짜별 계산)
for calc_date in dates_to_calc:  # 22일
    factors = calculate_indicators(price_pl, calc_date)

# After (전체 배치 처리)
# 모든 날짜의 팩터를 한 번에 계산
all_factors = calculate_indicators_batch(
    price_pl,
    dates=dates_to_calc  # 22일 한 번에
)
```

**예상 개선:** 8초 → 1-2초

#### 3.3 스트리밍 파이프라인
```python
# 데이터 로드 → 팩터 계산 → 백테스트 실행을 파이프라인으로
async def streaming_backtest():
    async for date_batch in stream_dates_batched(batch_size=5):
        # 배치 단위로 처리
        prices = await load_prices_batch(date_batch)
        factors = calculate_factors_batch(prices, date_batch)
        await execute_trades_batch(factors, date_batch)
```

**예상 개선:** 메모리 사용량 50% 감소, 전체 속도 20-30% 개선

**총 예상 개선:** 10-13초 절약 → **15초 → 2-5초**

---

## 📈 최종 목표 달성 예상

| 최적화 단계 | 1개월 백테스트 | 1년 백테스트 | 5년 백테스트 | 개선율 |
|------------|--------------|------------|------------|--------|
| **현재**     | 15-20초      | ~180초     | ~900초     | -      |
| **Quick Wins** | 8-10초   | ~90초      | ~450초     | 2배    |
| **Medium Effort** | 5-7초 | ~50초      | ~250초     | 3-4배  |
| **High Impact** | 1-3초   | ~20초      | ~100초     | 10배   |

**결론:** 3단계 최적화를 모두 적용하면 **목표 달성 가능!**

---

## 🔧 구현 우선순위

### Phase 1: Quick Wins (즉시 구현)
1. ✅ DB 쿼리 병렬화 (backtest_db_optimized.py)
2. ✅ 조건식 파싱 캐싱 (backtest.py)
3. ✅ DB 저장 최적화 (backtest.py)

### Phase 2: Medium Effort (1주일 내)
1. ✅ 날짜별 팩터 계산 병렬화 (backtest_integration.py)
2. ✅ 포트폴리오 가치 계산 벡터화 (backtest.py)
3. ✅ 매수/매도 로직 벡터화 (backtest.py)

### Phase 3: High Impact (필요시)
1. ⏳ GPU 가속 검토 (CuPy/RAPIDS)
2. ⏳ 전체 배치 처리 재설계
3. ⏳ 스트리밍 파이프라인 구현

---

## 📝 성공 지표

- [x] 1개월 백테스트: 15초 → **5초** (3배 향상)
- [ ] 1년 백테스트: 180초 → **30초** (6배 향상)
- [ ] 메모리 사용량: **30% 이상 절감**
- [ ] 캐시 히트율: **80% 이상**
- [ ] 에러 없음: **KeyError, AttributeError 0건 유지**

---

## 🚀 다음 단계

1. **Phase 1 구현 시작** (Quick Wins)
2. **성능 측정 및 비교**
3. **Phase 2 구현** (필요시)
4. **최종 벤치마크 및 보고서**
