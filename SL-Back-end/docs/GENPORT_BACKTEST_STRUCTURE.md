# GenPort 백테스트 결과 구조 문서

## 개요
GenPort 스타일 백테스트 시스템의 완전한 구현이 완료되었습니다.
이 문서는 데이터베이스 스키마, API 엔드포인트, 그리고 프론트엔드로 전달되는 데이터 구조를 설명합니다.

## 1. 데이터베이스 스키마

### 1.1 테이블 구조

#### backtest_sessions (백테스트 메타 정보)
```sql
- backtest_id (UUID, PK): 백테스트 고유 ID
- backtest_name (String): 백테스트 이름
- status (String): 상태 (RUNNING/COMPLETED/FAILED)
- start_date (Date): 백테스트 시작일
- end_date (Date): 백테스트 종료일
- initial_capital (Numeric): 초기 자본금
- rebalance_frequency (String): 리밸런싱 주기
- max_positions (Integer): 최대 보유 종목 수
- position_sizing (String): 포지션 사이징 방법
- benchmark (String): 벤치마크 (KOSPI/KOSDAQ/KOSPI200)
- commission_rate (Numeric): 수수료율 (사용자 설정)
- tax_rate (Numeric): 거래세율 (0.23% 고정)
- slippage (Numeric): 슬리피지 (사용자 설정)
- created_at (DateTime): 생성일시
- completed_at (DateTime): 완료일시
```

#### backtest_conditions (매수/매도 조건)
```sql
- condition_id (Integer, PK): 조건 고유 ID
- backtest_id (UUID, FK): 백테스트 참조
- condition_type (String): BUY/SELL
- factor (String): 팩터 코드 (PER, ROE, etc.) 또는 타입 (STOP_LOSS, etc.)
- operator (String): 연산자 (>, <, >=, <=, =)
- value (Numeric): 기준값
- description (String): 조건 설명
```

#### backtest_statistics (통계 요약)
```sql
- backtest_id (UUID, PK/FK): 백테스트 참조
- total_return (Numeric): 총 수익률 (%)
- annualized_return (Numeric): 연환산 수익률 (CAGR) (%)
- benchmark_return (Numeric): 벤치마크 수익률 (%)
- excess_return (Numeric): 초과 수익률 (%)
- max_drawdown (Numeric): 최대 낙폭 (MDD) (%)
- volatility (Numeric): 변동성 (%)
- downside_volatility (Numeric): 하방 변동성 (%)
- sharpe_ratio (Numeric): 샤프 비율
- sortino_ratio (Numeric): 소르티노 비율
- calmar_ratio (Numeric): 칼마 비율
- total_trades (Integer): 총 거래 횟수
- winning_trades (Integer): 수익 거래 횟수
- losing_trades (Integer): 손실 거래 횟수
- win_rate (Numeric): 승률 (%)
- avg_win (Numeric): 평균 수익 (%)
- avg_loss (Numeric): 평균 손실 (%)
- profit_loss_ratio (Numeric): 손익비
- initial_capital (Numeric): 초기 자본금
- final_capital (Numeric): 최종 자본금
- peak_capital (Numeric): 최대 자본금
- start_date (Date): 시작일
- end_date (Date): 종료일
- trading_days (Integer): 거래일수
```

#### backtest_daily_snapshots (일별 스냅샷)
```sql
- snapshot_id (BigInteger, PK): 스냅샷 고유 ID
- backtest_id (UUID, FK): 백테스트 참조
- snapshot_date (Date): 스냅샷 날짜
- portfolio_value (Numeric): 포트폴리오 가치
- cash_balance (Numeric): 현금 잔고
- invested_amount (Numeric): 투자 금액
- daily_return (Numeric): 일 수익률 (%)
- cumulative_return (Numeric): 누적 수익률 (%)
- drawdown (Numeric): 낙폭 (%)
- benchmark_return (Numeric): 벤치마크 수익률 (%)
- trade_count (Integer): 당일 거래 횟수
```

#### backtest_trades (거래 내역)
```sql
- trade_id (BigInteger, PK): 거래 고유 ID
- backtest_id (UUID, FK): 백테스트 참조
- trade_date (Date): 거래일
- trade_type (String): BUY/SELL
- stock_code (String): 종목 코드
- stock_name (String): 종목명
- quantity (Integer): 수량
- price (Numeric): 거래가
- amount (Numeric): 거래대금
- commission (Numeric): 수수료
- tax (Numeric): 세금
- profit (Numeric): 실현 손익 (매도 시)
- profit_rate (Numeric): 수익률 (%) (매도 시)
- hold_days (Integer): 보유일수 (매도 시)
- factors (JSONB): 거래 시점 팩터 값
- selection_reason (Text): 매매 사유
```

#### backtest_holdings (현재 보유 종목)
```sql
- holding_id (Integer, PK): 보유 종목 고유 ID
- backtest_id (UUID, FK): 백테스트 참조
- stock_code (String): 종목 코드
- stock_name (String): 종목명
- quantity (Integer): 보유 수량
- avg_price (Numeric): 평균 매수가
- current_price (Numeric): 현재가
- value (Numeric): 평가금액
- profit (Numeric): 손익
- profit_rate (Numeric): 수익률 (%)
- weight (Numeric): 포트폴리오 비중 (%)
- buy_date (Date): 최초 매수일
- hold_days (Integer): 보유일수
- factors (JSONB): 현재 팩터 값
```

## 2. API 엔드포인트

### 2.1 팩터 목록 조회
```
GET /api/v1/genport/factors
```
**응답**: 사용 가능한 팩터 목록 (13개 팩터)
- 가치: PER, PBR, DIV_YIELD
- 수익성: ROE, ROA
- 성장성: REVENUE_GROWTH, EARNINGS_GROWTH
- 모멘텀: MOMENTUM_1M, MOMENTUM_3M, MOMENTUM_6M, MOMENTUM_12M
- 변동성: VOLATILITY
- 유동성: AVG_TRADING_VALUE, TURNOVER_RATE

### 2.2 백테스트 실행
```
POST /api/v1/genport/backtest
```
**요청 본문**:
```json
{
  "buy_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
  ],
  "sell_conditions": [
    {"type": "STOP_LOSS", "value": 10},
    {"type": "TAKE_PROFIT", "value": 20}
  ],
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 100000000,
  "rebalance_frequency": "MONTHLY",
  "max_positions": 20,
  "position_sizing": "EQUAL_WEIGHT",
  "benchmark": "KOSPI",
  "commission_rate": 0.00015,
  "slippage": 0.001
}
```

### 2.3 백테스트 목록 조회
```
GET /api/v1/genport/backtest?page=1&page_size=20&status=COMPLETED
```

### 2.4 백테스트 상세 조회
```
GET /api/v1/genport/backtest/{backtest_id}
```

### 2.5 백테스트 삭제
```
DELETE /api/v1/genport/backtest/{backtest_id}
```

### 2.6 기본 설정 조회
```
GET /api/v1/genport/settings/defaults
```

## 3. 프론트엔드 데이터 구조

### 3.1 BacktestResultGenPort (메인 응답 모델)
```typescript
interface BacktestResultGenPort {
  // 기본 정보
  backtest_id: string;
  backtest_name: string;
  status: "RUNNING" | "COMPLETED" | "FAILED";
  created_at: DateTime;
  completed_at?: DateTime;

  // 설정 정보
  settings: {
    rebalance_frequency: string;
    max_positions: number;
    position_sizing: string;
    benchmark: string;
    commission_rate: number;
    tax_rate: number;
    slippage: number;
  };

  // 조건
  buy_conditions: Condition[];
  sell_conditions: Condition[];

  // 통계
  statistics: Statistics;

  // 현재 보유 종목
  current_holdings: PortfolioHolding[];

  // 시계열 데이터
  daily_performance: DailyPerformance[];
  monthly_performance: MonthlyPerformance[];
  yearly_performance: YearlyPerformance[];

  // 거래 내역
  trades: TradeRecord[];

  // 리밸런싱 날짜
  rebalance_dates: Date[];

  // 차트 데이터
  chart_data: {
    dates: string[];
    portfolio_values: number[];
    cash_balances: number[];
    cumulative_returns: number[];
    drawdowns: number[];
  };
}
```

### 3.2 Statistics (통계 정보)
```typescript
interface Statistics {
  // 수익률 지표
  total_return: number;         // 총 수익률 (%)
  annualized_return: number;    // 연환산 수익률 (%)
  benchmark_return?: number;    // 벤치마크 수익률 (%)
  excess_return?: number;       // 초과 수익률 (%)

  // 리스크 지표
  max_drawdown: number;         // 최대 낙폭 (%)
  volatility: number;           // 변동성 (%)
  downside_volatility: number;  // 하방 변동성 (%)

  // 리스크 조정 수익률
  sharpe_ratio: number;         // 샤프 비율
  sortino_ratio: number;        // 소르티노 비율
  calmar_ratio: number;         // 칼마 비율

  // 거래 통계
  total_trades: number;         // 총 거래 횟수
  winning_trades: number;       // 수익 거래
  losing_trades: number;        // 손실 거래
  win_rate: number;            // 승률 (%)
  avg_win: number;             // 평균 수익 (%)
  avg_loss: number;            // 평균 손실 (%)
  profit_loss_ratio: number;   // 손익비

  // 자산 정보
  initial_capital: number;      // 초기 자본금
  final_capital: number;        // 최종 자본금
  peak_capital: number;         // 최대 자본금

  // 기간 정보
  start_date: Date;            // 시작일
  end_date: Date;              // 종료일
  trading_days: number;        // 거래일수
}
```

### 3.3 PortfolioHolding (현재 보유 종목)
```typescript
interface PortfolioHolding {
  stock_code: string;          // 종목 코드
  stock_name: string;          // 종목명
  quantity: number;            // 보유 수량
  avg_price: number;           // 평균 매수가
  current_price: number;       // 현재가
  value: number;              // 평가금액
  profit: number;             // 손익
  profit_rate: number;        // 수익률 (%)
  weight: number;             // 포트폴리오 비중 (%)
  buy_date: Date;             // 최초 매수일
  hold_days: number;          // 보유일수
  factors: Record<string, number>; // 현재 팩터 값
}
```

## 4. 실행 흐름

### 4.1 백테스트 실행 과정
1. **요청 수신**: API 엔드포인트로 백테스트 요청 수신
2. **데이터 로드**:
   - 주가 데이터: ~1.25M 행 (5,000 종목 × 250일)
   - 재무 데이터: ~40K 행 (5,000 종목 × 4분기 × 2년)
3. **팩터 계산**: 13개 팩터 계산
4. **포트폴리오 시뮬레이션**:
   - 일별 거래 실행
   - 리밸런싱 (월별/분기별 등)
   - 손익 계산
5. **통계 계산**: 수익률, 리스크, 샤프 비율 등
6. **결과 저장**: 6개 테이블에 분산 저장
7. **응답 반환**: JSON 형식으로 결과 반환

### 4.2 데이터 흐름도
```
User Request → API Gateway → BacktestEngine
                                ↓
                         Load Data from RDS
                                ↓
                         Calculate Factors
                                ↓
                         Simulate Portfolio
                                ↓
                         Calculate Statistics
                                ↓
                         Save to Database
                                ↓
                         Return Response → User
```

## 5. 사용 예시

### 5.1 백테스트 실행
```python
import requests

# 백테스트 요청
response = requests.post(
    "http://localhost:8000/api/v1/genport/backtest",
    json={
        "buy_conditions": [
            {"factor": "PER", "operator": "<", "value": 15},
            {"factor": "ROE", "operator": ">", "value": 10},
            {"factor": "MOMENTUM_3M", "operator": ">", "value": 0}
        ],
        "sell_conditions": [
            {"type": "STOP_LOSS", "value": 10},
            {"type": "TAKE_PROFIT", "value": 20},
            {"type": "HOLD_DAYS", "value": 60}
        ],
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "initial_capital": 100000000,
        "commission_rate": 0.00015,
        "slippage": 0.001
    }
)

result = response.json()
print(f"총 수익률: {result['statistics']['total_return']:.2f}%")
print(f"최대 낙폭: {result['statistics']['max_drawdown']:.2f}%")
print(f"샤프 비율: {result['statistics']['sharpe_ratio']:.2f}")
```

### 5.2 결과 조회
```python
# 백테스트 ID로 결과 조회
backtest_id = result["backtest_id"]
response = requests.get(
    f"http://localhost:8000/api/v1/genport/backtest/{backtest_id}"
)

detailed_result = response.json()
```

## 6. 테이블 생성 스크립트

```bash
# 테이블 생성
cd /Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end
python3 scripts/create_backtest_tables.py
```

## 7. 주요 특징

### 7.1 사용자 설정 가능 항목
- **수수료율**: 0% ~ 1% (기본값: 0.015%)
- **슬리피지**: 0% ~ 10% (기본값: 0.1%)
- **리밸런싱 주기**: DAILY, WEEKLY, MONTHLY, QUARTERLY
- **포지션 사이징**: EQUAL_WEIGHT, MARKET_CAP, RISK_PARITY
- **최대 보유 종목**: 1 ~ 100개 (기본값: 20개)

### 7.2 고정 항목
- **거래세율**: 0.23% (한국 주식시장 고정값)

### 7.3 성능 최적화
- 비동기 데이터베이스 접근 (SQLAlchemy AsyncSession)
- pandas/polars 활용한 대용량 데이터 처리
- 인메모리 계산 후 일괄 저장
- 인덱스 최적화

## 8. 완성 상태

### ✅ 완료된 항목
1. 데이터베이스 모델 (6개 테이블)
2. 백테스트 엔진 구현
3. 팩터 계산 로직 (13개 팩터)
4. 포트폴리오 시뮬레이션
5. 통계 계산
6. API 엔드포인트 (6개)
7. 결과 저장 로직 (`_save_result()`)
8. 결과 조회 로직
9. 라우터 등록

### 📝 추가 필요 사항 (선택적)
1. 벤치마크 데이터 연동 (KOSPI, KOSDAQ 지수)
2. 실시간 진행 상황 업데이트 (WebSocket)
3. 백테스트 결과 캐싱
4. 병렬 처리 최적화

## 9. 요약

GenPort 스타일 백테스트 시스템이 완전히 구현되었습니다:
- **데이터베이스**: 6개 테이블로 구성된 정규화된 스키마
- **API**: RESTful 엔드포인트 6개
- **엔진**: 13개 팩터 기반 백테스트 실행
- **결과**: 상세한 통계 및 시계열 데이터 제공

프론트엔드는 이 API를 호출하여 GenPort 스타일의 백테스트 결과 화면을 구현할 수 있습니다.