# GenPort 백테스트 v2 사용 가이드

## 완료된 구현 내용

### ✅ Phase 1: 논리식 조건 통합
- `condition_evaluator.py` 구현 완료
- 논리식 파서 (`LogicalExpressionParser`) 구현
- 백테스트 엔진에 통합

### ✅ Phase 2: 주문/체결/포지션 추적
- `create_order()` - 주문 생성 및 추적
- `execute_order()` - 체결 시뮬레이션
- `update_position()` - 포지션 관리
- `track_position_history()` - 포지션 히스토리 추적

### ✅ Phase 3: 통계 계산 강화
- `calculate_monthly_stats()` - 월별 통계
- `calculate_yearly_stats()` - 연도별 통계
- `calculate_drawdown_periods()` - 드로다운 기간 분석
- `analyze_factor_contributions()` - 팩터 기여도 분석

### ✅ Phase 4: DB 스키마 확장
- 10개의 새로운 테이블 추가
- 주문/체결/포지션 추적 테이블
- 상세 통계 테이블

---

## 사용 예시

### 1. 논리식 조건 사용

#### 1.1 간단한 AND 조건
```python
# 기존 방식 (여전히 지원)
buy_conditions = [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
]
```

#### 1.2 논리식 조건 (새로운 방식)
```python
# (A and B) or C 형태
buy_conditions = {
    "expression": "(A and B) or C",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
    ],
    "factor_weights": {  # 선택적: 팩터 스코어링용
        "PER": -1,  # 낮을수록 좋음
        "ROE": 1,   # 높을수록 좋음
        "MOMENTUM_3M": 1
    }
}
```

#### 1.3 복잡한 논리식
```python
buy_conditions = {
    "expression": "(A and B and C) or (D and E) or F",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "PBR", "operator": "<", "value": 1},
        {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 50},
        {"id": "D", "factor": "ROE", "operator": ">", "value": 15},
        {"id": "E", "factor": "ROA", "operator": ">", "value": 10},
        {"id": "F", "factor": "MOMENTUM_12M", "operator": ">", "value": 30}
    ]
}
```

### 2. 백테스트 실행

```python
from app.services.backtest_genport_engine import GenPortBacktestEngine
from app.core.database import get_db
from uuid import uuid4
from datetime import date
from decimal import Decimal

async def run_backtest_example():
    async with get_db() as db:
        engine = GenPortBacktestEngine(db)

        # 논리식 조건
        buy_conditions = {
            "expression": "(A and B) or C",
            "conditions": [
                {"id": "A", "factor": "PER", "operator": "<", "value": 15},
                {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
                {"id": "C", "factor": "PBR", "operator": "<", "value": 1}
            ]
        }

        # 매도 조건
        sell_conditions = [
            {"type": "STOP_LOSS", "value": 10},  # 10% 손절
            {"type": "TAKE_PROFIT", "value": 20},  # 20% 익절
            {"type": "HOLD_DAYS", "value": 60}  # 60일 보유
        ]

        # 백테스트 실행
        result = await engine.run_backtest(
            backtest_id=uuid4(),
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=Decimal("100000000"),
            rebalance_frequency="MONTHLY",
            max_positions=20,
            position_sizing="EQUAL_WEIGHT",
            commission_rate=0.00015,
            slippage=0.001
        )

        # 추가 통계 계산
        monthly_stats = engine.calculate_monthly_stats(
            result.daily_performance,
            result.trades
        )

        yearly_stats = engine.calculate_yearly_stats(monthly_stats)

        drawdown_periods = engine.calculate_drawdown_periods(
            result.daily_performance
        )

        factor_contributions = engine.analyze_factor_contributions(
            result.trades,
            buy_conditions
        )

        print(f"총 수익률: {result.statistics.total_return}%")
        print(f"샤프 비율: {result.statistics.sharpe_ratio}")
        print(f"최대 낙폭: {result.statistics.max_drawdown}%")
        print(f"승률: {result.statistics.win_rate}%")

        # 월별 통계
        for stat in monthly_stats:
            print(f"{stat['year']}-{stat['month']:02d}: "
                  f"수익률 {stat['return_rate']:.2f}%, "
                  f"승률 {stat['win_rate']:.1f}%")

        # 팩터 기여도
        for factor, contrib in factor_contributions.items():
            print(f"{factor}: "
                  f"승률 {contrib['win_rate']:.1f}%, "
                  f"기여도 {contrib['contribution_score']:.1f}%, "
                  f"순위 {contrib['importance_rank']}")

        return result
```

### 3. 주문/체결/포지션 추적 예시

```python
from datetime import datetime

# 엔진 내부에서 자동으로 호출됨
async def simulate_trading_example(engine, stock_code, price, quantity):
    # 1. 주문 생성
    order = engine.create_order(
        stock_code=stock_code,
        stock_name=f"Stock_{stock_code}",
        order_side="BUY",
        quantity=quantity,
        order_date=datetime.now(),
        reason="Factor conditions met",
        factor_scores={"PER": 12.5, "ROE": 15.3},
        condition_results={"A": True, "B": True, "C": False}
    )

    # 2. 체결 시뮬레이션
    execution = engine.execute_order(
        order=order,
        market_price=Decimal(str(price)),
        slippage=Decimal("0.001"),
        commission_rate=Decimal("0.00015")
    )

    # 3. 포지션 업데이트
    position = engine.update_position(
        execution=execution,
        order=order,
        current_date=date.today(),
        factor_scores=order.factor_scores
    )

    print(f"주문 ID: {order.order_id}")
    print(f"체결가: {execution.price}")
    print(f"포지션: {position.stock_code} x {position.quantity}")

    return position
```

### 4. API 요청 예시

#### 4.1 백테스트 생성 (논리식 조건)
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "buy_conditions": {
      "expression": "(A and B) or C",
      "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
      ]
    },
    "sell_conditions": [
      {"type": "STOP_LOSS", "value": 10},
      {"type": "TAKE_PROFIT", "value": 20}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000000,
    "rebalance_frequency": "MONTHLY",
    "max_positions": 20,
    "commission_rate": 0.00015,
    "slippage": 0.001
  }'
```

#### 4.2 백테스트 조회
```bash
curl "http://localhost:8000/api/v1/backtest/backtest/{backtest_id}"
```

### 5. 데이터베이스 테이블 생성

```bash
# v2 테이블 생성
python scripts/create_backtest_v2_tables.py
```

---

## 주요 개선사항

### 1. 논리식 지원
- **이전**: 모든 조건을 AND로만 연결
- **현재**: `(A and B) or C` 같은 복잡한 논리식 지원

### 2. 완전한 거래 추적
- **이전**: 거래만 기록
- **현재**: 주문 → 체결 → 포지션 전체 라이프사이클 추적

### 3. 상세 통계
- **이전**: 기본 통계만 제공
- **현재**: 월별/연도별/드로다운/팩터 기여도 분석

### 4. 실시간 포지션 관리
- **이전**: 단순 보유 종목 리스트
- **현재**: 포지션별 손익, 최대 이익/손실, 보유 기간 추적

---

## 테스트 시나리오

### 시나리오 1: Value + Quality 전략
```python
buy_conditions = {
    "expression": "A and B and C",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 10},
        {"id": "B", "factor": "PBR", "operator": "<", "value": 1},
        {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 30}
    ]
}
```

### 시나리오 2: Growth OR Momentum 전략
```python
buy_conditions = {
    "expression": "(A and B) or (C and D)",
    "conditions": [
        {"id": "A", "factor": "REVENUE_GROWTH", "operator": ">", "value": 20},
        {"id": "B", "factor": "EARNINGS_GROWTH", "operator": ">", "value": 15},
        {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 10},
        {"id": "D", "factor": "MOMENTUM_6M", "operator": ">", "value": 15}
    ]
}
```

### 시나리오 3: 복합 전략
```python
buy_conditions = {
    "expression": "(A and B and not C) or (D and E)",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "DEBT_RATIO", "operator": ">", "value": 50},
        {"id": "D", "factor": "MOMENTUM_12M", "operator": ">", "value": 20},
        {"id": "E", "factor": "MARKET_CAP", "operator": ">", "value": 1000000000000}
    ]
}
```

---

## 성능 최적화 팁

### 1. SQLAlchemy → DataFrame 변환
```python
# 최적화된 방법
result = await db.execute(query)
df = pd.DataFrame(result.mappings().all())  # ✅ 빠름

# Polars 사용 (더 빠름)
import polars as pl
df = pl.DataFrame(result.mappings().all())  # ✅ 매우 빠름
```

### 2. 병렬 처리
```python
# 팩터 계산 병렬화
tasks = [
    calculate_value_factors(data),
    calculate_momentum_factors(data),
    calculate_quality_factors(data)
]
results = await asyncio.gather(*tasks)
```

### 3. 캐싱 활용
```python
# Redis 캐싱 (이미 구현됨)
from app.core.cache import cache

cached_data = await cache.get(f"factors:{date}")
if not cached_data:
    factors = await calculate_factors(date)
    await cache.set(f"factors:{date}", factors, expire=3600)
```

---

## 트러블슈팅

### 문제 1: 논리식 파싱 에러
```python
# 문제
expression = "A and B or"  # 불완전한 식

# 해결
expression = "A and (B or C)"  # 올바른 식
```

### 문제 2: 메모리 부족
```python
# 문제
df = pd.DataFrame(huge_data)  # 메모리 초과

# 해결
for chunk in pd.read_sql(query, con, chunksize=10000):
    process(chunk)
```

### 문제 3: 느린 백테스트
```python
# 문제
for date in dates:
    for stock in stocks:
        calculate_factor(stock, date)  # O(n²)

# 해결
# 벡터화된 연산 사용
df['PER'] = df['price'] / df['eps']  # O(n)
```

---

## 다음 단계

### 추가 개발 가능 항목
1. **실시간 백테스트**: WebSocket을 통한 실시간 진행상황 전송
2. **백테스트 비교**: 여러 백테스트 결과 비교 기능
3. **최적화**: 파라미터 최적화 (Grid Search, Bayesian Optimization)
4. **리포트 생성**: PDF/Excel 리포트 자동 생성
5. **알림**: 특정 조건 달성 시 알림 (Slack, Email)

---

## 결론

GenPort 스타일의 백테스트 시스템이 성공적으로 구현되었습니다:

✅ **논리식 조건 지원** - 복잡한 투자 전략 표현 가능
✅ **완전한 거래 추적** - 주문부터 포지션까지 전체 라이프사이클
✅ **상세 통계 분석** - 월별/연도별/드로다운/팩터 기여도
✅ **확장 가능한 구조** - 새로운 기능 추가 용이

이제 GenPort와 동등한 수준의 백테스트 분석이 가능합니다!