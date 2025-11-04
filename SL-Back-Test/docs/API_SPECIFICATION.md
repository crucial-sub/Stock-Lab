# 백테스트 API 명세서

## 개요

SL-Back-Test와 SL-Front-End 간 백테스트 API 통신 규격을 정의합니다.

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Base URL**: `http://localhost:8000/api/v1`

---

## 1. 백테스트 실행 API

### Endpoint
```
POST /api/v1/backtest/run
```

### Request

#### Headers
```
Content-Type: application/json
```

#### Body Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `buy_conditions` | Array | ✅ | - | 매수 조건 배열 |
| `sell_conditions` | Array | ✅ | - | 매도 조건 배열 |
| `start_date` | string | ❌ | "2020-01-01" | 백테스트 시작일 (YYYY-MM-DD) |
| `end_date` | string | ❌ | "2024-12-31" | 백테스트 종료일 (YYYY-MM-DD) |
| `initial_capital` | number | ❌ | 100000000 | 초기 투자 금액 (원) |
| `rebalance_frequency` | string | ❌ | "MONTHLY" | 리밸런싱 주기 |
| `max_positions` | number | ❌ | 20 | 최대 보유 종목 수 (1-100) |
| `position_sizing` | string | ❌ | "EQUAL_WEIGHT" | 포지션 사이징 방법 |
| `benchmark` | string | ❌ | "KOSPI" | 벤치마크 지수 |

#### Condition Object

매수/매도 조건 객체 구조:

| 필드 | 타입 | 필수 | 설명 | 예시 |
|------|------|------|------|------|
| `factor` | string | ✅ | 팩터 ID (대문자) | "PER", "ROE", "PBR" |
| `operator` | string | ✅ | 비교 연산자 | "<", ">", "<=", ">=", "=", "!=" |
| `value` | number | ✅ | 비교 값 | 15, 10.5 |

#### Rebalance Frequency 옵션
- `"DAILY"` - 일별
- `"WEEKLY"` - 주별
- `"MONTHLY"` - 월별 (기본값)
- `"QUARTERLY"` - 분기별

#### Position Sizing 옵션
- `"EQUAL_WEIGHT"` - 균등 비중 (기본값)
- `"MARKET_CAP"` - 시가총액 비중
- `"RISK_PARITY"` - 리스크 패리티

#### 지원되는 팩터 목록

**가치 (Value)**
- `PER` - 주가수익비율
- `PBR` - 주가순자산비율
- `EV_EBITDA` - EV/EBITDA
- `DIV_YIELD` - 배당수익률

**수익성 (Profitability)**
- `ROE` - 자기자본이익률
- `ROA` - 총자산이익률
- `GP_A` - 매출총이익률

**성장성 (Growth)**
- `REVENUE_GROWTH` - 매출성장률
- `EARNINGS_GROWTH` - 이익성장률

**모멘텀 (Momentum)**
- `MOMENTUM_1M` - 1개월 모멘텀
- `MOMENTUM_3M` - 3개월 모멘텀
- `MOMENTUM_6M` - 6개월 모멘텀
- `MOMENTUM_12M` - 12개월 모멘텀

**안정성 (Stability)**
- `DEBT_RATIO` - 부채비율
- `CURRENT_RATIO` - 유동비율

#### Request Example

```json
{
  "buy_conditions": [
    {
      "factor": "PER",
      "operator": "<",
      "value": 15
    },
    {
      "factor": "ROE",
      "operator": ">",
      "value": 10
    }
  ],
  "sell_conditions": [
    {
      "factor": "PER",
      "operator": ">",
      "value": 30
    }
  ],
  "start_date": "2025-01-01",
  "end_date": "2025-06-30",
  "initial_capital": 100000000,
  "rebalance_frequency": "MONTHLY",
  "max_positions": 20,
  "position_sizing": "EQUAL_WEIGHT",
  "benchmark": "KOSPI"
}
```

### Response

#### Success (200 OK)

```json
{
  "backtestId": "9de31c26-4dc4-4f5f-bdf0-3deb80f9df58",
  "status": "pending",
  "message": "백테스트가 시작되었습니다",
  "createdAt": "2025-11-04T06:33:29.866Z"
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `backtestId` | string | 백테스트 고유 ID (UUID) |
| `status` | string | 백테스트 상태 ("pending", "running", "completed", "failed") |
| `message` | string | 응답 메시지 |
| `createdAt` | string | 생성 시각 (ISO 8601) |

#### Error (4xx, 5xx)

```json
{
  "detail": "Error message"
}
```

---

## 2. 백테스트 상태 조회 API

### Endpoint
```
GET /api/v1/backtest/{backtestId}/status
```

### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `backtestId` | string | ✅ | 백테스트 ID |

### Response

#### Success (200 OK)

```json
{
  "backtest_id": "9de31c26-4dc4-4f5f-bdf0-3deb80f9df58",
  "status": "COMPLETED",
  "progress": 100,
  "message": "백테스트가 완료되었습니다",
  "started_at": "2025-11-04T06:33:29.866Z",
  "completed_at": "2025-11-04T06:33:32.945Z",
  "error_message": null
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `backtest_id` | string | 백테스트 ID |
| `status` | string | 상태 ("PENDING", "RUNNING", "COMPLETED", "FAILED") |
| `progress` | number | 진행률 (0-100) |
| `message` | string \| null | 상태 메시지 |
| `started_at` | string \| null | 시작 시각 |
| `completed_at` | string \| null | 완료 시각 |
| `error_message` | string \| null | 에러 메시지 (실패 시) |

---

## 3. 백테스트 결과 조회 API

### Endpoint
```
GET /api/v1/backtest/{backtestId}/result
```

### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `backtestId` | string | ✅ | 백테스트 ID |

### Response

#### Success (200 OK)

```json
{
  "backtest_id": "9de31c26-4dc4-4f5f-bdf0-3deb80f9df58",
  "status": "COMPLETED",
  "statistics": {
    "total_return": 15.0,
    "annualized_return": 30.0,
    "max_drawdown": 5.0,
    "volatility": 12.0,
    "sharpe_ratio": 1.25,
    "win_rate": 60.0,
    "total_trades": 10,
    "winning_trades": 6,
    "losing_trades": 4,
    "final_capital": 115000000.0
  },
  "daily_values": [
    {
      "date": "2025-01-01",
      "portfolio_value": 100000000.0,
      "daily_return": 0.0,
      "cumulative_return": 0.0
    },
    {
      "date": "2025-01-02",
      "portfolio_value": 100500000.0,
      "daily_return": 0.5,
      "cumulative_return": 0.5
    }
  ],
  "trades": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "buy_date": "2025-01-15",
      "sell_date": "2025-02-15",
      "buy_price": 70000,
      "sell_price": 75000,
      "quantity": 100,
      "profit": 500000,
      "return": 7.14
    }
  ]
}
```

#### Statistics Object

| 필드 | 타입 | 설명 |
|------|------|------|
| `total_return` | number | 총 수익률 (%) |
| `annualized_return` | number | 연환산 수익률 (%) |
| `max_drawdown` | number | 최대 낙폭 (%) |
| `volatility` | number | 변동성 (%) |
| `sharpe_ratio` | number | 샤프 비율 |
| `win_rate` | number | 승률 (%) |
| `total_trades` | number | 총 거래 횟수 |
| `winning_trades` | number | 수익 거래 횟수 |
| `losing_trades` | number | 손실 거래 횟수 |
| `final_capital` | number | 최종 자본금 (원) |

---

## Frontend-Backend 데이터 매핑

### Frontend → Backend 변환

프론트엔드에서 백엔드로 요청 시 다음 변환이 필요합니다:

```typescript
// Frontend (camelCase)
const frontendRequest = {
  buyConditions: [...],
  sellConditions: [...],
  period: {
    startDate: "2025-01-01",
    endDate: "2025-06-30"
  }
};

// Backend (snake_case)
const backendRequest = {
  buy_conditions: frontendRequest.buyConditions,
  sell_conditions: frontendRequest.sellConditions,
  start_date: frontendRequest.period.startDate,
  end_date: frontendRequest.period.endDate,
  initial_capital: 100000000,
  rebalance_frequency: "MONTHLY",
  max_positions: 20,
  position_sizing: "EQUAL_WEIGHT",
  benchmark: "KOSPI"
};
```

### Factor ID 변환

프론트엔드는 소문자 factor ID를 사용하지만, 백엔드는 대문자를 사용합니다:

```typescript
// Frontend
const condition = {
  factor: "per",  // 소문자
  operator: "<",
  value: 15
};

// Backend로 전송 시
const backendCondition = {
  factor: "PER",  // 대문자로 변환
  operator: "<",
  value: 15
};
```

---

## 사용 예시

### 1. 백테스트 실행 → 상태 확인 → 결과 조회

```typescript
// 1. 백테스트 실행
const response = await fetch('http://localhost:8000/api/v1/backtest/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    buy_conditions: [
      { factor: "PER", operator: "<", value: 15 },
      { factor: "ROE", operator: ">", value: 10 }
    ],
    sell_conditions: [],
    start_date: "2025-01-01",
    end_date: "2025-06-30",
    initial_capital: 100000000,
    rebalance_frequency: "MONTHLY",
    max_positions: 20,
    position_sizing: "EQUAL_WEIGHT",
    benchmark: "KOSPI"
  })
});

const { backtestId } = await response.json();

// 2. 상태 확인 (폴링)
const checkStatus = async () => {
  const statusResponse = await fetch(
    `http://localhost:8000/api/v1/backtest/${backtestId}/status`
  );
  const status = await statusResponse.json();
  
  if (status.status === 'COMPLETED') {
    return true;
  } else if (status.status === 'FAILED') {
    throw new Error(status.error_message);
  }
  return false;
};

// 3. 결과 조회
while (!(await checkStatus())) {
  await new Promise(resolve => setTimeout(resolve, 1000));
}

const resultResponse = await fetch(
  `http://localhost:8000/api/v1/backtest/${backtestId}/result`
);
const result = await resultResponse.json();
console.log('백테스트 결과:', result);
```

---

## 주의사항

1. **날짜 형식**: 모두 ISO 8601 형식 (`YYYY-MM-DD`) 사용
2. **Factor ID**: 백엔드는 대문자 필수 (PER, ROE 등)
3. **응답 필드명**: 
   - 백테스트 실행 응답: camelCase (`backtestId`, `createdAt`)
   - 기타 응답: snake_case (`backtest_id`, `created_at`)
4. **비동기 처리**: 백테스트는 즉시 완료되지 않으므로 상태 폴링 필요
5. **에러 처리**: 4xx, 5xx 응답 시 `detail` 필드에 에러 메시지 포함

---

## 버전 정보

- API Version: v1
- Last Updated: 2025-11-04
- Backend: FastAPI 0.109.0
- Frontend: Next.js 16.0.1
