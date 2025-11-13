# GenPort 스타일 백테스트 시스템 설계

## 1. 시스템 개요

GenPort와 동일한 수준의 백테스트 시스템 구현
- **논리식 기반 조건 처리**: "A and B or C" 형태의 조건식
- **완전한 거래 추적**: orders → executions → positions
- **상세한 통계**: 월별/연도별/드로다운 분석
- **팩터 기여도 분석**: 어떤 팩터가 수익에 기여했는지

## 2. 핵심 개선사항

### 2.1 조건식 시스템
```python
# 기존 방식 (단순 AND)
buy_conditions = [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
]

# 새로운 방식 (논리식)
buy_conditions = {
    "expression": "(A and B) or C",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
    ]
}
```

### 2.2 데이터베이스 구조

#### 기존 구조 (6개 테이블)
```
backtest_sessions
backtest_conditions
backtest_statistics
backtest_daily_snapshots
backtest_trades
backtest_holdings
```

#### 새로운 구조 (15개 테이블)
```
# 핵심 테이블
backtest_sessions_v2        # 세션 정보 (확장)
backtest_orders             # 주문 (NEW)
backtest_executions         # 체결 (NEW)
backtest_positions          # 포지션 (NEW)
backtest_position_history   # 포지션 히스토리 (NEW)

# 통계 테이블
backtest_daily_snapshots_v2 # 일별 스냅샷 (확장)
backtest_monthly_stats      # 월별 통계 (NEW)
backtest_yearly_stats       # 연도별 통계 (NEW)
backtest_drawdown_periods   # 드로다운 기간 (NEW)
backtest_factor_contributions # 팩터 기여도 (NEW)

# 보조 테이블
backtest_rebalance_dates    # 리밸런싱 날짜 (NEW)
backtest_universe_stocks    # 유니버스 종목 (NEW)
backtest_factor_values      # 팩터 값 히스토리 (NEW)
backtest_sector_allocations # 섹터 배분 (NEW)
backtest_logs              # 실행 로그 (NEW)
```

### 2.3 처리 흐름 개선

#### 기존 흐름
```
1. 데이터 로드
2. 팩터 계산
3. 매수/매도 실행
4. 결과 저장
```

#### 새로운 흐름
```
1. 유니버스 설정 및 검증
2. 데이터 로드 (최적화)
3. 팩터 계산 및 저장
4. 주문 생성 (orders)
5. 체결 시뮬레이션 (executions)
6. 포지션 업데이트 (positions)
7. 포지션 히스토리 기록
8. 일별/월별/연도별 통계 계산
9. 드로다운 분석
10. 팩터 기여도 분석
11. 결과 저장 및 리포팅
```

## 3. SQLAlchemy → DataFrame 변환 최적화

### 3.1 현재 문제점
```python
# 비효율적인 방법
result = await db.execute(query)
stocks = result.scalars().all()
df = pd.DataFrame([s.__dict__ for s in stocks])
```

### 3.2 개선된 방법
```python
# 효율적인 방법
result = await db.execute(query)
rows = result.mappings().all()  # 딕셔너리 매핑 사용
df = pd.DataFrame(rows)  # 직접 변환

# Polars 사용 (더 빠름)
import polars as pl
df = pl.DataFrame(rows)
```

## 4. 논리식 파서 구현

### 4.1 파서 구조
```python
class LogicalExpressionParser:
    def parse(self, expression: str) -> AST:
        # "A and B or C" → AST 변환

    def evaluate(self, expression: str, context: Dict[str, bool]) -> bool:
        # AST 평가 → True/False
```

### 4.2 사용 예시
```python
parser = LogicalExpressionParser()

expression = "(A and B) or (C and not D)"
context = {
    "A": True,   # PER < 15 만족
    "B": False,  # ROE > 10 불만족
    "C": True,   # PBR < 2 만족
    "D": False   # 부채비율 > 50 불만족
}

result = parser.evaluate(expression, context)  # True
```

## 5. Enum 기반 구조화

### 5.1 팩터 정의
```python
class FactorType(str, Enum):
    # Value
    PER = "PER"
    PBR = "PBR"
    PSR = "PSR"
    EV_EBITDA = "EV_EBITDA"

    # Profitability
    ROE = "ROE"
    ROA = "ROA"
    GP_A = "GP_A"

    # Growth
    REVENUE_GROWTH = "REVENUE_GROWTH"
    EARNINGS_GROWTH = "EARNINGS_GROWTH"

    # Momentum
    MOMENTUM_1M = "MOMENTUM_1M"
    MOMENTUM_3M = "MOMENTUM_3M"

    # Quality
    DEBT_RATIO = "DEBT_RATIO"
    CURRENT_RATIO = "CURRENT_RATIO"
```

### 5.2 주문 상태
```python
class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
```

## 6. 주문/체결/포지션 추적

### 6.1 주문 생성
```python
order = {
    "order_id": uuid4(),
    "order_date": datetime.now(),
    "stock_code": "005930",
    "order_type": "MARKET",
    "order_side": "BUY",
    "quantity": 100,
    "status": "PENDING",
    "factor_scores": {"PER": 12.5, "ROE": 15.3},
    "condition_results": {"A": True, "B": True, "C": False}
}
```

### 6.2 체결 기록
```python
execution = {
    "execution_id": uuid4(),
    "order_id": order_id,
    "execution_date": datetime.now(),
    "quantity": 100,
    "price": 65000,
    "commission": 975,
    "tax": 0,
    "slippage_amount": 65
}
```

### 6.3 포지션 추적
```python
position = {
    "position_id": uuid4(),
    "stock_code": "005930",
    "entry_date": date(2023, 1, 2),
    "entry_price": 65000,
    "quantity": 100,
    "current_price": 68000,
    "unrealized_pnl": 300000,
    "max_profit": 500000,
    "max_loss": -100000,
    "factor_scores_entry": {"PER": 12.5, "ROE": 15.3},
    "factor_scores_current": {"PER": 13.2, "ROE": 15.8}
}
```

## 7. 통계 계산 및 저장

### 7.1 월별 통계
```python
monthly_stats = {
    "year": 2023,
    "month": 1,
    "return_rate": 5.23,
    "win_rate": 65.5,        # 실제 거래 기반
    "trade_count": 25,
    "avg_hold_days": 15,
    "best_trade": {...},
    "worst_trade": {...},
    "max_drawdown": 3.2,
    "sharpe_ratio": 1.8
}
```

### 7.2 드로다운 분석
```python
drawdown_period = {
    "start_date": date(2023, 2, 15),
    "end_date": date(2023, 3, 10),
    "peak_value": 105000000,
    "trough_value": 97000000,
    "max_drawdown": 7.62,
    "duration_days": 23,
    "recovery_days": 15
}
```

### 7.3 팩터 기여도
```python
factor_contribution = {
    "factor_name": "PER",
    "total_trades": 150,
    "winning_trades": 98,
    "win_rate": 65.33,
    "avg_profit": 250000,
    "contribution_score": 45.2,
    "correlation_with_return": 0.72,
    "importance_rank": 1
}
```

## 8. API 엔드포인트 구조

### 8.1 백테스트 생성 (v2)
```
POST /api/v2/backtest
{
    "settings": {
        "backtest_name": "PER+ROE 전략",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "universe": {
            "type": "KOSPI",
            "market_cap_min": 1000000000000,
            "exclude_stocks": ["155660"]
        },
        "buy_expression": {
            "expression": "(A and B) or C",
            "conditions": [...]
        },
        "sell_conditions": [...],
        "rebalance_frequency": "MONTHLY"
    }
}
```

### 8.2 백테스트 조회 (v2)
```
GET /api/v2/backtest/{backtest_id}

Response:
{
    "backtest_id": "...",
    "status": "COMPLETED",
    "statistics": {...},
    "monthly_statistics": [...],
    "yearly_statistics": [...],
    "drawdown_statistics": {...},
    "factor_contributions": [...],
    "orders": [...],
    "executions": [...],
    "positions": [...],
    "chart_data": {...}
}
```

## 9. 구현 우선순위

### Phase 1: 핵심 기능 (필수)
1. ✅ 논리식 파서 구현
2. ✅ 새로운 DB 스키마 생성
3. ⬜ 주문/체결/포지션 로직
4. ⬜ 일별 통계 계산

### Phase 2: 통계 및 분석 (중요)
5. ⬜ 월별/연도별 통계
6. ⬜ 드로다운 분석
7. ⬜ 팩터 기여도 분석

### Phase 3: 최적화 (선택)
8. ⬜ Polars 전환
9. ⬜ 비동기 처리 최적화
10. ⬜ 캐싱 전략

## 10. 성능 최적화 전략

### 10.1 데이터 로딩
```python
# Chunked loading
chunk_size = 10000
for chunk in pd.read_sql(query, con, chunksize=chunk_size):
    process(chunk)
```

### 10.2 팩터 계산
```python
# Vectorized operations
df['PER'] = df['price'] / df['eps']  # Good
# Loop operations
for i in range(len(df)):  # Bad
    df.loc[i, 'PER'] = df.loc[i, 'price'] / df.loc[i, 'eps']
```

### 10.3 병렬 처리
```python
import asyncio
tasks = [
    calculate_value_factors(),
    calculate_momentum_factors(),
    calculate_quality_factors()
]
results = await asyncio.gather(*tasks)
```

## 11. 테스트 전략

### 11.1 단위 테스트
- 논리식 파서
- 팩터 계산
- 주문 체결 로직

### 11.2 통합 테스트
- 전체 백테스트 실행
- 결과 검증
- 성능 측정

### 11.3 검증 포인트
- 수익률 계산 정확성
- 거래 비용 적용
- 리밸런싱 타이밍
- 드로다운 계산

## 12. 예상 결과

### 12.1 개선 효과
- **정확성**: 논리식으로 복잡한 전략 표현
- **추적성**: 모든 주문/체결 기록
- **분석력**: 상세한 통계 및 기여도 분석
- **성능**: Polars 사용으로 3-5배 향상

### 12.2 제한사항
- 메모리 사용량 증가 (더 많은 데이터 저장)
- 초기 구현 복잡도 높음
- 기존 시스템과의 호환성 고려 필요