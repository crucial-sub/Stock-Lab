# camelCase Conversion Fix

## 문제 상황

프론트엔드에서 백테스트 결과 페이지 접속 시 다음 오류 발생:

```
TypeError: Cannot read properties of undefined (reading 'toFixed')
at QuantResultPageClient.tsx:88
```

**에러 원인**: 백엔드 API가 snake_case 필드명(`total_return`, `annualized_return`)으로 응답하지만, 프론트엔드는 camelCase 필드명(`totalReturn`, `annualizedReturn`)을 기대함.

## 해결 방법

Pydantic V2의 `serialization_alias` 기능을 사용하여 백엔드 응답을 camelCase로 자동 변환.

### 수정 파일

**`app/api/routes/backtest.py`**

### 변경 내역

#### 1. BacktestResultStatistics 모델

```python
class BacktestResultStatistics(BaseModel):
    """백테스트 결과 통계"""
    model_config = ConfigDict(populate_by_name=True)

    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: float = Field(..., serialization_alias="maxDrawdown")
    volatility: float
    sharpe_ratio: float = Field(..., serialization_alias="sharpeRatio")
    win_rate: float = Field(..., serialization_alias="winRate")
    profit_factor: float = Field(..., serialization_alias="profitFactor")
    total_trades: int = Field(..., serialization_alias="totalTrades")
    winning_trades: int = Field(..., serialization_alias="winningTrades")
    losing_trades: int = Field(..., serialization_alias="losingTrades")
    final_capital: float = Field(..., serialization_alias="finalCapital")
```

**변경 사항**:
- `model_config = ConfigDict(populate_by_name=True)` 추가
- 모든 snake_case 필드에 `serialization_alias` 추가하여 camelCase로 변환
- `volatility`는 이미 camelCase이므로 alias 불필요

#### 2. BacktestTrade 모델

```python
class BacktestTrade(BaseModel):
    """백테스트 거래 내역"""
    model_config = ConfigDict(populate_by_name=True)

    stock_name: str = Field(..., serialization_alias="stockName")
    stock_code: str = Field(..., serialization_alias="stockCode")
    buy_price: float = Field(..., serialization_alias="buyPrice")
    sell_price: float = Field(..., serialization_alias="sellPrice")
    profit: float
    profit_rate: float = Field(..., serialization_alias="profitRate")
    buy_date: str = Field(..., serialization_alias="buyDate")
    sell_date: str = Field(..., serialization_alias="sellDate")
    weight: float
    valuation: float
```

**변경 사항**:
- 매매 내역의 모든 snake_case 필드에 serialization_alias 추가
- `profit`, `weight`, `valuation`은 이미 camelCase이므로 alias 불필요

#### 3. BacktestResultResponse 모델

```python
class BacktestResultResponse(BaseModel):
    """백테스트 결과 응답"""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    status: str
    statistics: BacktestResultStatistics
    trades: List[BacktestTrade]
    yield_points: List[BacktestYieldPoint] = Field(..., serialization_alias="yieldPoints")
    created_at: datetime = Field(..., serialization_alias="createdAt")
    completed_at: Optional[datetime] = Field(None, serialization_alias="completedAt")
```

**변경 사항**:
- 날짜/시간 필드에 serialization_alias 추가
- 중첩된 `statistics`, `trades` 객체는 자동으로 변환됨

## 검증

### API 응답 예시 (변경 후)

```bash
curl http://localhost:8000/api/v1/backtest/{backtestId}/result
```

**응답**:
```json
{
  "id": "9de31c26-4dc4-4f5f-bdf0-3deb80f9df58",
  "status": "completed",
  "statistics": {
    "totalReturn": 15.0,           // ✓ camelCase
    "annualizedReturn": 30.0,       // ✓ camelCase
    "maxDrawdown": 5.0,             // ✓ camelCase
    "volatility": 12.0,
    "sharpeRatio": 1.25,            // ✓ camelCase
    "winRate": 60.0,                // ✓ camelCase
    "profitFactor": 0.0,            // ✓ camelCase
    "totalTrades": 10,              // ✓ camelCase
    "winningTrades": 6,             // ✓ camelCase
    "losingTrades": 4,              // ✓ camelCase
    "finalCapital": 115000000.0     // ✓ camelCase
  },
  "trades": [],
  "yieldPoints": [                  // ✓ camelCase
    {
      "date": "2025-01-01",
      "value": 0.0
    }
  ],
  "createdAt": "2025-11-04T06:33:29", // ✓ camelCase
  "completedAt": null
}
```

### 프론트엔드 검증

**`QuantResultPageClient.tsx`** 에서 사용하는 필드들이 이제 정상적으로 작동:

```typescript
// Line 88 - 더 이상 undefined 에러 발생하지 않음
value: `${backtestResult.statistics.totalReturn.toFixed(2)}%`

// Line 94
value: `${backtestResult.statistics.annualizedReturn.toFixed(2)}%`

// Line 100
value: backtestResult.statistics.sharpeRatio.toFixed(2)

// Line 106
value: `${backtestResult.statistics.maxDrawdown.toFixed(2)}%`
```

## Pydantic 설정 설명

### ConfigDict(populate_by_name=True)

이 설정은 Pydantic V2에서 필드명과 alias를 모두 허용하도록 합니다:
- **입력 시**: snake_case와 camelCase 모두 허용 (하위 호환성)
- **출력 시**: serialization_alias가 우선 사용됨

### serialization_alias vs validation_alias

- **`serialization_alias`**: JSON 응답 시 사용되는 필드명 (백엔드 → 프론트엔드)
- **`validation_alias`**: JSON 요청 시 허용되는 필드명 (프론트엔드 → 백엔드)

이 경우 응답 형식만 변경하므로 `serialization_alias`만 사용.

## 영향 범위

### 변경된 API 엔드포인트

- `GET /api/v1/backtest/{backtestId}/result`
- `GET /api/v1/backtest/{backtestId}/trades` (응답이 BacktestTrade 사용하는 경우)

### 영향 받는 프론트엔드 컴포넌트

- `QuantResultPageClient.tsx` - 백테스트 결과 페이지
- `useBacktestQuery.ts` - 백테스트 결과 조회 훅

### 하위 호환성

`populate_by_name=True` 설정으로 인해 기존 snake_case 요청도 여전히 허용됨. 따라서 프론트엔드 배포 전에도 백엔드를 먼저 배포할 수 있음.

## 관련 문서

- [Pydantic V2 Serialization Aliases](https://docs.pydantic.dev/latest/concepts/alias/)
- [API_SPECIFICATION.md](./API_SPECIFICATION.md) - 프론트엔드-백엔드 필드 매핑 문서

## 배포 순서

1. ✅ 백엔드 배포 (SL-Back-Test)
   - Pydantic 모델에 serialization_alias 추가
   - 서버 재시작 (uvicorn --reload로 자동 적용됨)

2. ✅ 프론트엔드 자동 적용 (SL-Front-End)
   - 타입 정의는 이미 camelCase로 되어있음
   - 백엔드가 camelCase로 응답하면 자동으로 작동

3. ✅ 검증
   - 백테스트 실행 후 결과 페이지 접속
   - "Cannot read properties of undefined" 에러 사라짐
   - 모든 통계 지표가 정상 표시됨

## 향후 개선 사항

### 1. 자동 camelCase 변환 미들웨어

모든 Pydantic 모델에 수동으로 alias를 추가하는 대신, 전역 미들웨어로 처리:

```python
# app/core/config.py
from pydantic import ConfigDict

# 전역 설정
DEFAULT_MODEL_CONFIG = ConfigDict(
    alias_generator=to_camel,  # 자동 camelCase 변환
    populate_by_name=True
)
```

### 2. 타입 생성 자동화

백엔드 Pydantic 모델에서 프론트엔드 TypeScript 타입 자동 생성:

```bash
pydantic-to-typescript --output src/types/generated.ts
```

### 3. API 계약 테스트

OpenAPI 스펙 기반으로 프론트엔드-백엔드 계약 테스트 추가.

---

**수정일**: 2025-11-04
**수정자**: Claude Code
**이슈**: TypeError: Cannot read properties of undefined (reading 'toFixed')
**해결**: Pydantic serialization_alias로 snake_case → camelCase 자동 변환
