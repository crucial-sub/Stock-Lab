# 🚀 백테스트 시스템 확장성 가이드

## 📊 동시성 요구사항 분석

### 현재 요구사항
- **동시 접속**: 100명
- **동시 백테스트**: 100개 (최악의 경우)
- **백테스트 소요 시간**: 2-5분 (예상)
- **데이터 크기**: 중간 규모

## 🎯 Kafka가 필요한가?

### ❌ **100명 수준에서는 Kafka 불필요**

#### 이유:
1. **오버엔지니어링**: Kafka는 수천~수만 TPS를 처리하기 위한 도구
2. **복잡도 증가**: Kafka 클러스터 관리 비용 > 얻는 이득
3. **비용**: Kafka 인프라 추가 비용
4. **학습 곡선**: Kafka 운영 전문성 필요

### ✅ **대신 이렇게 하세요**

## 1단계: Celery + Redis (추천) 👍

### 아키텍처
```
                    ┌─────────────┐
                    │   FastAPI   │
                    │   (API)     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │   (Queue)   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐      ┌─────────┐
   │ Worker 1│        │ Worker 2│      │ Worker N│
   │(Celery) │        │(Celery) │      │(Celery) │
   └─────────┘        └─────────┘      └─────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    ┌─────────────┐
                    │ PostgreSQL  │
                    │   (결과)    │
                    └─────────────┘
```

### 장점:
- ✅ **간단**: 빠른 구현 (1-2일)
- ✅ **검증됨**: 업계 표준
- ✅ **확장 가능**: Worker 추가로 수평 확장
- ✅ **모니터링**: Flower로 쉬운 모니터링
- ✅ **비용 효율적**: Redis만 추가

### 구현 예시

#### 1. Celery 설정
```python
# app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    'backtest',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,

    # 동시성 설정
    worker_concurrency=4,  # Worker당 4개 작업 동시 처리
    worker_prefetch_multiplier=1,

    # 타임아웃
    task_time_limit=600,  # 10분
    task_soft_time_limit=540,  # 9분
)
```

#### 2. 백테스트 Task
```python
# app/tasks/backtest_tasks.py
from app.core.celery_app import celery_app
from app.services.backtest import BacktestEngineGenPort

@celery_app.task(bind=True)
def run_backtest_async(self, backtest_id: str, config: dict):
    """비동기 백테스트 실행"""

    # 진행상황 업데이트
    self.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': 100, 'status': 'Starting...'}
    )

    try:
        # 백테스트 실행
        engine = BacktestEngineGenPort(db)
        result = await engine.run_backtest(**config)

        # 진행상황 업데이트
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Completed'}
        )

        return {
            'status': 'COMPLETED',
            'backtest_id': backtest_id,
            'result': result.dict()
        }

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
```

#### 3. API 엔드포인트 수정
```python
# app/api/v1/backtest.py
from app.tasks.backtest_tasks import run_backtest_async

@router.post("/backtest")
async def create_backtest(request: BacktestCreateRequest):
    """백테스트 생성 및 비동기 실행"""

    backtest_id = uuid4()

    # Celery Task로 비동기 실행
    task = run_backtest_async.delay(
        backtest_id=str(backtest_id),
        config=request.dict()
    )

    # Task ID 저장 (진행상황 조회용)
    await save_task_mapping(backtest_id, task.id)

    return {
        "backtest_id": backtest_id,
        "task_id": task.id,
        "status": "QUEUED",
        "message": "Backtest queued for processing"
    }

@router.get("/backtest/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """백테스트 진행상황 조회"""

    task_id = await get_task_id(backtest_id)
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {"status": "QUEUED", "progress": 0}
    elif task.state == 'PROGRESS':
        return {
            "status": "RUNNING",
            "progress": task.info.get('current', 0),
            "message": task.info.get('status', '')
        }
    elif task.state == 'SUCCESS':
        return {"status": "COMPLETED", "progress": 100}
    elif task.state == 'FAILURE':
        return {"status": "FAILED", "error": str(task.info)}
```

#### 4. Worker 실행
```bash
# Worker 시작 (4개 프로세스)
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=prefork

# Flower 모니터링 (선택)
celery -A app.core.celery_app flower --port=5555
```

### 성능 계산
```
Worker 수: 4개
Worker당 동시 작업: 4개
총 동시 처리: 16개 백테스트

백테스트 소요 시간: 3분 평균
시간당 처리량: 16 * (60분 / 3분) = 320개/시간

100명이 동시 요청 → 대기 시간: 최대 18분
(100명 ÷ 16 = 6.25 배치 × 3분 = 18.75분)
```

## 2단계: 더 빠른 처리가 필요하다면?

### 옵션 1: Worker 증설
```bash
# EC2 인스턴스 추가 (수평 확장)
# 서버 1: Worker 4개
# 서버 2: Worker 4개
# 서버 3: Worker 4개
# → 총 48개 동시 백테스트
```

### 옵션 2: 우선순위 큐
```python
# VIP 사용자는 우선 처리
@celery_app.task(priority=9)  # 높은 우선순위
def run_vip_backtest(backtest_id, config):
    pass

@celery_app.task(priority=1)  # 낮은 우선순위
def run_normal_backtest(backtest_id, config):
    pass
```

### 옵션 3: 백테스트 최적화
```python
# 1. 팩터 계산 캐싱
@lru_cache(maxsize=1000)
def calculate_factors(date, stock_code):
    pass

# 2. 벡터화 연산
df['PER'] = df['price'] / df['eps']  # 한번에 계산

# 3. 병렬 처리
async with asyncio.TaskGroup() as tg:
    for date in dates:
        tg.create_task(process_date(date))
```

## 3단계: 1000명+ 수준이라면?

### 이제 Kafka 고려 시점

```
                ┌──────────────┐
                │   FastAPI    │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    Kafka     │
                │  (메시지큐)  │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐     ┌────────┐    ┌────────┐
   │Consumer│     │Consumer│    │Consumer│
   │Group 1 │     │Group 2 │    │Group 3 │
   └────────┘     └────────┘    └────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │  결과 저장소    │
              └─────────────────┘
```

### Kafka 장점 (대규모)
- ✅ 초당 수만 메시지 처리
- ✅ 메시지 영구 저장
- ✅ 이벤트 스트리밍
- ✅ 복잡한 이벤트 처리

### Kafka 단점
- ❌ 복잡한 설정
- ❌ 높은 운영 비용
- ❌ Zookeeper 필요 (Kafka 2.x)
- ❌ 학습 곡선

## 4단계: 캐싱 전략 (필수!)

### Redis 캐싱
```python
# app/core/cache.py
import redis
import pickle

redis_client = redis.Redis(host='localhost', port=6379)

async def get_cached_factors(date: str):
    """팩터 데이터 캐싱"""
    key = f"factors:{date}"
    cached = redis_client.get(key)

    if cached:
        return pickle.loads(cached)

    # 계산
    factors = await calculate_all_factors(date)

    # 캐시 저장 (1시간)
    redis_client.setex(key, 3600, pickle.dumps(factors))

    return factors
```

## 📊 단계별 전략 요약

### Phase 1: 100명 수준 (현재)
```
✅ Celery + Redis
✅ Worker 4-8개
✅ 기본 캐싱
총 비용: $50-100/월
개발 기간: 2-3일
```

### Phase 2: 500명 수준
```
✅ Celery + Redis (확장)
✅ Worker 16-32개 (여러 서버)
✅ Redis Cluster
✅ 고급 캐싱
총 비용: $200-300/월
개발 기간: 1주
```

### Phase 3: 1000명+ 수준
```
✅ Kafka + Consumer Groups
✅ Auto-scaling Workers
✅ Redis Cluster
✅ CDN + Edge Caching
총 비용: $500-1000/월
개발 기간: 2-3주
```

## 🎯 추천 솔루션 (100명 기준)

### 최소 구성 (MVP)
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Redis (큐 + 캐시)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # FastAPI
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres

  # Celery Worker (4개)
  worker:
    build: .
    command: celery -A app.core.celery_app worker --concurrency=4
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 2  # 2개 컨테이너 = 8개 동시 백테스트

  # Flower (모니터링)
  flower:
    build: .
    command: celery -A app.core.celery_app flower
    ports:
      - "5555:5555"
    depends_on:
      - redis

  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: stocklab
      POSTGRES_PASSWORD: password

volumes:
  redis_data:
  postgres_data:
```

### 실행
```bash
# 전체 시스템 시작
docker-compose up -d

# Worker 스케일링 (필요시)
docker-compose up -d --scale worker=4  # 16개 동시 처리
```

## 💰 비용 비교

### Celery + Redis 구성
```
- EC2 t3.medium (API): $30/월
- EC2 t3.medium (Worker x2): $60/월
- ElastiCache Redis: $15/월
- RDS PostgreSQL: $25/월
총: $130/월
```

### Kafka 구성
```
- EC2 t3.medium (API): $30/월
- EC2 t3.large (Kafka x3): $210/월
- EC2 t3.medium (Worker x2): $60/월
- ElastiCache Redis: $15/월
- RDS PostgreSQL: $25/월
총: $340/월 (2.6배 비쌈!)
```

## 🏁 결론

### 100명 수준에서는:
1. ✅ **Celery + Redis** 사용
2. ✅ Worker 2-4개로 시작
3. ✅ 필요시 Worker만 증설
4. ✅ 캐싱 최적화
5. ❌ **Kafka는 불필요**

### Kafka를 고려할 시점:
- 동시 사용자 1000명+
- 초당 100+ 백테스트 요청
- 복잡한 이벤트 스트리밍 필요
- 메시지 영구 저장 필요
- 실시간 알림 시스템 구축

**지금은 Celery로 충분합니다!** 🚀