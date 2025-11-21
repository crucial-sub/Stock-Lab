# 유명 전략 팩터 누락 분석 및 추가 계획

**작성일**: 2025-11-21
**작업자**: AI Assistant
**목적**: migrate_strategies.py의 모든 유명 전략에서 사용하는 팩터를 분석하고 누락된 팩터 추가

---

## 📋 전략별 사용 팩터 분석

### 1. surge_stocks (급등주 전략)
**사용 팩터:**
- MARKET_CAP (시가총액) ✅
- CHANGE_RATE (일별 변화율) ❌ **누락**

### 2. steady_growth (안정적 성장 전략)
**사용 팩터:**
- REVENUE_GROWTH_3Y (매출 성장률 3년) ✅ factor_calculator_complete.py에 있음
- OPERATING_INCOME_GROWTH (영업이익 성장률) ❌ **누락**
- DEBT_RATIO (부채비율) ✅
- ROE (자기자본이익률) ✅

### 3. benjamin_graham (벤저민 그레이엄 전략)
**사용 팩터:**
- CURRENT_RATIO (유동비율) ✅ factor_calculator_complete.py에 있음 (stability_factors)
- PER (주가수익비율) ✅
- PBR (주가순자산비율) ✅

### 4. peter_lynch (피터 린치 전략)
**사용 팩터:**
- PER ✅
- DEBT_RATIO ✅
- ROE ✅
- ROA ✅
- DIVIDEND_YIELD (배당수익률) ❌ **누락**

### 5. warren_buffett (워렌 버핏 전략)
**사용 팩터:**
- ROE ✅
- CURRENT_RATIO ✅ factor_calculator_complete.py에 있음
- FCF_YIELD (잉여현금흐름 수익률) ❌ **누락**
- PER ✅
- PBR ✅
- DEBT_RATIO ✅
- EARNINGS_GROWTH (순이익 성장률) ✅ factor_calculator_complete.py에 EARNINGS_GROWTH_1Y로 있음

### 6. william_oneil (윌리엄 오닐 전략)
**사용 팩터:**
- EARNINGS_GROWTH ✅ factor_calculator_complete.py에 EARNINGS_GROWTH_1Y로 있음
- ROE ✅

### 7. bill_ackman (빌 애크만 전략)
**사용 팩터:**
- PER ✅
- PBR ✅
- DEBT_RATIO ✅
- FCF_YIELD ❌ **누락**
- DIVIDEND_YIELD ❌ **누락**

### 8. charlie_munger (찰리 멍거 전략)
**사용 팩터:**
- PER ✅
- PBR ✅
- ROE ✅
- REVENUE_GROWTH (매출 성장률) ✅ factor_calculator_complete.py에 REVENUE_GROWTH_1Y로 있음
- DEBT_RATIO ✅
- CURRENT_RATIO ✅ factor_calculator_complete.py에 있음

### 9. glenn_welling (글렌 웰링 전략)
**사용 팩터:**
- EV_EBITDA ❌ **누락**
- PBR ✅
- PSR (Price to Sales Ratio) ❌ **누락**

### 10. cathie_wood (캐시 우드 전략)
**사용 팩터:**
- PSR ❌ **누락**
- REVENUE_GROWTH ✅ factor_calculator_complete.py에 REVENUE_GROWTH_1Y로 있음
- CURRENT_RATIO ✅ factor_calculator_complete.py에 있음

### 11. glenn_greenberg (글렌 그린버그 전략)
**사용 팩터:**
- PER ✅
- DEBT_RATIO ✅
- GROSS_PROFIT_GROWTH (매출총이익 성장률) ❌ **누락**
- FCF_YIELD ❌ **누락**

### 12. undervalued_dividend (저평가 배당 전략)
**사용 팩터:**
- FCF_YIELD ❌ **누락**
- EARNINGS_GROWTH ✅ factor_calculator_complete.py에 EARNINGS_GROWTH_1Y로 있음
- PBR ✅
- PER ✅
- DIVIDEND_YIELD (우선 순위 팩터) ❌ **누락**

### 13. long_term_dividend (장기 배당 전략)
**사용 팩터:**
- DIVIDEND_YIELD ❌ **누락**
- PER ✅
- PBR ✅
- DEBT_RATIO ✅
- OPERATING_INCOME_GROWTH ❌ **누락**

---

## 🔍 현재 팩터 계산 상태

### factor_calculator_complete.py (표준 경로)
**기본 팩터 (9개)**: PER, PBR, ROE, ROA, DEBT_RATIO, AVG_TRADING_VALUE, TURNOVER_RATE, MOM_3M, VOLATILITY_90

**수익성 팩터 (6개)**: GPM, OPM, NPM, ASSET_TURNOVER, EQUITY_MULTIPLIER, OCF_RATIO

**성장성 팩터 (8개)**: REVENUE_GROWTH_1Y, EARNINGS_GROWTH_1Y, ASSET_GROWTH_1Y, EQUITY_GROWTH_1Y, REVENUE_GROWTH_3Y, EARNINGS_GROWTH_3Y

**안정성 팩터 (8개)**: CURRENT_RATIO, QUICK_RATIO, DEBT_TO_EQUITY, INTEREST_COVERAGE, CASH_RATIO, WORKING_CAPITAL_RATIO, EQUITY_RATIO, ALTMAN_Z_SCORE

**기술적 팩터 (6개)**: RSI_14, BOLLINGER_POSITION, STOCHASTIC_14, VOLUME_ROC, PRICE_TO_MA_20, MACD_SIGNAL

**품질 팩터 (5개)**: (상세 내역은 코드 참조)

### backtest_extreme_optimized.py (최적화 경로)
**재무 팩터 (7개)**: PER, PBR, ROE, ROA, DEBT_RATIO, OPERATING_MARGIN, NET_MARGIN

---

## ❌ 누락된 팩터 목록

### 1. CHANGE_RATE (일별 변화율)
**설명**: 전일 대비 주가 변화율
**전략**: surge_stocks (급등주)
**카테고리**: 기술적 지표
**추가 위치**: factor_calculator_complete.py (`_build_basic_factors()` 또는 `_calculate_advanced_momentum()`)

### 2. OPERATING_INCOME_GROWTH (영업이익 성장률)
**설명**: 전년 대비 영업이익 성장률
**전략**: steady_growth, long_term_dividend
**카테고리**: 성장성 팩터
**추가 위치**:
- factor_calculator_complete.py (`_calculate_growth_factors()`)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

### 3. DIVIDEND_YIELD (배당수익률)
**설명**: 주당 배당금 / 주가 × 100
**전략**: peter_lynch, bill_ackman, undervalued_dividend, long_term_dividend
**카테고리**: 재무 팩터 (가치 지표)
**추가 위치**:
- factor_calculator_complete.py (`_build_basic_factors()` 또는 별도 메서드)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

### 4. FCF_YIELD (잉여현금흐름 수익률)
**설명**: 잉여현금흐름 / 시가총액 × 100
**전략**: warren_buffett, bill_ackman, glenn_greenberg, undervalued_dividend
**카테고리**: 재무 팩터 (현금흐름 지표)
**추가 위치**:
- factor_calculator_complete.py (`_calculate_profitability_factors()` 또는 별도 메서드)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

### 5. EV_EBITDA
**설명**: Enterprise Value / EBITDA
**전략**: glenn_welling
**카테고리**: 재무 팩터 (가치 지표)
**추가 위치**:
- factor_calculator_complete.py (별도 메서드 또는 `_calculate_profitability_factors()`)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

### 6. PSR (Price to Sales Ratio)
**설명**: 시가총액 / 매출액
**전략**: glenn_welling, cathie_wood
**카테고리**: 재무 팩터 (가치 지표)
**추가 위치**:
- factor_calculator_complete.py (`_build_basic_factors()`)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

### 7. GROSS_PROFIT_GROWTH (매출총이익 성장률)
**설명**: 전년 대비 매출총이익 성장률
**전략**: glenn_greenberg
**카테고리**: 성장성 팩터
**추가 위치**:
- factor_calculator_complete.py (`_calculate_growth_factors()`)
- backtest_extreme_optimized.py (`_calculate_financial_factors_once()`)

---

## 🎯 추가 작업 우선순위

### Priority 1: 핵심 재무 팩터 (여러 전략에서 사용)
1. **DIVIDEND_YIELD** - 4개 전략에서 사용
2. **FCF_YIELD** - 4개 전략에서 사용
3. **OPERATING_INCOME_GROWTH** - 2개 전략에서 사용
4. **PSR** - 2개 전략에서 사용

### Priority 2: 특화 팩터
5. **EV_EBITDA** - 1개 전략 (glenn_welling)
6. **GROSS_PROFIT_GROWTH** - 1개 전략 (glenn_greenberg)
7. **CHANGE_RATE** - 1개 전략 (surge_stocks)

---

## 📝 작업 계획

### Phase 1: factor_calculator_complete.py 수정
1. `_build_basic_factors()` 메서드에 추가:
   - DIVIDEND_YIELD
   - PSR
   - CHANGE_RATE

2. `_calculate_growth_factors()` 메서드에 추가:
   - OPERATING_INCOME_GROWTH
   - GROSS_PROFIT_GROWTH

3. 새로운 메서드 또는 기존 메서드 확장:
   - FCF_YIELD → `_calculate_profitability_factors()`
   - EV_EBITDA → `_calculate_profitability_factors()`

### Phase 2: backtest_extreme_optimized.py 수정
`_calculate_financial_factors_once()` 메서드에 추가:
- DIVIDEND_YIELD
- FCF_YIELD
- PSR
- EV_EBITDA
- OPERATING_INCOME_GROWTH
- GROSS_PROFIT_GROWTH

### Phase 3: backtest_integration.py 기본 팩터 세트 업데이트
`required_factors` 세트에 새로운 팩터 추가

### Phase 4: 검증
1. Docker 재시작
2. 각 전략별 백테스트 실행 테스트
3. 로그 확인하여 팩터 정상 계산 검증

---

## 📊 예상 팩터 계산 로직

### DIVIDEND_YIELD (배당수익률)
```python
# 주당 배당금 데이터 필요 (재무 데이터 또는 별도 테이블)
# DIVIDEND_YIELD = (주당 배당금 / 현재 주가) × 100
dividend_yield = np.nan
dividend_per_share = row.get('주당배당금')  # 필요 시 DB 스키마 확인
current_price = row.get('close_price')
if dividend_per_share and current_price and current_price > 0:
    dividend_yield = (dividend_per_share / current_price) * 100
```

### FCF_YIELD (잉여현금흐름 수익률)
```python
# FCF_YIELD = (영업활동현금흐름 - 투자활동현금흐름) / 시가총액 × 100
fcf_yield = np.nan
operating_cf = row.get('영업활동현금흐름')
investing_cf = row.get('투자활동현금흐름')
market_cap = row.get('market_cap')
if operating_cf and investing_cf and market_cap and market_cap > 0:
    fcf = operating_cf - abs(investing_cf)
    fcf_yield = (fcf / market_cap) * 100
```

### PSR (Price to Sales Ratio)
```python
# PSR = 시가총액 / 매출액
psr = np.nan
market_cap = row.get('market_cap')
revenue = row.get('매출액')
if market_cap and revenue and revenue > 0:
    psr = market_cap / revenue
```

### EV_EBITDA
```python
# EV = 시가총액 + 순부채 (부채총계 - 현금및현금성자산)
# EBITDA = 영업이익 + 감가상각비 (감가상각비 데이터 확인 필요)
ev_ebitda = np.nan
market_cap = row.get('market_cap')
total_debt = row.get('부채총계')
cash = row.get('현금및현금성자산', 0)
operating_income = row.get('영업이익')
# 감가상각비 데이터가 없으면 영업이익으로 대체
if market_cap and total_debt and operating_income and operating_income > 0:
    ev = market_cap + total_debt - cash
    ebitda = operating_income  # 실제로는 + 감가상각비
    ev_ebitda = ev / ebitda
```

### OPERATING_INCOME_GROWTH
```python
# 전년 대비 영업이익 성장률
operating_income_growth = np.nan
current_oi = latest.get('영업이익')
previous_oi = previous.get('영업이익')
if current_oi and previous_oi and previous_oi > 0:
    operating_income_growth = ((current_oi - previous_oi) / previous_oi) * 100
```

### GROSS_PROFIT_GROWTH
```python
# 전년 대비 매출총이익 성장률
# 매출총이익 = 매출액 - 매출원가
gross_profit_growth = np.nan
current_revenue = latest.get('매출액')
current_cogs = latest.get('매출원가', 0)
previous_revenue = previous.get('매출액')
previous_cogs = previous.get('매출원가', 0)
if current_revenue and previous_revenue:
    current_gp = current_revenue - current_cogs
    previous_gp = previous_revenue - previous_cogs
    if previous_gp > 0:
        gross_profit_growth = ((current_gp - previous_gp) / previous_gp) * 100
```

### CHANGE_RATE (일별 변화율)
```python
# 전일 대비 주가 변화율
change_rate = np.nan
if len(stock_prices) >= 2:
    current_price = stock_prices.iloc[-1]['close_price']
    previous_price = stock_prices.iloc[-2]['close_price']
    if previous_price > 0:
        change_rate = ((current_price - previous_price) / previous_price) * 100
```

---

## ⚠️ 주의사항

### 1. 데이터베이스 스키마 확인 필요
- **주당배당금** 데이터가 재무 데이터 테이블에 있는지 확인
- **감가상각비** 데이터가 있는지 확인 (EV/EBITDA 계산용)
- 없는 경우 대체 로직 또는 근사 계산 방법 사용

### 2. 팩터 이름 매핑
- migrate_strategies.py에서 사용하는 이름: `EARNINGS_GROWTH`
- factor_calculator_complete.py의 이름: `EARNINGS_GROWTH_1Y`
- **해결 방법**: 두 가지 옵션
  1. factor_calculator에서 alias 추가: `EARNINGS_GROWTH = EARNINGS_GROWTH_1Y`
  2. migrate_strategies.py에서 팩터명 수정

### 3. 동기화 유지
- 새로운 팩터를 추가할 때 **반드시 두 곳에 추가**:
  1. `factor_calculator_complete.py` (표준 경로)
  2. `backtest_extreme_optimized.py` (최적화 경로)

---

## 📅 다음 단계

1. ✅ 누락된 팩터 목록 작성 및 우선순위 결정
2. ⏳ factor_calculator_complete.py에 팩터 계산 로직 추가
3. ⏳ backtest_extreme_optimized.py에 팩터 계산 로직 추가
4. ⏳ backtest_integration.py 기본 팩터 세트 업데이트
5. ⏳ Docker 재시작 및 검증
6. ⏳ 각 전략별 백테스트 테스트
