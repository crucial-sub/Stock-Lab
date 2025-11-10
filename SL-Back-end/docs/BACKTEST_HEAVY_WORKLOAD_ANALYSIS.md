# 🔥 백테스트 Heavy Workload 분석

## 📊 백테스트의 실제 부하 분석

### 백테스트 1회 실행 시 처리량

```python
# 예시: 2023-01-01 ~ 2023-12-31 (1년)
종목 수: 2,000개 (KOSPI + KOSDAQ)
거래일: 250일
팩터: 54개

총 데이터 포인트: 2,000 × 250 × 54 = 27,000,000개
메모리 사용: ~2-3GB per backtest
CPU 시간: 2-5분 (최적화 안된 경우 10-20분)
```

### 문제점
1. **메모리**: 한 번에 3GB × 16개 = **48GB 필요** 😱
2. **CPU**: 모든 코어 점유
3. **DB 부하**: 2700만 row 읽기
4. **네트워크**: 데이터 전송 병목

## 🚨 Celery만으로는 부족한 이유

### 문제 1: 메모리 폭발
```python
# Worker 16개가 동시 실행하면
Worker 1: 3GB
Worker 2: 3GB
...
Worker 16: 3GB
총 메모리: 48GB 😱

# 서버 한 대로는 불가능!
```

### 문제 2: DB 병목
```python
# 16개 백테스트가 동시에 DB 쿼리
SELECT * FROM stock_prices
WHERE date BETWEEN '2023-01-01' AND '2023-12-31'
-- 2,000개 종목 × 250일 = 500,000 rows

# 16배 = 8,000,000 rows 동시 읽기
# PostgreSQL 연결 고갈, Disk I/O 병목
```

### 문제 3: 데이터 중복 로딩
```python
# 각 Worker가 같은 데이터 로드
Worker 1: 2023년 가격 데이터 로드 (500,000 rows)
Worker 2: 2023년 가격 데이터 로드 (500,000 rows)
Worker 3: 2023년 가격 데이터 로드 (500,000 rows)
...
# 엄청난 중복과 낭비! 😱
```

## ✅ 올바른 해결책

### 1단계: 데이터 전처리 분리 (가장 중요!)

```python
# 잘못된 방식 (현재)
async def run_backtest():
    # 매번 모든 데이터 로드
    price_data = await load_price_data()      # 500K rows
    financial_data = await load_financial()   # 100K rows
    factor_data = await calculate_factors()   # 27M 계산

    result = simulate_portfolio(...)  # 실제 백테스트


# 올바른 방식 (개선)
# Step 1: 데이터 사전 준비 (1회만)
async def prepare_backtest_data(date_range):
    """모든 백테스트가 공유할 데이터 준비"""

    # Redis에 캐싱
    key = f"prepared_data:{date_range}"

    if not redis.exists(key):
        # 한 번만 계산
        price_data = await load_price_data()
        factor_data = await calculate_all_factors()

        # 압축해서 Redis에 저장
        compressed = compress(pickle.dumps({
            'prices': price_data,
            'factors': factor_data
        }))
        redis.set(key, compressed, ex=3600)  # 1시간 캐시

    return key

# Step 2: 백테스트 실행 (빠름!)
async def run_backtest(data_key, conditions):
    """준비된 데이터로 빠르게 실행"""

    # Redis에서 가져오기 (빠름!)
    data = decompress(redis.get(data_key))

    # 조건에 맞는 시뮬레이션만 실행
    result = simulate_portfolio(data, conditions)

    return result
```

### 2단계: 분산 캐싱 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI (API)                    │
└────────────┬───────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│              Data Preparation Service                │
│   (백그라운드에서 데이터 미리 준비 - 1시간마다)    │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│            Redis Cluster (Shared Cache)              │
│  - 가격 데이터 (압축)                               │
│  - 팩터 데이터 (압축)                               │
│  - 재무제표 데이터                                  │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker N│
│(경량화)│ │(경량화)│ │(경량화)│
└────────┘ └────────┘ └────────┘
   │          │          │
   └──────────┼──────────┘
              ▼
        ┌──────────┐
        │PostgreSQL│
        └──────────┘
```

### 3단계: 백테스트 엔진 최적화

```python
# app/services/backtest_optimized.py

class OptimizedBacktestEngine:
    """최적화된 백테스트 엔진"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.data_cache = {}

    async def run_backtest_optimized(
        self,
        backtest_id: UUID,
        conditions: dict,
        date_range: tuple
    ):
        """최적화된 백테스트 실행"""

        # 1. 캐시된 데이터 가져오기 (빠름!)
        cache_key = self._get_cache_key(date_range)
        cached_data = await self._get_cached_data(cache_key)

        if not cached_data:
            # 캐시 미스 - 데이터 준비
            cached_data = await self._prepare_and_cache_data(
                date_range, cache_key
            )

        # 2. 메모리 효율적인 시뮬레이션
        result = await self._run_lightweight_simulation(
            cached_data, conditions
        )

        return result

    async def _get_cached_data(self, key: str):
        """Redis에서 압축된 데이터 가져오기"""

        compressed = self.redis.get(key)
        if not compressed:
            return None

        # 압축 해제 (빠름!)
        data = pickle.loads(zlib.decompress(compressed))
        return data

    async def _prepare_and_cache_data(self, date_range, key):
        """데이터 준비 및 캐싱"""

        start, end = date_range

        # DB에서 데이터 로드 (1회만!)
        prices = await self.db.execute(
            select(StockPrice)
            .where(StockPrice.date.between(start, end))
        )

        # Pandas로 변환
        price_df = pd.DataFrame([
            {
                'date': p.date,
                'stock_code': p.stock_code,
                'close': p.close_price,
                'volume': p.volume
            }
            for p in prices
        ])

        # 팩터 계산 (벡터화!)
        factor_df = self._calculate_factors_vectorized(price_df)

        # 압축해서 캐싱
        data = {
            'prices': price_df.to_dict('records'),
            'factors': factor_df.to_dict('records')
        }

        compressed = zlib.compress(pickle.dumps(data))
        self.redis.setex(key, 3600, compressed)  # 1시간

        return data

    def _calculate_factors_vectorized(self, df: pd.DataFrame):
        """벡터화된 팩터 계산 (빠름!)"""

        # 한 번에 모든 팩터 계산
        df['PER'] = df['price'] / df['eps']
        df['PBR'] = df['price'] / df['book_value']
        df['MOMENTUM_3M'] = df.groupby('stock_code')['price'].pct_change(60)
        # ... 54개 팩터

        return df

    async def _run_lightweight_simulation(self, data, conditions):
        """경량화된 시뮬레이션 (메모리 효율적)"""

        # DataFrame 사용 (메모리 효율적)
        prices_df = pd.DataFrame(data['prices'])
        factors_df = pd.DataFrame(data['factors'])

        # Generator로 일별 처리 (메모리 절약!)
        holdings = {}
        cash = 100_000_000

        for date in prices_df['date'].unique():
            daily_prices = prices_df[prices_df['date'] == date]
            daily_factors = factors_df[factors_df['date'] == date]

            # 매수/매도 로직
            holdings, cash = self._process_trading_day(
                date, daily_prices, daily_factors,
                holdings, cash, conditions
            )

        return self._calculate_statistics(holdings, cash)
```

### 4단계: Celery + 전처리 조합

```python
# app/tasks/backtest_tasks.py

@celery_app.task(bind=True)
def prepare_data_background(self, date_range):
    """백그라운드에서 데이터 미리 준비"""

    # 인기있는 기간대 데이터 미리 캐싱
    common_ranges = [
        ('2023-01-01', '2023-12-31'),  # 1년
        ('2022-01-01', '2023-12-31'),  # 2년
        ('2020-01-01', '2023-12-31'),  # 3년
    ]

    for start, end in common_ranges:
        engine = OptimizedBacktestEngine(redis_client)
        await engine._prepare_and_cache_data((start, end), f"data:{start}:{end}")


@celery_app.task(bind=True)
def run_backtest_task(self, backtest_id, config):
    """최적화된 백테스트 Task"""

    engine = OptimizedBacktestEngine(redis_client)

    # 캐시된 데이터 사용 (빠름!)
    result = await engine.run_backtest_optimized(
        backtest_id=backtest_id,
        conditions=config['conditions'],
        date_range=(config['start_date'], config['end_date'])
    )

    return result
```

### 5단계: 메모리 최적화

```python
# 메모리 사용량 비교

# Before (최적화 전)
메모리: 3GB per backtest
16개 동시: 48GB

# After (최적화 후)
공유 데이터 (Redis): 5GB (압축, 모든 Worker 공유)
Worker 메모리: 500MB per backtest
16개 동시: 8GB + 5GB = 13GB ✅
```

## 📊 성능 비교

### 최적화 전
```python
# 각 백테스트마다 데이터 로드
DB 쿼리: 500K rows × 16 = 8M rows
메모리: 48GB
실행 시간: 5분/백테스트
```

### 최적화 후
```python
# 데이터 1회 준비, 재사용
DB 쿼리: 500K rows × 1 = 500K rows (16배 감소!)
메모리: 13GB (3.7배 감소!)
실행 시간: 30초/백테스트 (10배 빠름!)
```

## 🎯 결론: Kafka vs Celery (재평가)

### 100명 동시 백테스트

#### ❌ Kafka 여전히 불필요
- Kafka는 **메시지 큐**일 뿐
- **메모리/CPU/데이터 문제는 해결 못함**
- Kafka Consumer도 결국 같은 데이터 로드 필요

#### ✅ 올바른 해결책
1. **데이터 전처리 + Redis 캐싱** (가장 중요!)
2. **벡터화 연산** (Pandas/NumPy)
3. **메모리 효율적 알고리즘**
4. **Celery로 작업 분산**

### 최종 아키텍처

```yaml
# docker-compose.yml
services:
  # Redis (대용량 캐시)
  redis:
    image: redis:7
    command: redis-server --maxmemory 10gb --maxmemory-policy lru
    volumes:
      - redis_data:/data

  # Data Preparation (백그라운드)
  data-prep:
    build: .
    command: celery -A app.tasks.data_prep worker
    environment:
      - CELERY_QUEUE=data-preparation

  # Backtest Workers
  worker:
    build: .
    command: celery -A app.tasks.backtest_tasks worker --concurrency=2
    environment:
      - CELERY_QUEUE=backtest
    deploy:
      replicas: 4  # 8개 동시 백테스트

  # API
  api:
    build: .
    ports:
      - "8000:8000"
```

### 성능 예상
```
데이터 준비 시간: 5분 (1회만, 백그라운드)
백테스트 실행: 30초/개
동시 처리: 8개

100명 요청 → 약 6분 내 모두 완료
(100 ÷ 8 = 12.5 배치 × 30초 = 6.25분)

충분히 빠름! ✅
```

## 💡 핵심 인사이트

### Kafka가 해결하는 것:
- ✅ 메시지 큐잉
- ✅ 이벤트 스트리밍
- ✅ 메시지 순서 보장

### Kafka가 해결 못하는 것:
- ❌ 데이터 중복 로딩
- ❌ 메모리 사용량
- ❌ CPU 병목
- ❌ DB 부하

### 진짜 필요한 것:
- ✅ **데이터 캐싱** (Redis)
- ✅ **전처리 분리**
- ✅ **벡터화 연산**
- ✅ **메모리 효율 알고리즘**
- ✅ Celery (작업 분산)

## 🚀 최종 답변

**100명 수준에서는 Kafka 불필요!**

**대신 이렇게 하세요:**
1. Redis로 데이터 캐싱 (가장 중요!)
2. 백그라운드에서 데이터 미리 준비
3. 벡터화 연산으로 최적화
4. Celery로 작업 분산

**이렇게 하면:**
- 메모리: 48GB → 13GB
- 속도: 5분 → 30초
- DB 부하: 16배 감소
- 비용: 저렴

**Kafka는 1000명+ 되고, 복잡한 이벤트 처리 필요할 때!**