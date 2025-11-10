# ⚡ Tick 기반 백테스트 아키텍처

## 🔥 데이터 규모 비교

### 일봉 기반 (현재)
```python
# 1년 백테스트
종목: 2,000개
거래일: 250일
데이터 포인트: 2,000 × 250 = 500,000개
데이터 크기: ~100MB
처리 시간: 30초 - 5분
```

### Tick 기반 (체결 단위)
```python
# 1일 백테스트만 해도...
종목: 2,000개
거래시간: 6시간 (09:00-15:30)
평균 Tick: 100개/종목/분
Tick 수: 2,000 × 360분 × 100 = 72,000,000개/일

# 1년이면
72M × 250일 = 18,000,000,000개 (180억 개!) 😱
데이터 크기: ~1-2TB
처리 시간: ???
```

## 🚨 Tick 기반의 도전 과제

### 1. 데이터 저장 문제
```python
# PostgreSQL로는 불가능!
18B rows × 평균 100 bytes = 1.8TB

# 쿼리 한 번에
SELECT * FROM tick_data WHERE date = '2023-01-01'
→ 72M rows 읽기 → 타임아웃!
```

### 2. 메모리 폭발
```python
# 하루치 데이터만 메모리에 올리면
72M rows × 100 bytes = 7.2GB (하루만!)

# 1년치는?
250일 × 7.2GB = 1.8TB 😱😱😱
서버 메모리 초과!
```

### 3. 처리 시간
```python
# 초당 100만개 처리해도
18B ÷ 1M = 18,000초 = 5시간!

# 실제로는 더 느림 (조건 평가, 거래 시뮬레이션 등)
예상 시간: 10-20시간/백테스트
```

## ✅ Tick 기반이라면: Kafka + 시계열 DB 필수!

### 아키텍처

```
┌─────────────────────────────────────────────────────┐
│              Tick Data Ingestion                     │
│   (실시간 체결 데이터 수집 - Kafka Producer)        │
└────────────┬────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│                  Kafka Cluster                       │
│   Topic: tick-data (Partitioned by Stock Code)      │
│   Retention: 7 days (압축)                          │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┼────────────┐
    ▼        ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐
│Consumer│ │Consumer│ │Consumer│
│Group 1 │ │Group 2 │ │Group 3 │
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     ▼          ▼          ▼
┌──────────────────────────────────────┐
│      TimescaleDB / ClickHouse        │
│  (시계열 데이터베이스 - 초고속)     │
│  - Hypertables (자동 파티셔닝)      │
│  - Columnar Storage (압축)          │
│  - Continuous Aggregates            │
└──────────────────────────────────────┘
```

### 왜 Kafka가 필요한가?

#### 1. 실시간 Tick 데이터 스트리밍
```python
# 거래소에서 초당 수십만 Tick 발생
초당 Tick: 300,000개
분당 Tick: 18,000,000개
하루 Tick: 72,000,000개

# Kafka만 이 속도를 감당 가능
Kafka 처리량: 초당 수백만 메시지
Redis Queue: 초당 수만 개 (부족!)
```

#### 2. 파티셔닝으로 병렬 처리
```python
# Kafka Topic Partitioning
Topic: tick-data
Partitions:
  - Partition 0: 005930 (삼성전자)
  - Partition 1: 000660 (SK하이닉스)
  - Partition 2: 035420 (NAVER)
  ...

# Consumer Group이 병렬로 처리
Consumer 1 → Partition 0-99
Consumer 2 → Partition 100-199
Consumer 3 → Partition 200-299
...
```

#### 3. Replay 가능 (백테스트 핵심!)
```python
# Kafka는 메시지를 보관
# 백테스트 = 과거 Tick 데이터 Replay

# 2023-01-01 00:00:00부터 Replay
kafka_consumer = KafkaConsumer(
    'tick-data',
    auto_offset_reset='earliest',
    enable_auto_commit=False
)

# 시간 순서대로 Tick 처리
for tick in kafka_consumer:
    process_tick(tick)
```

## 🏗️ Tick 기반 백테스트 스택

### Stack 1: 시계열 DB (필수!)

#### TimescaleDB (PostgreSQL 확장)
```sql
-- Hypertable 생성 (자동 파티셔닝)
CREATE TABLE tick_data (
    time TIMESTAMPTZ NOT NULL,
    stock_code VARCHAR(10),
    price DECIMAL(10, 2),
    volume INTEGER,
    bid_price DECIMAL(10, 2),
    ask_price DECIMAL(10, 2)
);

-- Hypertable로 변환
SELECT create_hypertable('tick_data', 'time');

-- 자동 압축 (오래된 데이터)
ALTER TABLE tick_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'stock_code'
);

-- 빠른 쿼리
SELECT * FROM tick_data
WHERE time BETWEEN '2023-01-01' AND '2023-01-02'
AND stock_code = '005930'
ORDER BY time
-- Partition pruning으로 초고속!
```

**장점:**
- PostgreSQL 호환
- SQL 사용 가능
- 자동 파티셔닝
- 압축 (10:1)

#### ClickHouse (더 빠름!)
```sql
-- 테이블 생성
CREATE TABLE tick_data (
    time DateTime,
    stock_code String,
    price Decimal(10, 2),
    volume UInt32
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(time)
ORDER BY (stock_code, time);

-- 초고속 쿼리
SELECT
    stock_code,
    avg(price),
    sum(volume)
FROM tick_data
WHERE time >= '2023-01-01'
GROUP BY stock_code
-- 180억 rows를 초 단위로 처리!
```

**장점:**
- 컬럼 저장 (압축 50:1)
- 초고속 (TimescaleDB보다 10배 빠름)
- 수평 확장

**단점:**
- SQL 약간 다름
- 트랜잭션 없음

### Stack 2: Kafka + Flink (실시간 처리)

```python
# Apache Flink (스트림 처리)
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer

env = StreamExecutionEnvironment.get_execution_environment()

# Kafka에서 Tick 스트림
kafka_consumer = FlinkKafkaConsumer(
    topics='tick-data',
    deserialization_schema=...,
    properties={'bootstrap.servers': 'localhost:9092'}
)

tick_stream = env.add_source(kafka_consumer)

# 실시간 집계
tick_stream \
    .key_by(lambda x: x['stock_code']) \
    .window(TumblingProcessingTimeWindows.of(Time.seconds(1))) \
    .aggregate(TickAggregator()) \
    .add_sink(...)

env.execute()
```

### Stack 3: DuckDB (분석용)

```python
# Parquet 파일로 저장 후 DuckDB로 분석
import duckdb

# 1TB 데이터도 빠르게 쿼리
con = duckdb.connect()

result = con.execute("""
    SELECT
        stock_code,
        date_trunc('minute', time) as minute,
        avg(price) as avg_price,
        sum(volume) as total_volume
    FROM read_parquet('tick_data/*.parquet')
    WHERE time >= '2023-01-01'
    GROUP BY stock_code, minute
""").fetchdf()

# Pandas DataFrame으로 백테스트
```

## 📊 Tick 백테스트 성능 비교

### PostgreSQL (현재)
```
데이터: 500K rows (일봉)
쿼리 시간: 0.1초
백테스트: 5분
✅ 일봉에는 적합
❌ Tick에는 불가능
```

### TimescaleDB + Kafka
```
데이터: 18B rows (Tick)
쿼리 시간: 1-5초 (Hypertable)
백테스트: 1-2시간
✅ Tick 가능
⚠️ 비용 높음
```

### ClickHouse + Kafka + Flink
```
데이터: 18B rows (Tick)
쿼리 시간: 0.1-1초
백테스트: 10-30분
✅ Tick 최적
✅ 실시간 처리
❌ 복잡도 매우 높음
```

## 💰 비용 비교 (Tick 기반)

### 최소 구성
```
- ClickHouse (3 nodes): $300/월
- Kafka (3 brokers): $200/월
- Flink (2 workers): $150/월
- S3 (스토리지): $100/월
- EC2 (API): $50/월
총: $800-1000/월
```

### 프로덕션 구성
```
- ClickHouse Cluster (9 nodes): $900/월
- Kafka Cluster (5 brokers): $400/월
- Flink Cluster (5 workers): $400/월
- S3 (스토리지): $300/월
- Load Balancer: $50/월
총: $2000-3000/월
```

## 🎯 Tick 백테스트 구현 예시

### 1. Kafka Producer (Tick 수집)
```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# 실시간 Tick 전송
def send_tick(stock_code, price, volume, timestamp):
    tick = {
        'stock_code': stock_code,
        'price': price,
        'volume': volume,
        'timestamp': timestamp.isoformat()
    }
    producer.send('tick-data', value=tick, key=stock_code.encode())
```

### 2. Kafka Consumer (Tick 저장)
```python
from kafka import KafkaConsumer
import clickhouse_driver

consumer = KafkaConsumer(
    'tick-data',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=False
)

client = clickhouse_driver.Client('localhost')

# Batch insert (성능 최적화)
batch = []
for message in consumer:
    tick = json.loads(message.value)
    batch.append(tick)

    if len(batch) >= 10000:
        # Bulk insert
        client.execute(
            'INSERT INTO tick_data VALUES',
            batch
        )
        batch = []
        consumer.commit()
```

### 3. Tick 백테스트 엔진
```python
class TickBacktestEngine:
    """Tick 기반 백테스트 엔진"""

    def __init__(self, clickhouse_client):
        self.db = clickhouse_client

    async def run_tick_backtest(
        self,
        stock_code: str,
        start_time: datetime,
        end_time: datetime,
        strategy: callable
    ):
        """Tick 단위 백테스트"""

        # 스트리밍 쿼리 (메모리 절약)
        query = f"""
        SELECT time, price, volume
        FROM tick_data
        WHERE stock_code = '{stock_code}'
        AND time BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY time
        """

        # Generator로 Tick 하나씩 처리 (메모리 효율적)
        tick_stream = self.db.execute_iter(query)

        position = None
        cash = 100_000_000
        trades = []

        for tick in tick_stream:
            time, price, volume = tick

            # 전략 시그널
            signal = strategy(tick, position)

            # 매수
            if signal == 'BUY' and position is None:
                shares = cash // price
                position = {
                    'entry_time': time,
                    'entry_price': price,
                    'shares': shares
                }
                cash -= shares * price
                trades.append(('BUY', time, price, shares))

            # 매도
            elif signal == 'SELL' and position:
                cash += position['shares'] * price
                trades.append(('SELL', time, price, position['shares']))
                position = None

        return {
            'trades': trades,
            'final_cash': cash,
            'final_position': position
        }
```

### 4. 실시간 전략 시그널
```python
def momentum_strategy(tick, position):
    """Tick 기반 모멘텀 전략"""

    # 최근 100 Tick의 이동평균
    recent_prices = get_recent_ticks(tick['stock_code'], 100)
    ma = sum(recent_prices) / len(recent_prices)

    # 매수 시그널
    if tick['price'] > ma * 1.02 and position is None:
        return 'BUY'

    # 매도 시그널
    if position and tick['price'] < position['entry_price'] * 0.98:
        return 'SELL'  # 2% 손절

    return 'HOLD'
```

## 📊 결론

### 일봉 기반 (현재)
```
데이터: 500K rows
DB: PostgreSQL ✅
Queue: Celery + Redis ✅
비용: $130/월 ✅
```

### Tick 기반
```
데이터: 18B rows
DB: ClickHouse / TimescaleDB 필수! ✅
Queue: Kafka 필수! ✅
Stream: Flink 권장 ✅
비용: $1000-3000/월 ⚠️
```

## 🎯 최종 답변

### 현재 프로젝트 (일봉)
- ❌ Kafka 불필요
- ✅ Celery + Redis + PostgreSQL

### Tick 기반으로 확장 시
- ✅ **Kafka 필수!**
- ✅ **ClickHouse / TimescaleDB 필수!**
- ✅ **Flink 권장**
- 💰 **비용 10배 증가**

**Tick 기반은 완전히 다른 프로젝트입니다!** 🚀

**현재는 일봉으로 시작하고, 수익 발생 후 Tick으로 확장하세요.**