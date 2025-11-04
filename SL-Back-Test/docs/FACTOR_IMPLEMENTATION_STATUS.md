# 팩터 구현 상태 보고서

## 📊 전체 요약

- **총 팩터 수**: 22개
- **구현 가능**: 20개 ✅
- **구현 불가**: 2개 ❌

---

## ✅ 구현 완료 팩터 (20개)

### 1. 가치 팩터 (Value) - 4개

| # | 팩터 이름 | API Endpoint | Input 데이터 | Output |
|---|----------|-------------|------------|--------|
| 1 | **PER (주가수익비율)** | `POST /api/v1/factors/per` | - 일별 시세 (close_price, listed_shares)<br>- 손익계산서 (당기순이익) | stock_code, company_name, close_price, eps, per, rank |
| 2 | **PBR (주가순자산비율)** | `POST /api/v1/factors/pbr` | - 일별 시세 (close_price, listed_shares)<br>- 재무상태표 (자본총계) | stock_code, company_name, close_price, bps, pbr, rank |
| 3 | **PSR (주가매출비율)** | `POST /api/v1/factors/psr` | - 일별 시세 (market_cap)<br>- 손익계산서 (매출액) | stock_code, company_name, market_cap, revenue, psr, rank |
| 4 | **PCR (주가현금흐름비율)** | `POST /api/v1/factors/pcr` | - 일별 시세 (market_cap)<br>- 현금흐름표 (영업활동현금흐름) | stock_code, company_name, market_cap, operating_cashflow, pcr, rank |

**계산 공식**:
- `PER = 주가 / EPS`, where `EPS = 당기순이익 / 발행주식수`
- `PBR = 주가 / BPS`, where `BPS = 자본총계 / 발행주식수`
- `PSR = 시가총액 / 매출액`
- `PCR = 시가총액 / 영업활동현금흐름`

---

### 2. 퀄리티 팩터 (Quality) - 5개

| # | 팩터 이름 | API Endpoint | Input 데이터 | Output |
|---|----------|-------------|------------|--------|
| 5 | **ROE (자기자본이익률)** | `POST /api/v1/factors/roe` | - 손익계산서 (당기순이익)<br>- 재무상태표 (자본총계) | stock_code, company_name, net_income, equity, roe, rank |
| 6 | **ROA (총자산이익률)** | `POST /api/v1/factors/roa` | - 손익계산서 (당기순이익)<br>- 재무상태표 (자산총계) | stock_code, company_name, net_income, total_assets, roa, rank |
| 7 | **매출총이익률** | `POST /api/v1/factors/gross-profit-margin` | - 손익계산서 (매출액, 매출원가) | stock_code, company_name, revenue, gross_profit, margin, rank |
| 8 | **부채비율** | `POST /api/v1/factors/debt-ratio` | - 재무상태표 (부채총계, 자본총계) | stock_code, company_name, liabilities, equity, debt_ratio, rank |
| 9 | **유동비율** | `POST /api/v1/factors/current-ratio` | - 재무상태표 (유동자산, 유동부채) | stock_code, company_name, current_assets, current_liabilities, ratio, rank |

**계산 공식**:
- `ROE = (당기순이익 / 자본총계) × 100`
- `ROA = (당기순이익 / 자산총계) × 100`
- `매출총이익률 = ((매출액 - 매출원가) / 매출액) × 100`
- `부채비율 = (부채총계 / 자본총계) × 100`
- `유동비율 = (유동자산 / 유동부채) × 100`

---

### 3. 성장 팩터 (Growth) - 4개

| # | 팩터 이름 | API Endpoint | Input 데이터 | Output |
|---|----------|-------------|------------|--------|
| 10 | **매출액증가율** | `POST /api/v1/factors/revenue-growth` | - 손익계산서 (당기매출, 전기매출) | stock_code, company_name, current_revenue, previous_revenue, growth, rank |
| 11 | **영업이익증가율** | `POST /api/v1/factors/operating-profit-growth` | - 손익계산서 (당기영업이익, 전기영업이익) | stock_code, company_name, current_op, previous_op, growth, rank |
| 12 | **EPS증가율** | `POST /api/v1/factors/eps-growth` | - 손익계산서 (당기EPS, 전기EPS) | stock_code, company_name, current_eps, previous_eps, growth, rank |
| 13 | **자산증가율** | `POST /api/v1/factors/asset-growth` | - 재무상태표 (당기자산, 전기자산) | stock_code, company_name, current_assets, previous_assets, growth, rank |

**계산 공식**:
- `증가율 = ((당기 - 전기) / 전기) × 100`

---

### 4. 모멘텀 팩터 (Momentum) - 5개

| # | 팩터 이름 | API Endpoint | Input 데이터 | Output |
|---|----------|-------------|------------|--------|
| 14 | **3개월 수익률** | `POST /api/v1/factors/momentum-3m` | - 일별 시세 (현재가, 3개월전 종가) | stock_code, company_name, current_price, past_price, return_pct, rank |
| 15 | **12개월 수익률** | `POST /api/v1/factors/momentum-12m` | - 일별 시세 (현재가, 12개월전 종가) | stock_code, company_name, current_price, past_price, return_pct, rank |
| 16 | **거래량** | `POST /api/v1/factors/volume` | - 일별 시세 (최근 20일 거래량) | stock_code, company_name, avg_volume, rank |
| 17 | **거래대금** | `POST /api/v1/factors/trading-value` | - 일별 시세 (최근 20일 거래대금) | stock_code, company_name, avg_trading_value, rank |
| 18 | **52주 최고가 대비** | `POST /api/v1/factors/high-52w-ratio` | - 일별 시세 (현재가, 52주 최고가) | stock_code, company_name, current_price, high_52w, ratio, rank |

**계산 공식**:
- `수익률 = ((현재가 - 과거가) / 과거가) × 100`
- `평균거래량 = SUM(거래량) / N일`
- `52주 최고가 대비 = 현재가 / MAX(52주 고가)`

---

### 5. 규모 팩터 (Size) - 3개

| # | 팩터 이름 | API Endpoint | Input 데이터 | Output |
|---|----------|-------------|------------|--------|
| 19 | **시가총액** | `POST /api/v1/factors/market-cap` | - 일별 시세 (market_cap) | stock_code, company_name, market_cap, rank |
| 20 | **매출액** | `POST /api/v1/factors/revenue` | - 손익계산서 (매출액) | stock_code, company_name, revenue, rank |
| 21 | **총자산** | `POST /api/v1/factors/total-assets` | - 재무상태표 (자산총계) | stock_code, company_name, total_assets, rank |

---

## ❌ 구현 불가능 팩터 (2개)

| # | 팩터 이름 | 구현 불가 이유 |
|---|----------|--------------|
| 22 | **배당수익률** | **자본변동표 (Statement of Changes in Equity) 테이블이 ERD에 존재하지 않음**<br><br>배당금 데이터는 자본변동표에 기록되지만, 현재 ERD_GUIDE.md에는 다음 7개 테이블만 정의되어 있음:<br>1. companies<br>2. stock_prices<br>3. disclosures<br>4. financial_statements<br>5. balance_sheets<br>6. income_statements<br>7. cashflow_statements<br><br>**해결 방법**:<br>1. `equity_changes` 테이블 추가 생성<br>2. DART API에서 자본변동표 데이터 수집<br>3. 배당금 총액 컬럼 추가 |

---

## 📋 API 공통 Request/Response 형식

### Request Body (공통)
```json
{
  "stock_codes": ["005930", "000660"],  // Optional, 없으면 전체
  "base_date": "2024-11-04",            // 기준일 (YYYY-MM-DD)
  "market_type": "KOSPI"                // Optional: KOSPI/KOSDAQ/ALL
}
```

### Response Body (공통)
```json
{
  "factor_id": "PER",
  "factor_name": "주가수익비율",
  "base_date": "2024-11-04",
  "data": [
    {
      "stock_code": "005930",
      "company_name": "삼성전자",
      "value": 12.5,
      "rank": 1
    }
  ],
  "total_count": 2500,
  "calculation_time_ms": 1234.56
}
```

---

## 🚀 사용 예시

### 1. 단일 팩터 조회
```bash
curl -X POST "http://localhost:8000/api/v1/factors/per" \
  -H "Content-Type: application/json" \
  -d '{
    "base_date": "2024-11-04",
    "market_type": "KOSPI"
  }'
```

### 2. 멀티 팩터 조합
```bash
curl -X POST "http://localhost:8000/api/v1/factors/multi" \
  -H "Content-Type: application/json" \
  -d '{
    "factor_ids": ["PER", "PBR", "ROE"],
    "weights": {"PER": 0.4, "PBR": 0.3, "ROE": 0.3},
    "base_date": "2024-11-04",
    "market_type": "ALL"
  }'
```

---

## 🗄️ 데이터 요구사항

### 필요한 테이블별 컬럼

#### 1. companies
- `company_id`, `stock_code`, `company_name`, `market_type`, `is_active`

#### 2. stock_prices
- `company_id`, `trade_date`, `close_price`, `open_price`, `high_price`, `low_price`
- `volume`, `trading_value`, `market_cap`, `listed_shares`

#### 3. financial_statements
- `stmt_id`, `company_id`, `bsns_year`, `reprt_code`, `fs_div`, `report_date`

#### 4. balance_sheets
- `stmt_id`, `account_nm`, `thstrm_amount`, `frmtrm_amount`
- 필요 계정과목: 자산총계, 부채총계, 자본총계, 유동자산, 유동부채

#### 5. income_statements
- `stmt_id`, `account_nm`, `thstrm_amount`, `frmtrm_amount`
- 필요 계정과목: 매출액, 매출원가, 영업이익, 당기순이익

#### 6. cashflow_statements
- `stmt_id`, `account_nm`, `thstrm_amount`
- 필요 계정과목: 영업활동현금흐름

---

## ⚡ 성능 최적화

### 대용량 데이터 처리 (10GB+)

1. **Polars DataFrame 사용**
   - Pandas 대비 10-100배 빠른 처리
   - Rust 기반 컬럼형 데이터 처리

2. **비동기 쿼리**
   - AsyncPG + SQLAlchemy async
   - 커넥션 풀링 (20 base + 40 overflow)

3. **인덱스 최적화**
   - 복합 인덱스: `(company_id, trade_date, close_price)`
   - 재무제표 조회: `(stmt_id, account_nm)`

4. **Redis 캐싱**
   - 팩터 계산 결과 1시간 캐싱
   - 재무제표 메타 데이터 캐싱

5. **청크 처리**
   - 10,000건 단위로 배치 처리
   - 메모리 사용량 제한

---

## 📊 백테스팅 시뮬레이션 연동

모든 팩터는 백테스팅 시뮬레이션 엔진과 통합되어 사용 가능:

1. **스크리닝 (Screening)**: 조건 충족 종목 필터링
   - 예: PER < 10, ROE > 15%

2. **랭킹 (Ranking)**: 상위/하위 N% 선택
   - 예: PBR 하위 30%, 모멘텀 상위 30%

3. **스코어링 (Scoring)**: 가중 합산 점수
   - 예: PER(40%) + PBR(30%) + ROE(30%)

---

## 🔄 배당수익률 구현을 위한 추가 작업

### 필요한 작업

1. **자본변동표 테이블 생성**
```sql
CREATE TABLE equity_changes (
    ec_id BIGSERIAL PRIMARY KEY,
    stmt_id INTEGER REFERENCES financial_statements(stmt_id),
    account_nm VARCHAR(300),
    dividend_amount BIGINT,  -- 배당금 총액
    ...
);
```

2. **DART API 데이터 수집**
   - 엔드포인트: `/api/fnlttSinglAcntAll.json`
   - 재무제표 유형: `cfs` (자본변동표)

3. **팩터 계산 로직 추가**
```python
async def calculate_dividend_yield(self, base_date, ...):
    # 배당금총액 / 발행주식수 = 주당배당금
    # (주당배당금 / 주가) × 100 = 배당수익률
    ...
```

---

**작성일**: 2025-11-04
**작성자**: AI Assistant
**버전**: 1.0.0
