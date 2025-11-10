# 🔗 프론트엔드 연동 가이드

## 1. 백테스트 실행 API

### 📍 엔드포인트
```
POST /api/v1/backtest/backtest
```

### 📥 요청 (Request)
```json
{
    "buy_expression": {
        "expression": "(A and B) or C",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 15},
            {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
            {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
        ],
        "factor_weights": {
            "PER": -1,
            "ROE": 1,
            "MOMENTUM_3M": 1
        }
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
    "position_sizing": "EQUAL_WEIGHT",
    "commission_rate": 0.00015,
    "slippage": 0.001
}
```

### 📤 응답 (Response)
```json
{
    "backtest_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "COMPLETED",
    "created_at": "2024-11-10T10:00:00",
    "completed_at": "2024-11-10T10:05:23",

    "statistics": {
        "total_return": 23.45,
        "annualized_return": 23.45,
        "max_drawdown": -8.32,
        "sharpe_ratio": 1.82,
        "sortino_ratio": 2.14,
        "calmar_ratio": 2.82,
        "volatility": 12.5,
        "win_rate": 65.2,
        "total_trades": 142,
        "winning_trades": 93,
        "losing_trades": 49,
        "avg_win": 3.2,
        "avg_loss": -1.8,
        "profit_loss_ratio": 1.78
    },

    "chart_data": {
        "portfolio_values": [
            {"date": "2023-01-01", "value": 100000000},
            {"date": "2023-01-02", "value": 100120000},
            // ... 매일 데이터
        ],
        "cumulative_returns": [
            {"date": "2023-01-01", "return": 0},
            {"date": "2023-01-02", "return": 0.12},
            // ...
        ],
        "drawdowns": [
            {"date": "2023-02-15", "drawdown": -3.2},
            // ...
        ]
    },

    "monthly_returns": [
        {"year": 2023, "month": 1, "return": 2.3},
        {"year": 2023, "month": 2, "return": -1.2},
        // ... 12개월
    ],

    "trades": [
        {
            "date": "2023-01-15",
            "type": "BUY",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "quantity": 100,
            "price": 65000,
            "amount": 6500000
        },
        // ... 모든 거래
    ],

    "final_holdings": [
        {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "quantity": 100,
            "avg_price": 65000,
            "current_price": 71000,
            "profit": 600000,
            "profit_rate": 9.23,
            "weight": 5.2
        },
        // ... 최종 보유 종목
    ]
}
```

## 2. 백테스트 결과 조회 API

### 📍 엔드포인트
```
GET /api/v1/backtest/backtest/{backtest_id}
```

### 📤 응답
위와 동일한 구조

## 3. 백테스트 목록 조회 API

### 📍 엔드포인트
```
GET /api/v1/backtest/backtests?limit=10&offset=0
```

### 📤 응답
```json
{
    "total": 25,
    "backtests": [
        {
            "backtest_id": "550e8400-e29b-41d4-a716-446655440000",
            "backtest_name": "Value + Momentum Strategy",
            "status": "COMPLETED",
            "total_return": 23.45,
            "sharpe_ratio": 1.82,
            "created_at": "2024-11-10T10:00:00"
        },
        // ...
    ]
}
```

## 4. 실시간 백테스트 진행상황 (WebSocket)

### 📍 엔드포인트
```
ws://localhost:8000/api/v1/backtest/ws/{backtest_id}
```

### 📤 메시지 형식
```json
{
    "type": "progress",
    "data": {
        "current_date": "2023-06-15",
        "progress": 50,  // 퍼센트
        "message": "Processing trades for June 2023..."
    }
}
```

## 5. 프론트엔드 구현 필요 사항

### 5.1 백테스트 설정 화면

```tsx
// BacktestConfig.tsx
interface BacktestConfig {
    // 기간 설정
    startDate: string;
    endDate: string;

    // 자본금 설정
    initialCapital: number;

    // 매수 조건 설정
    buyConditions: {
        expression: string;  // "(A and B) or C"
        conditions: Condition[];
    };

    // 매도 조건 설정
    sellConditions: SellCondition[];

    // 리밸런싱 설정
    rebalanceFrequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY';
    maxPositions: number;
    positionSizing: 'EQUAL_WEIGHT' | 'MARKET_CAP' | 'RISK_PARITY';

    // 거래 비용
    commissionRate: number;
    slippage: number;
}
```

### 5.2 결과 화면 컴포넌트

```tsx
// BacktestResult.tsx
const BacktestResult = ({ backtestId }) => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchBacktestResult(backtestId)
            .then(setResult)
            .finally(() => setLoading(false));
    }, [backtestId]);

    if (loading) return <LoadingSpinner />;

    return (
        <div>
            {/* 1. 요약 통계 */}
            <StatisticsSummary stats={result.statistics} />

            {/* 2. 차트 */}
            <PortfolioChart data={result.chart_data} />

            {/* 3. 월별 수익률 히트맵 */}
            <MonthlyReturnsHeatmap data={result.monthly_returns} />

            {/* 4. 거래 내역 테이블 */}
            <TradesTable trades={result.trades} />

            {/* 5. 최종 보유 종목 */}
            <HoldingsTable holdings={result.final_holdings} />
        </div>
    );
};
```

### 5.3 실시간 진행상황 표시

```tsx
// BacktestProgress.tsx
const BacktestProgress = ({ backtestId }) => {
    const [progress, setProgress] = useState(0);
    const [message, setMessage] = useState('');

    useEffect(() => {
        const ws = new WebSocket(`ws://localhost:8000/api/v1/backtest/ws/${backtestId}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
                setProgress(data.data.progress);
                setMessage(data.data.message);
            } else if (data.type === 'complete') {
                // 결과 화면으로 이동
                window.location.href = `/backtest/result/${backtestId}`;
            }
        };

        return () => ws.close();
    }, [backtestId]);

    return (
        <div>
            <ProgressBar percent={progress} />
            <p>{message}</p>
        </div>
    );
};
```

## 6. 라우팅 구조

```tsx
// App.tsx
<Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/backtest" element={<BacktestList />} />
    <Route path="/backtest/new" element={<BacktestConfig />} />
    <Route path="/backtest/running/:id" element={<BacktestProgress />} />
    <Route path="/backtest/result/:id" element={<BacktestResult />} />
</Routes>
```

## 7. API 클라이언트

```typescript
// api/backtest.ts
class BacktestAPI {
    private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    async createBacktest(config: BacktestConfig): Promise<BacktestResponse> {
        const response = await fetch(`${this.baseURL}/api/v1/backtest/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return response.json();
    }

    async getBacktestResult(backtestId: string): Promise<BacktestResult> {
        const response = await fetch(`${this.baseURL}/api/v1/backtest/backtest/${backtestId}`);
        return response.json();
    }

    async listBacktests(limit = 10, offset = 0): Promise<BacktestList> {
        const response = await fetch(
            `${this.baseURL}/api/v1/backtest/backtests?limit=${limit}&offset=${offset}`
        );
        return response.json();
    }
}
```

## 8. 상태 관리 (Redux/Zustand)

```typescript
// store/backtestStore.ts
interface BacktestStore {
    currentBacktest: BacktestResult | null;
    backtestList: BacktestSummary[];
    isRunning: boolean;
    progress: number;

    // Actions
    startBacktest: (config: BacktestConfig) => Promise<void>;
    fetchResult: (id: string) => Promise<void>;
    fetchList: () => Promise<void>;
}
```

## 9. 차트 컴포넌트 (Chart.js / Recharts)

```tsx
// components/PortfolioChart.tsx
import { Line } from 'react-chartjs-2';

const PortfolioChart = ({ data }) => {
    const chartData = {
        labels: data.portfolio_values.map(d => d.date),
        datasets: [{
            label: 'Portfolio Value',
            data: data.portfolio_values.map(d => d.value),
            borderColor: 'rgb(75, 192, 192)',
            fill: false
        }]
    };

    return <Line data={chartData} />;
};
```

## 10. 에러 처리

```typescript
// hooks/useBacktest.ts
const useBacktest = () => {
    const [error, setError] = useState<string | null>(null);

    const runBacktest = async (config: BacktestConfig) => {
        try {
            const result = await api.createBacktest(config);

            // WebSocket으로 진행상황 추적
            if (result.status === 'RUNNING') {
                // Progress 화면으로 이동
                navigate(`/backtest/running/${result.backtest_id}`);
            } else if (result.status === 'COMPLETED') {
                // 결과 화면으로 이동
                navigate(`/backtest/result/${result.backtest_id}`);
            }
        } catch (error) {
            setError(error.message);
            toast.error('백테스트 실행 실패');
        }
    };

    return { runBacktest, error };
};
```

## ✅ 체크리스트

- [ ] 백테스트 설정 UI
- [ ] 조건식 빌더 UI
- [ ] 팩터 선택 UI (54개)
- [ ] 결과 차트 컴포넌트
- [ ] 거래 내역 테이블
- [ ] 통계 대시보드
- [ ] 실시간 진행상황 표시
- [ ] 에러 처리 및 로딩 상태
- [ ] 반응형 디자인
- [ ] 다크모드 지원