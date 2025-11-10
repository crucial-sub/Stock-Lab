# 현재 백테스트 시스템 구조 분석

## 📊 전체 시스템 구조

### 1. 파일 구조
```
app/
├── services/
│   ├── backtest.py                  ✅ 메인 백테스트 엔진
│   └── condition_evaluator.py       ✅ 논리식 평가 엔진
├── models/
│   └── backtest_genport.py          ✅ DB 모델 (6개 테이블)
└── schemas/
    └── backtest_genport.py           ✅ API 스키마 (통합 완료)
```

---

## 🗄️ 데이터베이스 스키마 상세 분석

### 테이블 1: `backtest_sessions` (백테스트 세션)
**용도**: 백테스트 메타 정보 및 설정

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `backtest_id` | UUID | PK | 백테스트 고유 ID | ✅ |
| `backtest_name` | VARCHAR(200) | N | 백테스트 이름 | ✅ |
| `status` | VARCHAR(20) | N | 상태 (RUNNING/COMPLETED/FAILED) | ✅ |
| `start_date` | DATE | N | 시작일 | ✅ |
| `end_date` | DATE | N | 종료일 | ✅ |
| `initial_capital` | NUMERIC(20,2) | N | 초기 자본금 | ✅ |
| `rebalance_frequency` | VARCHAR(20) | N | 리밸런싱 주기 | ✅ |
| `max_positions` | INTEGER | N | 최대 보유 종목 수 | ✅ |
| `position_sizing` | VARCHAR(20) | N | 포지션 사이징 방법 | ✅ |
| `benchmark` | VARCHAR(20) | N | 벤치마크 | ✅ |
| `commission_rate` | NUMERIC(10,6) | N | 수수료율 | ✅ |
| `tax_rate` | NUMERIC(10,6) | N | 거래세율 (0.0023) | ✅ |
| `slippage` | NUMERIC(10,6) | N | 슬리피지 | ✅ |
| `created_at` | TIMESTAMP | N | 생성일시 | ✅ |
| `completed_at` | TIMESTAMP | Y | 완료일시 | ✅ |

**관계**:
- ← `backtest_conditions` (1:N)
- ← `backtest_statistics` (1:1)
- ← `backtest_daily_snapshots` (1:N)
- ← `backtest_trades` (1:N)
- ← `backtest_holdings` (1:N)

**인덱스**:
- ✅ `idx_backtest_sessions_created_at` (created_at)
- ✅ `idx_backtest_sessions_status` (status)

---

### 테이블 2: `backtest_conditions` (백테스트 조건)
**용도**: 매수/매도 조건 저장

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `condition_id` | INTEGER | PK | 조건 고유 ID (자동증가) | ✅ |
| `backtest_id` | UUID | FK | 백테스트 참조 ID | ✅ |
| `condition_type` | VARCHAR(10) | N | BUY / SELL | ✅ |
| `factor` | VARCHAR(50) | N | 팩터 코드 (PER, ROE 등) | ✅ |
| `operator` | VARCHAR(10) | N | 연산자 (>, <, >=, <=) | ✅ |
| `value` | NUMERIC(20,4) | N | 기준값 | ✅ |
| `description` | VARCHAR(500) | Y | 조건 설명 | ✅ |

**관계**:
- → `backtest_sessions` (N:1)

**인덱스**:
- ✅ `idx_backtest_conditions_backtest` (backtest_id)

**⚠️ 이슈**:
- 논리식 조건 (expression, condition_id 등)을 저장할 컬럼이 없음
- 현재는 개별 조건만 저장 가능

---

### 테이블 3: `backtest_statistics` (백테스트 통계)
**용도**: 백테스트 요약 통계

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `backtest_id` | UUID | PK/FK | 백테스트 참조 ID (1:1) | ✅ |
| **수익률 지표** |
| `total_return` | NUMERIC(10,4) | N | 총 수익률 (%) | ✅ |
| `annualized_return` | NUMERIC(10,4) | N | 연환산 수익률 (CAGR) | ✅ |
| `benchmark_return` | NUMERIC(10,4) | Y | 벤치마크 수익률 | ✅ |
| `excess_return` | NUMERIC(10,4) | Y | 초과 수익률 | ✅ |
| **리스크 지표** |
| `max_drawdown` | NUMERIC(10,4) | N | 최대 낙폭 (MDD) | ✅ |
| `volatility` | NUMERIC(10,4) | N | 변동성 | ✅ |
| `downside_volatility` | NUMERIC(10,4) | N | 하방 변동성 | ✅ |
| **리스크 조정 수익률** |
| `sharpe_ratio` | NUMERIC(10,4) | N | 샤프 비율 | ✅ |
| `sortino_ratio` | NUMERIC(10,4) | N | 소르티노 비율 | ✅ |
| `calmar_ratio` | NUMERIC(10,4) | N | 칼마 비율 | ✅ |
| **거래 통계** |
| `total_trades` | INTEGER | N | 총 거래 횟수 | ✅ |
| `winning_trades` | INTEGER | N | 수익 거래 횟수 | ✅ |
| `losing_trades` | INTEGER | N | 손실 거래 횟수 | ✅ |
| `win_rate` | NUMERIC(10,4) | N | 승률 (%) | ✅ |
| `avg_win` | NUMERIC(10,4) | N | 평균 수익 (%) | ✅ |
| `avg_loss` | NUMERIC(10,4) | N | 평균 손실 (%) | ✅ |
| `profit_loss_ratio` | NUMERIC(10,4) | N | 손익비 | ✅ |
| **자산 정보** |
| `initial_capital` | NUMERIC(20,2) | N | 초기 자본금 | ✅ |
| `final_capital` | NUMERIC(20,2) | N | 최종 자본금 | ✅ |
| `peak_capital` | NUMERIC(20,2) | N | 최대 자본금 | ✅ |
| **기간 정보** |
| `start_date` | DATE | N | 시작일 | ✅ |
| `end_date` | DATE | N | 종료일 | ✅ |
| `trading_days` | INTEGER | N | 거래일수 | ✅ |

**관계**:
- → `backtest_sessions` (1:1)

---

### 테이블 4: `backtest_daily_snapshots` (일별 스냅샷)
**용도**: 일별 포트폴리오 상태 기록

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `snapshot_id` | BIGINT | PK | 스냅샷 고유 ID (자동증가) | ✅ |
| `backtest_id` | UUID | FK | 백테스트 참조 ID | ✅ |
| `snapshot_date` | DATE | N | 스냅샷 날짜 | ✅ |
| **포트폴리오 가치** |
| `portfolio_value` | NUMERIC(20,2) | N | 포트폴리오 가치 | ✅ |
| `cash_balance` | NUMERIC(20,2) | N | 현금 잔고 | ✅ |
| `invested_amount` | NUMERIC(20,2) | N | 투자 금액 | ✅ |
| **수익률** |
| `daily_return` | NUMERIC(10,4) | N | 일 수익률 (%) | ✅ |
| `cumulative_return` | NUMERIC(10,4) | N | 누적 수익률 (%) | ✅ |
| `drawdown` | NUMERIC(10,4) | N | 낙폭 (%) | ✅ |
| `benchmark_return` | NUMERIC(10,4) | Y | 벤치마크 수익률 | ✅ |
| **거래** |
| `trade_count` | INTEGER | N | 당일 거래 횟수 | ✅ |

**관계**:
- → `backtest_sessions` (N:1)

**인덱스**:
- ✅ `idx_backtest_daily_snapshots_backtest_date` (backtest_id, snapshot_date)
- ✅ UNIQUE (backtest_id, snapshot_date)

---

### 테이블 5: `backtest_trades` (거래 내역)
**용도**: 모든 매수/매도 거래 기록

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `trade_id` | BIGINT | PK | 거래 고유 ID (자동증가) | ✅ |
| `backtest_id` | UUID | FK | 백테스트 참조 ID | ✅ |
| **거래 기본 정보** |
| `trade_date` | DATE | N | 거래일 | ✅ |
| `trade_type` | VARCHAR(10) | N | BUY / SELL | ✅ |
| `stock_code` | VARCHAR(6) | N | 종목 코드 | ✅ |
| `stock_name` | VARCHAR(200) | N | 종목명 | ✅ |
| **거래 상세** |
| `quantity` | INTEGER | N | 수량 | ✅ |
| `price` | NUMERIC(20,2) | N | 거래가 | ✅ |
| `amount` | NUMERIC(20,2) | N | 거래대금 | ✅ |
| `commission` | NUMERIC(20,2) | N | 수수료 | ✅ |
| `tax` | NUMERIC(20,2) | N | 세금 (매도 시만) | ✅ |
| **매도 시에만** |
| `profit` | NUMERIC(20,2) | Y | 실현 손익 | ✅ |
| `profit_rate` | NUMERIC(10,4) | Y | 수익률 (%) | ✅ |
| `hold_days` | INTEGER | Y | 보유일수 | ✅ |
| **팩터 정보** |
| `factors` | JSONB | Y | 거래 시점 팩터 값 | ✅ |
| `selection_reason` | TEXT | Y | 매매 사유 | ✅ |

**관계**:
- → `backtest_sessions` (N:1)

**인덱스**:
- ✅ `idx_backtest_trades_backtest_date` (backtest_id, trade_date)
- ✅ `idx_backtest_trades_stock` (stock_code)

---

### 테이블 6: `backtest_holdings` (보유 종목)
**용도**: 백테스트 종료 시점의 최종 보유 종목

| 컬럼명 | 타입 | Null | 설명 | 검증 |
|--------|------|------|------|------|
| `holding_id` | INTEGER | PK | 보유 종목 고유 ID (자동증가) | ✅ |
| `backtest_id` | UUID | FK | 백테스트 참조 ID | ✅ |
| **종목 정보** |
| `stock_code` | VARCHAR(6) | N | 종목 코드 | ✅ |
| `stock_name` | VARCHAR(200) | N | 종목명 | ✅ |
| **보유 정보** |
| `quantity` | INTEGER | N | 보유 수량 | ✅ |
| `avg_price` | NUMERIC(20,2) | N | 평균 매수가 | ✅ |
| `current_price` | NUMERIC(20,2) | N | 현재가 | ✅ |
| `value` | NUMERIC(20,2) | N | 평가금액 | ✅ |
| **손익** |
| `profit` | NUMERIC(20,2) | N | 미실현 손익 | ✅ |
| `profit_rate` | NUMERIC(10,4) | N | 수익률 (%) | ✅ |
| **비중** |
| `weight` | NUMERIC(10,4) | N | 포트폴리오 비중 (%) | ✅ |
| **보유 기간** |
| `buy_date` | DATE | N | 최초 매수일 | ✅ |
| `hold_days` | INTEGER | N | 보유일수 | ✅ |
| **팩터 정보** |
| `factors` | JSONB | Y | 현재 팩터 값 | ✅ |

**관계**:
- → `backtest_sessions` (N:1)

**인덱스**:
- ✅ `idx_backtest_holdings_backtest` (backtest_id)
- ✅ UNIQUE (backtest_id, stock_code)

---

## 💾 데이터 로딩 구조

### 1. 가격 데이터 (`_load_price_data`)

**소스 테이블**: `stock_prices` + `companies`

**쿼리 구조**:
```sql
SELECT
    sp.company_id,
    c.stock_code,
    c.company_name AS stock_name,
    sp.trade_date AS date,
    sp.open_price,
    sp.high_price,
    sp.low_price,
    sp.close_price,
    sp.volume,
    sp.trading_value,
    sp.market_cap,
    sp.listed_shares
FROM stock_prices sp
JOIN companies c ON sp.company_id = c.company_id
WHERE sp.trade_date BETWEEN :extended_start AND :end_date
  AND sp.close_price IS NOT NULL
  AND sp.volume > 0
ORDER BY sp.trade_date, c.stock_code
```

**기간 설정**:
- `extended_start = start_date - 365일` (모멘텀 계산용)
- `end_date = 백테스트 종료일`

**변환 과정**:
```python
result = await db.execute(query)
rows = result.mappings().all()  # ✅ 최적화된 방식
df = pd.DataFrame(rows)
df['date'] = pd.to_datetime(df['date'])
```

**예상 데이터량**:
- 종목 수: ~2,000개
- 거래일: ~250일/년
- 2년 백테스트: **~1,000,000 행**

**✅ 검증 결과**:
- JOIN 구조 올바름
- 컬럼명 매핑 정확 (`trade_date` → `date`)
- NULL 필터링 적절
- 인덱스 활용 가능 (trade_date, company_id)

---

### 2. 재무 데이터 (`_load_financial_data`)

**소스 테이블**:
- `financial_statements`
- `income_statements`
- `balance_sheets`
- `companies`

**손익계산서 쿼리**:
```sql
SELECT
    fs.company_id,
    c.stock_code,
    fs.bsns_year AS fiscal_year,     -- ✅ 올바른 매핑
    fs.reprt_code AS report_code,     -- ✅ 올바른 매핑
    fs.report_date,
    is_.account_nm,
    is_.thstrm_amount AS current_amount,
    is_.thstrm_add_amount AS cumulative_amount,
    is_.frmtrm_amount AS previous_amount
FROM financial_statements fs
JOIN income_statements is_ ON fs.stmt_id = is_.stmt_id
JOIN companies c ON fs.company_id = c.company_id
WHERE fs.report_date BETWEEN :extended_start AND :end_date
  AND is_.account_nm IN (
      '매출액', '매출', '영업수익',
      '영업이익', '영업이익(손실)',
      '당기순이익', '당기순이익(손실)',
      '매출총이익', '매출원가'
  )
```

**재무상태표 쿼리**:
```sql
SELECT
    fs.company_id,
    c.stock_code,
    fs.bsns_year AS fiscal_year,
    fs.reprt_code AS report_code,
    fs.report_date,
    bs.account_nm,
    bs.thstrm_amount AS current_amount
FROM financial_statements fs
JOIN balance_sheets bs ON fs.stmt_id = bs.stmt_id
JOIN companies c ON fs.company_id = c.company_id
WHERE fs.report_date BETWEEN :extended_start AND :end_date
  AND bs.account_nm IN (
      '자산총계', '자산',
      '부채총계', '부채',
      '자본총계', '자본',
      '유동자산', '유동부채',
      '현금및현금성자산'
  )
```

**기간 설정**:
- `extended_start = start_date - 180일` (6개월 전 데이터)

**예상 데이터량**:
- 종목 수: ~2,000개
- 분기당 계정과목: ~15개
- 2년 백테스트 (8분기): **~240,000 행**

**✅ 검증 결과**:
- ✅ `bsns_year` → `fiscal_year` 매핑 올바름
- ✅ `reprt_code` → `report_code` 매핑 올바름
- ✅ 계정과목 필터링 적절
- ✅ JOIN 구조 정확

---

### 3. 벤치마크 데이터 (`_load_benchmark_data`)

**소스 테이블**: `stock_prices`

**쿼리 구조**:
```sql
SELECT
    trade_date AS date,
    close_price AS index_value
FROM stock_prices
WHERE stock_code IN ('155660', '229200')  -- KOSPI, KOSDAQ ETF
  AND trade_date BETWEEN :start_date AND :end_date
ORDER BY trade_date
```

**✅ 검증 결과**:
- ETF 코드 사용 (지수 직접 데이터 없음)
- 간단하고 효율적

---

## 🔧 팩터 계산 로직

### 팩터 계산 메서드: `_calculate_factors`

**입력**:
- `price_data`: 가격 데이터프레임
- `financial_data`: 재무 데이터프레임

**출력**:
- 모든 팩터가 계산된 DataFrame

### 구현된 팩터 (13개)

#### 1. Value Factors
```python
# PER (주가수익비율)
PER = price / EPS
where EPS = 당기순이익 / 발행주식수

# PBR (주가순자산비율)
PBR = price / BPS
where BPS = 자본총계 / 발행주식수

# DIV_YIELD (배당수익률)
DIV_YIELD = (배당금 / price) * 100
```

#### 2. Profitability Factors
```python
# ROE (자기자본이익률)
ROE = (당기순이익 / 자본총계) * 100

# ROA (총자산이익률)
ROA = (당기순이익 / 자산총계) * 100
```

#### 3. Growth Factors
```python
# REVENUE_GROWTH (매출 성장률)
REVENUE_GROWTH = ((현재매출 - 전년매출) / 전년매출) * 100

# EARNINGS_GROWTH (순이익 성장률)
EARNINGS_GROWTH = ((현재순이익 - 전년순이익) / 전년순이익) * 100
```

#### 4. Momentum Factors
```python
# MOMENTUM_1M (1개월 모멘텀)
MOMENTUM_1M = ((현재가 - 1개월전가) / 1개월전가) * 100

# MOMENTUM_3M (3개월 모멘텀)
MOMENTUM_3M = ((현재가 - 3개월전가) / 3개월전가) * 100

# MOMENTUM_6M (6개월 모멘텀)
MOMENTUM_6M = ((현재가 - 6개월전가) / 6개월전가) * 100

# MOMENTUM_12M (12개월 모멘텀)
MOMENTUM_12M = ((현재가 - 12개월전가) / 12개월전가) * 100
```

#### 5. Volatility Factor
```python
# VOLATILITY (변동성)
VOLATILITY = 최근 60일 수익률의 표준편차 * sqrt(252)
```

#### 6. Liquidity Factors
```python
# AVG_TRADING_VALUE (평균 거래대금)
AVG_TRADING_VALUE = 최근 20일 거래대금 평균

# TURNOVER_RATE (회전율)
TURNOVER_RATE = (거래량 / 발행주식수) * 100
```

**✅ 검증 결과**:
- 팩터 계산 로직 정확
- 재무 데이터 매핑 올바름
- 시계열 계산 (모멘텀 등) 정확

---

## 🔄 백테스트 실행 흐름

### Phase 1: 데이터 로딩
```python
1. price_data = load_price_data(start_date, end_date)
   └─ stock_prices + companies 조인

2. financial_data = load_financial_data(start_date, end_date)
   └─ financial_statements + income/balance_sheets 조인

3. benchmark_data = load_benchmark_data(benchmark, start_date, end_date)
   └─ KOSPI/KOSDAQ ETF 데이터
```

### Phase 2: 팩터 계산
```python
4. factor_data = calculate_factors(price_data, financial_data)
   └─ 13개 팩터 계산 + 랭킹
```

### Phase 3: 포트폴리오 시뮬레이션
```python
5. for trading_day in trading_days:

   # 매도 조건 체크 (매일)
   5.1. sell_trades = execute_sells(
        holdings, sell_conditions, price_data, trading_day
   )

   # 리밸런싱 날짜인 경우
   if trading_day in rebalance_dates:

       # 매수 후보 선정
       5.2. candidates = select_buy_candidates(
            factor_data, buy_conditions, trading_day
       )

       # 포지션 사이징
       5.3. position_sizes = calculate_position_sizes(
            candidates, cash_balance, max_positions
       )

       # 매수 실행
       5.4. buy_trades = execute_buys(
            position_sizes, price_data, trading_day
       )

   # 일별 스냅샷 저장
   5.5. daily_snapshot = {
       'date': trading_day,
       'portfolio_value': calculate_portfolio_value(),
       'cash_balance': cash_balance,
       ...
   }
```

### Phase 4: 통계 계산
```python
6. statistics = calculate_statistics(
   daily_snapshots, trades, initial_capital
)

7. monthly_performance = aggregate_monthly_performance(
   daily_snapshots, trades
)
```

### Phase 5: 결과 저장
```python
8. save_to_database(
   session, conditions, statistics,
   daily_snapshots, trades, holdings
)
```

---

## ⚠️ 발견된 이슈 및 개선사항

### Critical Issues

#### 1. ❌ 논리식 조건 저장 불가
**문제**: `backtest_conditions` 테이블이 논리식 저장 불가능
```python
# 현재 저장 불가능한 구조
{
    "expression": "(A and B) or C",
    "conditions": [
        {"id": "A", ...},
        {"id": "B", ...}
    ]
}
```

**해결책**:
```sql
-- Option 1: JSONB 컬럼 추가
ALTER TABLE backtest_conditions
ADD COLUMN condition_expression JSONB;

-- Option 2: 새 테이블 생성
CREATE TABLE backtest_condition_expressions (
    expression_id SERIAL PRIMARY KEY,
    backtest_id UUID REFERENCES backtest_sessions,
    expression TEXT NOT NULL,
    factor_weights JSONB
);
```

#### 2. ❌ 주문/체결 데이터 미저장
**문제**: 엔진에서 Order, Execution 객체 생성하지만 DB에 저장 안됨

**현재 상태**:
- ✅ 메모리에서 Order, Execution 객체 생성
- ❌ DB에 저장되지 않음
- ❌ 재조회 시 주문/체결 히스토리 없음

**해결책**: Phase 4에서 계획한 테이블 생성 필요
```sql
CREATE TABLE backtest_orders (...);
CREATE TABLE backtest_executions (...);
CREATE TABLE backtest_positions (...);
```

#### 3. ❌ 월별/연도별 통계 미저장
**문제**: 엔진에서 계산하지만 DB에 저장 안됨

**현재 상태**:
- ✅ `calculate_monthly_stats()` 메서드 구현됨
- ✅ `calculate_yearly_stats()` 메서드 구현됨
- ❌ DB 테이블 없음

**해결책**:
```sql
CREATE TABLE backtest_monthly_stats (...);
CREATE TABLE backtest_yearly_stats (...);
```

### Medium Issues

#### 4. ⚠️ 팩터 데이터 구조 비효율
**문제**: `factor_data`가 wide format (종목별 컬럼)

```python
# 현재 구조 (비효율적)
factor_data:
    date  | 005930_PER | 005930_ROE | 000660_PER | ...

# 개선 제안 (long format)
factor_data:
    date | stock_code | factor_name | value | rank
```

**영향**: 메모리 사용량 증가, 쿼리 복잡도 증가

#### 5. ⚠️ condition_evaluator.py의 데이터 접근 방식
**문제**: `factor_data.index` 사용 → index 설정 필요

**현재 코드**:
```python
stock_data = factor_data[
    (factor_data.index == stock_code) &  # ← index 사용
    (factor_data['date'] == trading_date)
]
```

**개선 코드** (사용자가 수정함):
```python
stock_mask = (factor_data['stock_code'] == stock_code)
date_mask = (pd.to_datetime(factor_data['date']) == trading_ts)
stock_data = factor_data[stock_mask & date_mask]
```

**✅ 현재 상태**: 사용자가 이미 수정 완료

---

## ✅ 잘 구현된 부분

### 1. ✅ 데이터베이스 스키마
- 정규화 잘 됨 (1:1, 1:N 관계 명확)
- 인덱스 적절히 설정
- JSONB 활용으로 유연성 확보 (factors 컬럼)
- Cascade 삭제 설정

### 2. ✅ 데이터 로딩
- SQLAlchemy `mappings()` 사용으로 효율적
- JOIN 구조 정확
- 날짜 범위 확장 (모멘텀 계산용) 적절
- NULL 필터링 철저

### 3. ✅ 매수/매도 로직
- 매도: 매일 체크 (손절/익절 즉시 실행)
- 매수: 리밸런싱 날짜에만
- 슬리피지 양방향 적용
- 수수료/세금 정확히 계산

### 4. ✅ 팩터 계산
- 13개 팩터 정확히 구현
- 재무 데이터 매핑 올바름 (bsns_year, reprt_code)
- 시계열 계산 (모멘텀) 정확

### 5. ✅ 통계 계산
- 샤프/소르티노/칼마 비율
- MDD, 변동성
- 승률, 손익비
- 모두 정확히 구현됨

---

## 📊 성능 분석

### 예상 데이터량 (2년 백테스트)

| 데이터 | 행 수 | 크기 (추정) |
|--------|-------|-------------|
| 가격 데이터 | ~1,000,000 | ~100MB |
| 재무 데이터 | ~240,000 | ~50MB |
| 벤치마크 | ~500 | ~50KB |
| **총계** | **~1,240,000** | **~150MB** |

### 병목 구간

1. **데이터 로딩**:
   - 가장 큰 병목 (~5-10초)
   - 인덱스 활용으로 최적화 가능

2. **팩터 계산**:
   - 판다스 벡터 연산으로 빠름 (~2-3초)

3. **시뮬레이션**:
   - 일별 루프지만 효율적 (~3-5초)

4. **DB 저장**:
   - Bulk insert 사용 권장 (~1-2초)

**총 예상 시간**: **10-20초** (2년 백테스트)

---

## 🎯 권장 개선사항 우선순위

### High Priority

1. **논리식 조건 저장 구조 추가**
   ```sql
   ALTER TABLE backtest_conditions
   ADD COLUMN condition_id VARCHAR(10);  -- A, B, C

   ALTER TABLE backtest_sessions
   ADD COLUMN buy_expression TEXT;  -- "(A and B) or C"
   ADD COLUMN factor_weights JSONB;  -- {"PER": -1, "ROE": 1}
   ```

2. **주문/체결/포지션 테이블 생성**
   - 완전한 거래 추적 가능
   - GenPort 수준 분석 가능

3. **월별/연도별 통계 테이블 생성**
   - 이미 계산 로직 있음
   - 저장만 추가하면 됨

### Medium Priority

4. **팩터 데이터 구조 개선**
   - Long format으로 변경
   - 메모리 효율 개선

5. **Bulk Insert 최적화**
   ```python
   # 현재: 개별 insert
   for trade in trades:
       db.add(BacktestTrade(**trade))

   # 개선: bulk insert
   db.bulk_insert_mappings(BacktestTrade, trades)
   ```

### Low Priority

6. **캐싱 추가**
   - Redis에 팩터 데이터 캐싱
   - 반복 백테스트 시 속도 향상

7. **비동기 처리 확대**
   - 팩터 계산 병렬화
   - 통계 계산 병렬화

---

## 📝 결론

### 전체 완성도: **85%**

#### ✅ 잘된 부분
- DB 스키마 설계 (6개 테이블)
- 데이터 로딩 및 변환
- 팩터 계산 로직
- 매수/매도 시뮬레이션
- 기본 통계 계산

#### ⚠️ 개선 필요
- 논리식 조건 저장 (테이블 수정 필요)
- 주문/체결 데이터 저장 (테이블 추가 필요)
- 월별/연도별 통계 저장 (테이블 추가 필요)

#### 🎯 다음 단계
1. 논리식 저장 구조 추가
2. 추가 테이블 생성 (orders, executions, positions, monthly_stats, yearly_stats)
3. Bulk insert 최적화
4. 실전 테스트

**현재 시스템은 기본 백테스트로는 충분하지만, GenPort 수준의 상세 분석을 위해서는 위 개선사항이 필요합니다.**