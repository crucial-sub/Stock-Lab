# GenPort 백테스트 시스템 구현 계획

## 현재 상황 분석

### 완료된 작업
1. ✅ Critical Issues 3개 수정
   - 매도 조건 일별 체크
   - 매수 조건 AND 로직
   - 매도 슬리피지 적용

2. ✅ 기본 구조 생성
   - `backtest_genport_v2.py` (스키마)
   - `condition_evaluator.py` (논리식 파서)
   - `backtest_genport_v2.py` (DB 모델)

### 필요한 작업
1. **논리식 기반 조건 시스템 완성**
2. **주문/체결/포지션 추적 시스템**
3. **통계 계산 및 저장**
4. **API 엔드포인트 v2**

## 구현 순서

### Step 1: 기존 엔진 분석 및 개선점 도출
```python
# 현재 구조
backtest_genport_engine.py
- 단순 거래 기록
- 기본 통계만 계산
- 논리식 미지원

# 목표 구조
backtest_engine_v2.py
- 주문 → 체결 → 포지션 흐름
- 상세 통계 (월별/연도별/드로다운)
- 논리식 조건 지원
```

### Step 2: 데이터 흐름 재설계

#### 2.1 현재 흐름
```
매수 조건 체크 → 바로 매수 → trades 테이블에 저장
```

#### 2.2 새로운 흐름
```
1. 매수 조건 체크 (논리식)
2. 주문 생성 (orders)
3. 체결 시뮬레이션 (슬리피지, 부분체결)
4. 체결 기록 (executions)
5. 포지션 업데이트 (positions)
6. 포지션 히스토리 기록
7. 통계 업데이트
```

### Step 3: 구현 우선순위

#### Phase 1: 핵심 엔진 (1-2일)
1. **논리식 평가 엔진 완성**
   - `condition_evaluator.py` 개선
   - 테스트 케이스 작성

2. **새로운 백테스트 엔진**
   - `backtest_engine_v2.py` 생성
   - 주문/체결/포지션 로직

#### Phase 2: 데이터베이스 (1일)
3. **테이블 생성 스크립트**
   - `create_backtest_v2_tables.py`
   - 마이그레이션 전략

4. **데이터 저장 로직**
   - 트랜잭션 처리
   - 벌크 인서트 최적화

#### Phase 3: 통계 및 분석 (1-2일)
5. **통계 계산 모듈**
   - `statistics_calculator.py`
   - 월별/연도별/드로다운

6. **팩터 기여도 분석**
   - `factor_analyzer.py`
   - 상관관계 분석

#### Phase 4: API 및 통합 (1일)
7. **API 엔드포인트 v2**
   - `backtest_genport_v2.py` (endpoints)
   - Swagger 문서화

8. **통합 테스트**
   - 전체 플로우 테스트
   - 성능 측정

## 구체적 구현 내용

### 1. 논리식 처리 예시
```python
# API 요청
{
    "buy_expression": {
        "expression": "(A and B) or (C and D)",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 15},
            {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
            {"id": "C", "factor": "PBR", "operator": "<", "value": 1},
            {"id": "D", "factor": "MOMENTUM_3M", "operator": ">", "value": 0}
        ]
    }
}

# 처리 로직
for stock in universe:
    results = {}
    for condition in conditions:
        results[condition.id] = evaluate_condition(stock, condition)

    if evaluate_expression(expression, results):
        create_buy_order(stock)
```

### 2. 주문/체결 추적
```python
# 주문 생성
order = create_order(
    stock_code="005930",
    order_type="MARKET",
    quantity=100,
    factor_scores=current_factors
)

# 체결 시뮬레이션
execution = simulate_execution(
    order=order,
    market_price=65000,
    slippage=0.001
)

# 포지션 업데이트
position = update_position(
    execution=execution,
    current_positions=positions
)
```

### 3. SQLAlchemy 최적화
```python
# 기존 방식 (느림)
for stock in stocks:
    price = db.query(StockPrice).filter(...).first()

# 개선 방식 (빠름)
query = select(StockPrice).where(...)
result = await db.execute(query)
prices_df = pd.DataFrame(result.mappings().all())

# Polars 사용 (더 빠름)
import polars as pl
prices_df = pl.DataFrame(result.mappings().all())
```

### 4. 통계 계산 최적화
```python
# 일별 → 월별 집계
daily_df = pd.DataFrame(daily_snapshots)
daily_df['date'] = pd.to_datetime(daily_df['date'])
daily_df['year_month'] = daily_df['date'].dt.to_period('M')

monthly_stats = daily_df.groupby('year_month').agg({
    'return': 'sum',
    'trades': 'sum',
    'portfolio_value': 'last'
})

# 드로다운 계산
cumulative_returns = (1 + daily_returns).cumprod()
running_max = cumulative_returns.expanding().max()
drawdown = (cumulative_returns - running_max) / running_max
```

## 예상 결과물

### 1. 파일 구조
```
app/
├── services/
│   ├── backtest_engine_v2.py       # 새 엔진
│   ├── condition_evaluator.py      # 논리식 파서
│   ├── statistics_calculator.py    # 통계 계산
│   └── factor_analyzer.py          # 팩터 분석
├── models/
│   └── backtest_genport_v2.py      # DB 모델
├── schemas/
│   └── backtest_genport_v2.py      # Pydantic 스키마
└── api/v2/endpoints/
    └── backtest.py                  # API 엔드포인트
```

### 2. 데이터베이스 구조
```sql
-- 15개 테이블
-- 주문/체결/포지션 추적
-- 일별/월별/연도별 통계
-- 드로다운 기간
-- 팩터 기여도
```

### 3. API 응답 예시
```json
{
    "backtest_id": "uuid",
    "total_return": 21.35,
    "sharpe_ratio": 1.82,
    "max_drawdown": -7.62,
    "monthly_statistics": [...],
    "factor_contributions": [
        {
            "factor": "PER",
            "win_rate": 65.3,
            "contribution_score": 45.2,
            "importance_rank": 1
        }
    ],
    "positions": [...],
    "chart_data": {...}
}
```

## 다음 단계

1. **즉시 시작**: 논리식 파서 완성 및 테스트
2. **오늘 중**: 새 백테스트 엔진 핵심 로직
3. **내일**: 통계 계산 및 DB 저장
4. **모레**: API 통합 및 테스트

## 위험 요소 및 대응

1. **기존 시스템 호환성**
   - v1, v2 병행 운영
   - 점진적 마이그레이션

2. **성능 이슈**
   - Polars 도입
   - 비동기 처리 최적화
   - 캐싱 전략

3. **데이터 정합성**
   - 트랜잭션 처리
   - 검증 로직 강화