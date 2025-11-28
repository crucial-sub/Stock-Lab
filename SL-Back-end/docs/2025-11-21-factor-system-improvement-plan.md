# 팩터 시스템 개선 계획 (대단위 작업)

**작성일**: 2025-11-21
**작업자**: AI Assistant
**목적**: 팩터 시스템의 장기적인 개선 및 유지보수 효율화

---

## 📋 완료된 작업 요약

### Phase 1: 긴급 팩터 추가 완료 (2025-11-21)

#### 추가된 팩터:
1. ✅ **PSR** (Price to Sales Ratio) - 시가총액 / 매출액
2. ✅ **CHANGE_RATE** (일별 변화율) - 전일 대비 주가 변화율
3. ✅ **OPERATING_INCOME_GROWTH** (영업이익 성장률)
4. ✅ **GROSS_PROFIT_GROWTH** (매출총이익 성장률)

#### 수정된 파일:
- `factor_calculator_complete.py`
  - Line 382-383: PSR 추가
  - Line 407-423: CHANGE_RATE 추가
  - Line 536-541: OPERATING_INCOME_GROWTH, GROSS_PROFIT_GROWTH 추가

- `backtest_extreme_optimized.py`
  - Line 487-496: PSR 추가
  - Line 14-37: 팩터 추가 프로세스 문서화

- `backtest_integration.py`
  - Line 188-193: 기본 팩터 세트에 새로운 팩터 추가

---

## 🎯 Phase 2: 추가 팩터 구현 (Priority 2 팩터들)

### 2.1 FCF_YIELD (잉여현금흐름 수익률)
**사용 전략**: warren_buffett, bill_ackman, glenn_greenberg, undervalued_dividend (4개)

**데이터 요구사항:**
- 영업활동현금흐름 (이미 있음)
- 투자활동현금흐름 (확인 필요)
- 시가총액 (이미 있음)

**계산 로직:**
```python
# FCF = 영업활동현금흐름 - 투자활동현금흐름
# FCF_YIELD = (FCF / 시가총액) × 100
fcf_yield = np.nan
operating_cf = row.get('영업활동현금흐름')
investing_cf = row.get('투자활동현금흐름')  # ← 데이터 확인 필요
market_cap = row.get('market_cap')
if operating_cf and investing_cf and market_cap and market_cap > 0:
    fcf = operating_cf - abs(investing_cf)
    fcf_yield = (fcf / market_cap) * 100
```

**추가 위치:**
- `factor_calculator_complete.py` → `_calculate_profitability_factors()` 메서드
- `backtest_extreme_optimized.py` → `_calculate_financial_factors_once()` 메서드

**예상 작업 시간:** 30분 (데이터 확인 포함)

---

### 2.2 DIVIDEND_YIELD (배당수익률)
**사용 전략**: peter_lynch, bill_ackman, undervalued_dividend, long_term_dividend (4개)

**데이터 요구사항:**
- 주당 배당금 (DB 스키마 확인 필요)
- 현재 주가 (이미 있음)

**계산 로직:**
```python
# DIVIDEND_YIELD = (주당 배당금 / 현재 주가) × 100
dividend_yield = np.nan
dividend_per_share = row.get('주당배당금')  # ← DB 스키마 확인 필요
current_price = row.get('close_price')
if dividend_per_share and current_price and current_price > 0:
    dividend_yield = (dividend_per_share / current_price) * 100
```

**주의사항:**
- DB에 배당금 데이터가 있는지 확인 필요
- 없으면 별도 데이터 수집 필요 (네이버 금융, KRX 등)

**추가 위치:**
- `factor_calculator_complete.py` → `_build_basic_factors()` 또는 별도 메서드
- `backtest_extreme_optimized.py` → `_calculate_financial_factors_once()` 메서드

**예상 작업 시간:** 1-2시간 (데이터 수집 포함 가능)

---

### 2.3 EV_EBITDA
**사용 전략**: glenn_welling (1개)

**데이터 요구사항:**
- 시가총액 (이미 있음)
- 부채총계 (이미 있음)
- 현금및현금성자산 (이미 있음)
- 영업이익 (이미 있음)
- 감가상각비 (확인 필요)

**계산 로직:**
```python
# EV = 시가총액 + 순부채 (부채총계 - 현금)
# EBITDA = 영업이익 + 감가상각비
# EV/EBITDA = EV / EBITDA
ev_ebitda = np.nan
market_cap = row.get('market_cap')
total_debt = row.get('부채총계')
cash = row.get('현금및현금성자산', 0)
operating_income = row.get('영업이익')
depreciation = row.get('감가상각비', 0)  # ← 데이터 확인 필요

if market_cap and total_debt and operating_income and operating_income > 0:
    ev = market_cap + total_debt - cash
    ebitda = operating_income + depreciation
    if ebitda > 0:
        ev_ebitda = ev / ebitda
```

**주의사항:**
- 감가상각비 데이터가 없으면 영업이익만으로 근사 계산
- EV/EBIT로 대체 가능

**추가 위치:**
- `factor_calculator_complete.py` → `_calculate_profitability_factors()` 메서드
- `backtest_extreme_optimized.py` → `_calculate_financial_factors_once()` 메서드

**예상 작업 시간:** 30-45분

---

## 🏗️ Phase 3: 아키텍처 리팩토링 (대단위 작업)

### 3.1 목표
현재 팩터 계산이 두 곳에서 이루어지고 있어 동기화 문제가 발생합니다:
- `factor_calculator_complete.py` (표준 경로 - 54개 팩터)
- `backtest_extreme_optimized.py` (최적화 경로 - 재무 팩터 8개)

**문제점:**
1. 새로운 팩터 추가 시 두 곳을 모두 수정해야 함
2. 동기화 누락 시 버그 발생 (DEBT_RATIO 사례)
3. 유지보수 비용 증가

### 3.2 해결 방안

#### Option A: 팩터 계산 로직 통합 (권장)
**아이디어:** 재무 팩터 계산을 단일 소스로 통합

```python
# factor_calculator_complete.py
class FactorCalculator:
    def _calculate_single_stock_financial_factors(
        self,
        stock_code: str,
        financial_row: dict,
        market_cap: float
    ) -> dict:
        """단일 종목의 재무 팩터 계산 (공통 로직)"""
        return {
            'PER': self._calc_per(market_cap, financial_row),
            'PBR': self._calc_pbr(market_cap, financial_row),
            'PSR': self._calc_psr(market_cap, financial_row),
            'ROE': self._calc_roe(financial_row),
            'ROA': self._calc_roa(financial_row),
            'DEBT_RATIO': self._calc_debt_ratio(financial_row),
            'OPERATING_MARGIN': self._calc_operating_margin(financial_row),
            'NET_MARGIN': self._calc_net_margin(financial_row),
        }

# backtest_extreme_optimized.py
class ExtremeOptimizer:
    def __init__(self, factor_calculator: FactorCalculator):
        self.factor_calculator = factor_calculator

    def _calculate_financial_factors_once(...):
        # 기존 데이터 준비 로직
        for stock_code in stock_codes:
            financial_factors[stock_code] = self.factor_calculator._calculate_single_stock_financial_factors(
                stock_code, financial_row, market_cap
            )
```

**장점:**
- ✅ 팩터 계산 로직 단일화
- ✅ 새로운 팩터 추가 시 한 곳만 수정
- ✅ 테스트 및 검증 용이

**단점:**
- ⚠️ 리팩토링 작업 필요 (2-3시간)
- ⚠️ 성능 영향 최소화 필요 (프로파일링 필요)

**예상 작업 시간:** 3-4시간

---

#### Option B: 자동화된 동기화 체크 (차선책)
**아이디어:** 단위 테스트로 두 경로의 팩터 목록 일치 검증

```python
# tests/test_factor_sync.py
import pytest
from app.services.factor_calculator_complete import CompleteFactorCalculator
from app.services.backtest_extreme_optimized import _calculate_financial_factors_once

def test_financial_factors_sync():
    """
    두 경로에서 계산되는 재무 팩터 목록이 일치하는지 검증
    """
    # factor_calculator_complete.py에서 계산되는 재무 팩터
    standard_factors = {
        'PER', 'PBR', 'PSR', 'ROE', 'ROA', 'DEBT_RATIO',
        'OPERATING_MARGIN', 'NET_MARGIN'
    }

    # backtest_extreme_optimized.py에서 계산되는 재무 팩터
    # (_calculate_financial_factors_once 반환 딕셔너리 키 추출)
    optimized_factors = set(_get_optimized_factor_keys())

    # 일치 검증
    missing_in_optimized = standard_factors - optimized_factors
    extra_in_optimized = optimized_factors - standard_factors

    assert not missing_in_optimized, f"최적화 경로에 누락된 팩터: {missing_in_optimized}"
    assert not extra_in_optimized, f"최적화 경로에 추가 팩터: {extra_in_optimized}"
```

**CI/CD 통합:**
```yaml
# .github/workflows/test.yml
- name: Run factor sync tests
  run: pytest tests/test_factor_sync.py
```

**장점:**
- ✅ 빠른 구현 (1시간)
- ✅ CI/CD 자동 검증
- ✅ 리팩토링 없음

**단점:**
- ❌ 근본적인 문제 해결 안 됨
- ❌ 여전히 두 곳 수정 필요

**예상 작업 시간:** 1-1.5시간

---

### 3.3 권장 작업 순서

#### Phase 3.1: 단기 (1주일 이내)
1. ✅ **Option B 구현** - 자동화된 동기화 체크
   - 단위 테스트 작성
   - CI/CD 통합
   - 기존 팩터 검증

#### Phase 3.2: 중기 (2-4주)
2. ⏳ **Option A 구현** - 팩터 계산 로직 통합
   - 리팩토링 계획 수립
   - 성능 프로파일링
   - 단계적 마이그레이션

#### Phase 3.3: 장기 (1-2개월)
3. ⏳ **추가 팩터 구현** (Priority 2)
   - FCF_YIELD
   - DIVIDEND_YIELD
   - EV_EBITDA

---

## 📊 데이터베이스 스키마 확인 작업

### 필요한 확인 사항:
1. **배당금 데이터:**
   - `financial_statements` 관련 테이블에 주당배당금 컬럼 있는지
   - 없으면 외부 데이터 소스 필요 (네이버 금융, KRX)

2. **현금흐름 데이터:**
   - `cashflow_statements` 테이블 구조
   - 투자활동현금흐름 컬럼 확인

3. **감가상각비 데이터:**
   - `income_statements` 또는 `cashflow_statements`에 포함 여부
   - 없으면 영업이익으로 근사 계산

### 확인 방법:
```sql
-- 재무제표 테이블 구조 확인
\d financial_statements
\d income_statements
\d balance_sheets
\d cashflow_statements

-- 배당금 데이터 확인
SELECT column_name
FROM information_schema.columns
WHERE table_name LIKE '%dividend%'
   OR column_name LIKE '%배당%';

-- 현금흐름 데이터 확인
SELECT account_nm
FROM cashflow_statements
WHERE account_nm LIKE '%투자%'
   OR account_nm LIKE '%현금%';
```

---

## 🎓 팩터 추가 표준 프로세스 (정립 완료)

### Step 1: 팩터 분석
1. 어떤 전략에서 사용하는가?
2. 계산에 필요한 데이터는 무엇인가?
3. DB에 데이터가 있는가?

### Step 2: 표준 경로 구현
1. `factor_calculator_complete.py` 수정
   - 적절한 메서드 선택 (`_build_basic_factors()`, `_calculate_growth_factors()` 등)
   - 계산 로직 추가
   - 주석으로 계산 공식 명시

### Step 3: 최적화 경로 구현
1. `backtest_extreme_optimized.py` 수정
   - `_calculate_financial_factors_once()` 메서드
   - 반환 딕셔너리에 팩터 추가
   - 주석으로 계산 공식 명시

### Step 4: 기본 팩터 세트 업데이트
1. `backtest_integration.py` 수정
   - `required_factors` 세트에 추가

### Step 5: 검증
1. Docker 재시작
2. 백테스트 실행
3. 로그 확인하여 팩터 정상 계산 검증
4. 전략별 테스트

---

## 📝 다음 단계

### 즉시 수행 가능:
- ✅ 코드 문서화 완료
- ✅ Docker 재시작 완료
- ⏳ 백테스트 실행 및 검증 (사용자 테스트 대기 중)

### 단기 작업 (1주일):
- [ ] 자동화된 동기화 체크 구현 (Option B)
- [ ] 데이터베이스 스키마 확인
- [ ] Priority 2 팩터 중 FCF_YIELD 추가

### 중기 작업 (2-4주):
- [ ] 팩터 계산 로직 통합 (Option A)
- [ ] Priority 2 팩터 모두 추가 (DIVIDEND_YIELD, EV_EBITDA)

### 장기 작업 (1-2개월):
- [ ] 팩터 시스템 리팩토링 완료
- [ ] 통합 테스트 구축
- [ ] 성능 최적화 및 프로파일링

---

## 🔑 핵심 교훈

1. **두 경로 동기화의 중요성:**
   - 성능 최적화를 위한 코드 분리는 유지보수 비용 증가
   - 자동화된 검증 시스템 필요

2. **단계적 개선:**
   - 긴급 → 단기 → 중기 → 장기
   - 각 단계마다 검증 및 테스트

3. **문서화의 가치:**
   - 코드 주석으로 미래의 개발자에게 경고
   - 상세한 작업 계획으로 우선순위 명확화

---

**작업 완료!** 🎉

팩터 시스템 개선을 위한 종합 계획이 수립되었습니다.
