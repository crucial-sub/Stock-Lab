# 백테스트 엔진 - RDS DB 스키마 매핑

## 개요
`backtest_genport_engine.py`가 RDS 데이터베이스의 실제 테이블 스키마와 올바르게 연동되도록 필드 매핑을 정리한 문서입니다.

---

## 1. 주가 데이터 (StockPrice 테이블)

### 사용하는 필드
| 백테스트 엔진 필드 | DB 컬럼명 | 타입 | 설명 |
|------------------|----------|------|------|
| company_id | company_id | Integer | 기업 고유 ID |
| stock_code | stock_code (via Company join) | String(6) | 종목 코드 |
| stock_name | company_name (via Company join) | String(200) | 종목명 |
| date | trade_date | Date | 거래일자 |
| open_price | open_price | Integer | 시가 |
| high_price | high_price | Integer | 고가 |
| low_price | low_price | Integer | 저가 |
| close_price | close_price | Integer | 종가 |
| volume | volume | BigInteger | 거래량 |
| trading_value | trading_value | BigInteger | 거래대금 |
| market_cap | market_cap | BigInteger | 시가총액 |
| listed_shares | listed_shares | BigInteger | 상장주식수 |

### SQL 쿼리 예시
```python
query = select(
    StockPrice.company_id,
    Company.stock_code,
    Company.company_name.label('stock_name'),
    StockPrice.trade_date.label('date'),
    StockPrice.open_price,
    StockPrice.high_price,
    StockPrice.low_price,
    StockPrice.close_price,
    StockPrice.volume,
    StockPrice.trading_value,
    StockPrice.market_cap,
    StockPrice.listed_shares
).join(
    Company, StockPrice.company_id == Company.company_id
).where(...)
```

**✅ 연동 상태: 정상**

---

## 2. 재무 데이터 (FinancialStatement 테이블)

### 필드 매핑 (수정 완료)

| 백테스트 엔진 필드 | DB 컬럼명 | 타입 | 설명 |
|------------------|----------|------|------|
| fiscal_year | bsns_year | String(4) | 사업연도 (YYYY) |
| report_code | reprt_code | String(5) | 보고서 코드 |
| report_date | report_date | Date | 보고서 제출일 |

### 보고서 코드 (reprt_code) 매핑
| 코드 | 의미 | 분기 정보 |
|------|------|----------|
| 11011 | 사업보고서 | 연간 (4Q) |
| 11012 | 반기보고서 | 2Q |
| 11013 | 1분기보고서 | 1Q |
| 11014 | 3분기보고서 | 3Q |

### SQL 쿼리 예시
```python
income_query = select(
    FinancialStatement.company_id,
    Company.stock_code,
    FinancialStatement.bsns_year.label('fiscal_year'),  # ✅ 수정됨
    FinancialStatement.reprt_code.label('report_code'),  # ✅ 수정됨
    FinancialStatement.report_date,
    IncomeStatement.account_nm,
    IncomeStatement.thstrm_amount.label('current_amount'),
    ...
).join(...)
```

**✅ 연동 상태: 수정 완료**

---

## 3. 손익계산서 (IncomeStatement 테이블)

### 사용하는 계정과목
| 계정과목명 | 용도 |
|-----------|------|
| 매출액, 매출, 영업수익 | 매출 팩터 계산 |
| 영업이익, 영업이익(손실) | 수익성 팩터 계산 |
| 당기순이익, 당기순이익(손실) | ROE, ROA, 성장률 계산 |
| 매출총이익 | 매출총이익률 계산 |
| 매출원가 | 매출총이익 계산 |

### 필드
| 백테스트 엔진 필드 | DB 컬럼명 | 설명 |
|------------------|----------|------|
| current_amount | thstrm_amount | 당기 금액 (해당 분기) |
| cumulative_amount | thstrm_add_amount | 당기 누적 금액 (연초부터 누적) |
| previous_amount | frmtrm_amount | 전기 금액 |

**✅ 연동 상태: 정상**

---

## 4. 재무상태표 (BalanceSheet 테이블)

### 사용하는 계정과목
| 계정과목명 | 용도 |
|-----------|------|
| 자산총계 | ROA, 총자산 계산 |
| 자본총계 | ROE, PBR 계산 |
| 부채총계 | 레버리지 계산 |
| 유동자산 | 유동성 분석 |
| 유동부채 | 유동비율 계산 |
| 비유동부채 | 부채 구조 분석 |
| 현금및현금성자산 | 현금 팩터 계산 |
| 단기차입금 | 단기부채 계산 |
| 장기차입금 | 장기부채 계산 |

### 필드
| 백테스트 엔진 필드 | DB 컬럼명 | 설명 |
|------------------|----------|------|
| current_amount | thstrm_amount | 당기 금액 |

**✅ 연동 상태: 정상**

---

## 5. 팩터 계산에 사용되는 데이터

### 가치 팩터 (Value Factors)
```python
# PER = 시가총액 / 당기순이익
PER = StockPrice.market_cap / IncomeStatement['당기순이익']

# PBR = 시가총액 / 자본총계
PBR = StockPrice.market_cap / BalanceSheet['자본총계']
```

### 수익성 팩터 (Profitability Factors)
```python
# ROE = 당기순이익 / 자본총계 × 100
ROE = IncomeStatement['당기순이익'] / BalanceSheet['자본총계'] * 100

# ROA = 당기순이익 / 자산총계 × 100
ROA = IncomeStatement['당기순이익'] / BalanceSheet['자산총계'] * 100
```

### 성장성 팩터 (Growth Factors)
```python
# 매출 성장률 = (금분기 매출 - 전년동분기) / 전년동분기 × 100
revenue_growth = (current['매출액'] / past['매출액'] - 1) * 100

# 이익 성장률 = (금분기 순이익 - 전년동분기) / 전년동분기 × 100
earnings_growth = (current['당기순이익'] / past['당기순이익'] - 1) * 100
```

### 모멘텀 팩터 (Momentum Factors)
```python
# N개월 모멘텀 = (현재가 / N개월전 가격 - 1) × 100
momentum = (current_price / past_price - 1) * 100

# 사용 기간: 1M(20일), 3M(60일), 6M(120일), 12M(240일)
```

---

## 6. 데이터 조회 최적화

### 인덱스 활용
```python
# StockPrice 테이블 인덱스
- idx_stock_prices_date_company: (trade_date, company_id)
- idx_stock_prices_company_date_close: (company_id, trade_date, close_price)

# FinancialStatement 테이블 인덱스
- idx_financial_statements_company_year: (company_id, bsns_year)
- idx_financial_statements_reprt_code: (reprt_code)
```

### 조회 기간 확장
```python
# 주가 데이터: 백테스트 시작일 - 365일 (모멘텀 계산용)
extended_start = start_date - timedelta(days=365)

# 재무 데이터: 백테스트 시작일 - 180일 (분기 데이터 고려)
extended_start = start_date - timedelta(days=180)
```

---

## 7. 검증 체크리스트

### 필수 확인 사항
- [x] StockPrice.trade_date → 'date'로 레이블링
- [x] FinancialStatement.bsns_year → 'fiscal_year'로 레이블링
- [x] FinancialStatement.reprt_code → 'report_code'로 레이블링
- [x] Company JOIN을 통한 stock_code, company_name 조회
- [x] IncomeStatement, BalanceSheet JOIN 정상 동작
- [x] 계정과목명 필터링 (account_nm.in_([...]))
- [x] 날짜 필터링 (report_date >= start, report_date <= end)

### 데이터 품질 확인
- [ ] NULL 값 처리 (close_price.isnot(None), volume > 0)
- [ ] 중복 데이터 제거 (UniqueConstraint 활용)
- [ ] 이상치 처리 (Winsorize 적용)

---

## 8. 수정 이력

### 2025-01-09
- ✅ FinancialStatement 필드명 수정
  - `fiscal_year` → `bsns_year` (DB 스키마 준수)
  - `quarter` → `reprt_code` (보고서 코드로 분기 정보 표현)
- ✅ pivot_table index 수정 (fiscal_year, report_code 사용)
- ✅ DataFrame merge key 수정

---

## 9. 주의사항

### 계정과목명 다양성
- 재무제표 계정과목명이 기업마다 다를 수 있음
- 예: '매출액', '매출', '영업수익' 등 다양한 표현 존재
- 팩터 계산 시 여러 변형 포함하여 조회

### 재무 데이터 지연
- 재무제표는 보고서 제출일(report_date) 기준으로 사용
- 실제 결산일과 공시일 간 시차 존재
- 백테스트 시 Look-ahead bias 방지 필요

### TTM (Trailing Twelve Months) 계산
- 분기 데이터를 연환산하여 사용
- thstrm_add_amount (누적 금액) 활용 권장

---

## 10. 참고 문서
- [ERD_GUIDE.md](./ERD_GUIDE.md): 전체 데이터베이스 스키마
- [FACTOR_SHORTLIST.md](../FACTOR_SHORTLIST.md): 팩터 정의 및 계산 수식
- [backtest_genport_engine.py](../app/services/backtest_genport_engine.py): 백테스트 엔진 구현

---

## 연동 상태 요약

| 테이블 | 연동 상태 | 비고 |
|-------|---------|------|
| companies | ✅ 정상 | stock_code 매핑 정상 |
| stock_prices | ✅ 정상 | 주가 데이터 로드 정상 |
| financial_statements | ✅ 정상 | bsns_year, reprt_code 매핑 완료 |
| income_statements | ✅ 정상 | 계정과목 필터링 정상 |
| balance_sheets | ✅ 정상 | 계정과목 필터링 정상 |

**전체 연동 상태: ✅ 정상 (수정 완료)**
