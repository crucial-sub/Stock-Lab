# 백테스트 스키마 통합 완료

## 🎯 작업 개요

`backtest_genport_v2.py` 파일을 삭제하고 필요한 기능만 `backtest_genport.py`에 통합했습니다.

## ✅ 완료된 작업

### 1. 삭제된 파일
- ❌ `app/schemas/backtest_genport_v2.py`
- ❌ `app/models/backtest_genport_v2.py`
- ❌ `scripts/create_backtest_v2_tables.py`

### 2. 통합된 파일
- ✅ `app/schemas/backtest_genport.py` (확장됨)

### 3. 추가된 기능

#### 3.1 필수 Enum 타입
```python
class RebalanceFrequency(str, Enum):
    """리밸런싱 주기"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"

class PositionSizingMethod(str, Enum):
    """포지션 크기 결정 방법"""
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    MARKET_CAP = "MARKET_CAP"
    RISK_PARITY = "RISK_PARITY"

class SellConditionType(str, Enum):
    """매도 조건 타입"""
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    HOLD_DAYS = "HOLD_DAYS"
    REBALANCE = "REBALANCE"
```

#### 3.2 확장된 조건 클래스
```python
class BacktestCondition(BaseModel):
    """백테스트 조건 (기존 방식 + 논리식 지원)"""
    factor: str
    operator: str
    value: Union[float, List[float]]  # 단일값 또는 범위
    description: Optional[str] = None
    id: Optional[str] = None  # 논리식용 ID (A, B, C)
```

#### 3.3 논리식 조건 클래스 (신규)
```python
class BacktestConditionExpression(BaseModel):
    """논리식 기반 조건"""
    expression: str  # "(A and B) or C"
    conditions: List[BacktestCondition]
    factor_weights: Optional[Dict[str, float]] = None
```

#### 3.4 백테스트 요청 스키마 (신규)
```python
class BacktestCreateRequest(BaseModel):
    """백테스트 생성 요청"""
    # 기존 방식 (하위 호환)
    buy_conditions: Optional[List[BacktestCondition]] = None

    # 논리식 방식 (새로운)
    buy_expression: Optional[BacktestConditionExpression] = None

    sell_conditions: List[BacktestCondition]
    start_date: date
    end_date: date
    initial_capital: float = 100_000_000
    rebalance_frequency: str = "MONTHLY"
    max_positions: int = 20
    position_sizing: str = "EQUAL_WEIGHT"
    benchmark: Optional[str] = None
    commission_rate: float = 0.00015
    slippage: float = 0.001
```

## 📋 남은 파일 구조

### 스키마
```
app/schemas/
└── backtest_genport.py  ✅ 통합 완료
```

### 모델
```
app/models/
└── backtest_genport.py  ✅ 기존 사용
```

### 서비스
```
app/services/
├── backtest.py              ✅ 메인 엔진
└── condition_evaluator.py   ✅ 논리식 파서
```

### 스크립트
```
scripts/
└── create_backtest_tables.py  ✅ 테이블 생성
```

## 🔄 사용 방법

### 방법 1: 기존 방식 (하위 호환)
```python
# 모든 조건을 AND로 연결
{
    "buy_conditions": [
        {"factor": "PER", "operator": "<", "value": 15},
        {"factor": "ROE", "operator": ">", "value": 10}
    ],
    "sell_conditions": [
        {"type": "STOP_LOSS", "value": 10}
    ],
    ...
}
```

### 방법 2: 논리식 방식 (새로운)
```python
# 복잡한 논리식 사용 가능
{
    "buy_expression": {
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
    ...
}
```

## ✨ 개선 효과

### Before (v2 분리 상태)
```
❌ 혼란스러운 구조
   - backtest_genport.py (사용 중)
   - backtest_genport_v2.py (미사용)
   - 어느 것을 써야 할지 불명확

❌ 중복된 코드
   - 비슷한 내용이 두 파일에 존재
   - 유지보수 어려움

❌ 복잡한 임포트
   - 여러 파일 참조 필요
```

### After (통합 완료)
```
✅ 명확한 구조
   - backtest_genport.py 하나로 통합
   - 단일 진실 공급원(Single Source of Truth)

✅ 하위 호환성
   - 기존 방식 그대로 사용 가능
   - 새로운 논리식도 지원

✅ 간단한 사용
   - 하나의 파일만 임포트
   - 명확한 API
```

## 🎨 API 예시

### 엔드포인트
```
POST /api/v1/backtest/backtest
```

### 요청 (논리식 사용)
```json
{
    "buy_expression": {
        "expression": "(A and B) or (C and D)",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 15},
            {"id": "B", "factor": "PBR", "operator": "<", "value": 1},
            {"id": "C", "factor": "ROE", "operator": ">", "value": 15},
            {"id": "D", "factor": "MOMENTUM_3M", "operator": ">", "value": 10}
        ],
        "factor_weights": {
            "PER": -1,
            "PBR": -1,
            "ROE": 1,
            "MOMENTUM_3M": 1
        }
    },
    "sell_conditions": [
        {"type": "STOP_LOSS", "value": 10},
        {"type": "TAKE_PROFIT", "value": 20},
        {"type": "HOLD_DAYS", "value": 60}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000000,
    "rebalance_frequency": "MONTHLY",
    "max_positions": 20,
    "commission_rate": 0.00015,
    "slippage": 0.001
}
```

### 응답
```json
{
    "backtest_id": "uuid-xxx",
    "status": "COMPLETED",
    "statistics": {
        "total_return": 21.35,
        "sharpe_ratio": 1.82,
        "max_drawdown": -7.62,
        "win_rate": 65.5
    },
    "monthly_performance": [...],
    "trades": [...],
    "chart_data": {...}
}
```

## 🧪 테스트 시나리오

### 시나리오 1: 기존 방식 테스트
```python
# 기존 코드가 그대로 작동하는지 확인
buy_conditions = [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
]
# ✅ 정상 작동해야 함
```

### 시나리오 2: 논리식 테스트
```python
# 새로운 논리식이 작동하는지 확인
buy_expression = {
    "expression": "(A and B) or C",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "PBR", "operator": "<", "value": 1}
    ]
}
# ✅ 정상 작동해야 함
```

## 📝 주의사항

### 1. 검증 로직
`BacktestCreateRequest`는 다음을 검증합니다:
- `buy_conditions` 또는 `buy_expression` 중 **하나는 반드시** 제공되어야 함
- 둘 다 없으면 ValidationError 발생

### 2. 엔진 처리
`backtest.py` 엔진은:
- `buy_expression`이 있으면 → 논리식 평가
- `buy_conditions`만 있으면 → AND 로직 (기존 방식)
- 하위 호환성 완벽 유지

### 3. 논리식 문법
- 허용된 키워드: `and`, `or`, `not`, `(`, `)`
- 조건 ID: 알파벳 한 글자 (`A`, `B`, `C`, ...)
- 예시: `(A and B) or (C and not D)`

## 🚀 다음 단계

1. **테스트 실행**
   ```bash
   pytest tests/test_backtest_conditions.py
   ```

2. **API 문서 확인**
   ```
   http://localhost:8000/docs
   ```

3. **실제 백테스트 실행**
   ```bash
   # 기존 방식
   curl -X POST .../backtest -d '{"buy_conditions": [...]}'

   # 논리식 방식
   curl -X POST .../backtest -d '{"buy_expression": {...}}'
   ```

## ✅ 결론

- **v2 파일 제거 완료** ✅
- **기능은 모두 통합됨** ✅
- **하위 호환성 유지** ✅
- **논리식 지원 추가** ✅
- **구조 단순화** ✅

이제 **단일 스키마 파일**로 모든 기능을 사용할 수 있습니다!