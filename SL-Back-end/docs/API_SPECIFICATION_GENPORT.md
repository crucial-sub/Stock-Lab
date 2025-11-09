# GenPort 스타일 백테스트 API 명세서

## 개요

GenPort UI 스크린샷 기반으로 재설계된 백테스트 API 명세서입니다.

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js (TypeScript)
- **Base URL**: `http://localhost:8000/api/v1`

---

## 1. 백테스트 실행 API

### Endpoint
```
POST /api/v1/backtest/run
```

### Request Body

```json
{
  "backtest_name": "lucainr_20251105_191632",
  "buy_conditions": [
    {
      "factor": "PER",
      "operator": "<",
      "value": 15,
      "description": "PER 15 이하"
    },
    {
      "factor": "ROE",
      "operator": ">",
      "value": 10,
      "description": "ROE 10% 이상"
    }
  ],
  "sell_conditions": [
    {
      "factor": "PER",
      "operator": ">",
      "value": 30,
      "description": "PER 30 초과시 매도"
    }
  ],
  "start_date": "2024-11-01",
  "end_date": "2025-11-04",
  "initial_capital": 50000000,
  "rebalance_frequency": "MONTHLY",
  "max_positions": 20,
  "position_sizing": "EQUAL_WEIGHT",
  "benchmark": "KOSPI",
  "settings": {
    "commission_rate": 0.015,
    "tax_rate": 0.23,
    "slippage": 0.1,
    "stop_loss": null,
    "take_profit": null
  }
}
```

### Response

```json
{
  "backtest_id": "B5120599",
  "status": "pending",
  "message": "백테스트가 시작되었습니다",
  "created_at": "2025-11-05T19:16:32.000Z"
}
```

---

## 2. 백테스트 결과 조회 API (GenPort 스타일)

### Endpoint
```
GET /api/v1/backtest/{backtest_id}/result
```

### Response

```json
{
  "backtest_id": "B5120599",
  "backtest_name": "lucainr_20251105_191632",
  "status": "COMPLETED",
  "created_at": "2025-11-05T19:16:32.000Z",
  "completed_at": "2025-11-05T19:17:45.000Z",

  "settings": {
    "rebalance_frequency": "MONTHLY",
    "max_positions": 20,
    "position_sizing": "EQUAL_WEIGHT",
    "benchmark": "KOSPI",
    "commission_rate": 0.015,
    "tax_rate": 0.23,
    "slippage": 0.1
  },

  "buy_conditions": [
    {
      "factor": "PER",
      "operator": "<",
      "value": 15,
      "description": "PER 15 이하"
    }
  ],

  "sell_conditions": [
    {
      "factor": "PER",
      "operator": ">",
      "value": 30,
      "description": "PER 30 초과시 매도"
    }
  ],

  "statistics": {
    "total_return": 0.08,
    "annualized_return": 20.94,
    "benchmark_return": -10.12,
    "excess_return": 31.06,
    "max_drawdown": 15.43,
    "volatility": 21.76,
    "downside_volatility": 15.23,
    "sharpe_ratio": 1.17,
    "sortino_ratio": 1.53,
    "calmar_ratio": 0.87,
    "total_trades": 244,
    "winning_trades": 152,
    "losing_trades": 92,
    "win_rate": 62.3,
    "avg_win": 11.16,
    "avg_loss": -7.13,
    "profit_loss_ratio": 1.8,
    "initial_capital": 50000000,
    "final_capital": 60563511,
    "peak_capital": 64312223,
    "start_date": "2024-11-01",
    "end_date": "2025-11-04",
    "trading_days": 244
  },

  "current_holdings": [
    {
      "stock_code": "A264450",
      "stock_name": "유비쿼스",
      "quantity": 1000,
      "avg_price": 6282.458,
      "current_price": 6282.458,
      "value": 6282458,
      "profit": 0,
      "profit_rate": 0,
      "weight": 10.37,
      "buy_date": "2025-01-06",
      "hold_days": 43,
      "factors": {
        "PER": 9.94,
        "PBR": 0.91,
        "ROE": 9.54
      }
    }
  ],

  "daily_performance": [
    {
      "date": "2024-11-01",
      "portfolio_value": 50000000,
      "cash_balance": 50000000,
      "invested_amount": 0,
      "daily_return": 0,
      "cumulative_return": 0,
      "drawdown": 0,
      "benchmark_return": 0,
      "trade_count": 0
    },
    {
      "date": "2024-11-04",
      "portfolio_value": 50174511,
      "cash_balance": 5174511,
      "invested_amount": 45000000,
      "daily_return": 0.11,
      "cumulative_return": 0.35,
      "drawdown": -0.79,
      "benchmark_return": -0.36,
      "trade_count": 9
    }
  ],

  "monthly_performance": [
    {
      "year": 2024,
      "month": 11,
      "return_rate": 0.35,
      "benchmark_return": -0.79,
      "win_rate": 60.0,
      "trade_count": 9,
      "avg_hold_days": 30
    },
    {
      "year": 2025,
      "month": 1,
      "return_rate": 11.63,
      "benchmark_return": 0.62,
      "win_rate": 62.5,
      "trade_count": 14,
      "avg_hold_days": 31
    }
  ],

  "yearly_performance": [
    {
      "year": 2024,
      "return_rate": 0.35,
      "benchmark_return": -0.79,
      "max_drawdown": 3.91,
      "sharpe_ratio": 0.92,
      "trades": 9
    },
    {
      "year": 2025,
      "return_rate": -0.27,
      "benchmark_return": -9.33,
      "max_drawdown": 15.43,
      "sharpe_ratio": 0.88,
      "trades": 235
    }
  ],

  "trades": [
    {
      "trade_id": "T001",
      "trade_date": "2024-11-04",
      "trade_type": "BUY",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 100,
      "price": 70000,
      "amount": 7000000,
      "commission": 1050,
      "tax": 0,
      "factors": {
        "PER": 12.1,
        "PBR": 1.2,
        "ROE": 15.3
      },
      "selection_reason": "PER < 15 and ROE > 10"
    },
    {
      "trade_id": "T002",
      "trade_date": "2024-12-01",
      "trade_type": "SELL",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 100,
      "price": 75000,
      "amount": 7500000,
      "commission": 1125,
      "tax": 17250,
      "profit": 481625,
      "profit_rate": 6.88,
      "hold_days": 27
    }
  ],

  "rebalance_dates": [
    "2024-11-01",
    "2024-12-02",
    "2025-01-02",
    "2025-02-03",
    "2025-03-03",
    "2025-04-01",
    "2025-05-02",
    "2025-06-02",
    "2025-07-01",
    "2025-08-01",
    "2025-09-01",
    "2025-10-01",
    "2025-11-03"
  ],

  "chart_data": {
    "cumulative_returns": {
      "dates": ["2024-11-01", "2024-11-02", "..."],
      "portfolio": [0, 0.11, 0.35, "..."],
      "benchmark": [0, -0.12, -0.36, "..."]
    },
    "drawdown": {
      "dates": ["2024-11-01", "2024-11-02", "..."],
      "values": [0, -0.5, -1.2, "..."]
    },
    "monthly_returns": {
      "months": ["2024-11", "2024-12", "2025-01", "..."],
      "portfolio": [0.35, 7.2, 11.63, "..."],
      "kospi": [-0.79, 1.2, 0.62, "..."],
      "kosdaq": [-1.17, 2.3, 1.05, "..."]
    },
    "holdings_distribution": {
      "labels": ["유비쿼스", "에스텍디텍", "아이디스올", "..."],
      "values": [10.37, 8.45, 7.23, "..."]
    },
    "sector_distribution": {
      "labels": ["IT", "바이오", "제조", "기타"],
      "values": [35.2, 28.1, 22.3, 14.4]
    }
  }
}
```

---

## 3. 백테스트 목록 조회 API

### Endpoint
```
GET /api/v1/backtest/list
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `page` | number | ❌ | 1 | 페이지 번호 |
| `page_size` | number | ❌ | 20 | 페이지 크기 |
| `sort_by` | string | ❌ | "created_at" | 정렬 기준 |
| `sort_order` | string | ❌ | "desc" | 정렬 순서 |

### Response

```json
{
  "items": [
    {
      "backtest_id": "B5120599",
      "backtest_name": "lucainr_20251105_191632",
      "created_at": "2025-11-05T19:16:32.000Z",
      "status": "COMPLETED",
      "total_return": 0.08,
      "max_drawdown": 15.43,
      "sharpe_ratio": 1.17,
      "start_date": "2024-11-01",
      "end_date": "2025-11-04"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

## 4. 포트폴리오 실시간 조회 API

### Endpoint
```
GET /api/v1/backtest/{backtest_id}/portfolio
```

### Response

```json
{
  "backtest_id": "B5120599",
  "current_date": "2025-11-04",
  "portfolio_value": 60563511,
  "cash_balance": 10563511,
  "invested_amount": 50000000,
  "daily_return": 0.11,
  "cumulative_return": 21.13,
  "holdings": [
    {
      "stock_code": "A264450",
      "stock_name": "유비쿼스",
      "quantity": 1000,
      "avg_price": 6282.458,
      "current_price": 6282.458,
      "value": 6282458,
      "profit": 0,
      "profit_rate": 0,
      "weight": 10.37
    }
  ]
}
```

---

## 5. 팩터 데이터 조회 API

### Endpoint
```
GET /api/v1/factors/{stock_code}
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `date` | string | ❌ | today | 조회 날짜 |
| `factors` | string | ❌ | "all" | 팩터 리스트 (comma separated) |

### Response

```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "date": "2025-11-04",
  "factors": {
    "PER": 12.1,
    "PBR": 1.2,
    "EV_EBITDA": 8.5,
    "DIV_YIELD": 2.3,
    "ROE": 15.3,
    "ROA": 8.7,
    "GP_A": 35.2,
    "REVENUE_GROWTH": 5.2,
    "EARNINGS_GROWTH": 10.3,
    "MOMENTUM_1M": -2.1,
    "MOMENTUM_3M": 5.4,
    "MOMENTUM_6M": 12.3,
    "MOMENTUM_12M": 18.7,
    "DEBT_RATIO": 45.2,
    "CURRENT_RATIO": 1.8,
    "VOLATILITY": 22.3
  },
  "ranks": {
    "PER": 45,
    "PBR": 32,
    "ROE": 12
  },
  "percentiles": {
    "PER": 75.2,
    "PBR": 60.1,
    "ROE": 85.3
  }
}
```

---

## 6. 팩터 업데이트 API (배치)

### Endpoint
```
POST /api/v1/factors/update
```

### Request Body

```json
{
  "date": "2025-11-04",
  "factors": ["PER", "PBR", "ROE", "MOMENTUM_1M"]
}
```

### Response

```json
{
  "status": "success",
  "date": "2025-11-04",
  "stocks_updated": 2345,
  "factors_calculated": 4,
  "execution_time": 12.5
}
```

---

## WebSocket API (실시간 백테스트 진행 상황)

### Endpoint
```
ws://localhost:8000/ws/backtest/{backtest_id}
```

### Message Format

#### Client → Server
```json
{
  "type": "subscribe",
  "backtest_id": "B5120599"
}
```

#### Server → Client (Progress Update)
```json
{
  "type": "progress",
  "backtest_id": "B5120599",
  "status": "RUNNING",
  "progress": 45,
  "current_date": "2025-03-15",
  "message": "2025년 3월 리밸런싱 진행 중..."
}
```

#### Server → Client (Trade Event)
```json
{
  "type": "trade",
  "backtest_id": "B5120599",
  "trade": {
    "date": "2025-03-15",
    "type": "BUY",
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "quantity": 100,
    "price": 70000
  }
}
```

#### Server → Client (Completion)
```json
{
  "type": "completed",
  "backtest_id": "B5120599",
  "statistics": {
    "total_return": 21.13,
    "max_drawdown": 15.43
  }
}
```

---

## 에러 응답 형식

### 4xx/5xx 에러

```json
{
  "error": {
    "code": "INVALID_FACTOR",
    "message": "지원하지 않는 팩터입니다: UNKNOWN_FACTOR",
    "details": {
      "supported_factors": ["PER", "PBR", "ROE", "..."],
      "invalid_factor": "UNKNOWN_FACTOR"
    }
  },
  "timestamp": "2025-11-04T12:00:00.000Z",
  "path": "/api/v1/backtest/run"
}
```

---

## 데이터 타입 정의

### Factor (팩터)
```typescript
type Factor =
  | "PER" | "PBR" | "EV_EBITDA" | "DIV_YIELD"  // Value
  | "ROE" | "ROA" | "GP_A"                      // Profitability
  | "REVENUE_GROWTH" | "EARNINGS_GROWTH"        // Growth
  | "MOMENTUM_1M" | "MOMENTUM_3M" | "MOMENTUM_6M" | "MOMENTUM_12M"  // Momentum
  | "DEBT_RATIO" | "CURRENT_RATIO"              // Stability
  | "VOLATILITY";                                // Risk
```

### Operator (연산자)
```typescript
type Operator = "<" | ">" | "<=" | ">=" | "=" | "!=";
```

### RebalanceFrequency (리밸런싱 주기)
```typescript
type RebalanceFrequency = "DAILY" | "WEEKLY" | "MONTHLY" | "QUARTERLY";
```

### PositionSizing (포지션 사이징)
```typescript
type PositionSizing = "EQUAL_WEIGHT" | "MARKET_CAP" | "RISK_PARITY";
```

### BacktestStatus (백테스트 상태)
```typescript
type BacktestStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
```

### TradeType (거래 유형)
```typescript
type TradeType = "BUY" | "SELL";
```

---

## 주의사항

1. **날짜 형식**: ISO 8601 (`YYYY-MM-DD`)
2. **숫자 정밀도**: Decimal 타입 사용 (소수점 6자리)
3. **백테스트 ID**: `B` prefix + 7자리 숫자
4. **페이지네이션**: 최대 page_size는 100
5. **WebSocket**: 자동 재연결 구현 필요
6. **캐싱**: 팩터 데이터는 일별로 캐싱됨

---

## 버전 정보

- API Version: v1
- Last Updated: 2025-11-09
- Backend: FastAPI 0.109.0
- Frontend: Next.js 16.0.1