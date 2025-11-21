# 팩터 시스템 인수인계 체크리스트

**작성일**: 2025-11-21
**작성자**: AI Assistant
**인수자**: 백엔드 팀원

---

## 🎬 배경 스토리: 이 모든 것의 시작

### DEBT_RATIO 계산 문제
2025-11-21, 사용자가 백테스트에서 "부채비율 < 200" 조건을 선택했을 때 **매수 거래가 0건** 발생하는 문제를 보고했습니다. PER, PBR 등 다른 재무 팩터는 정상 작동했지만 DEBT_RATIO만 계산되지 않았습니다.

### 근본 원인 발견
여러 차례 로그 디버깅을 시도했지만 실패했고, 결국 **전체 코드 플로우를 처음부터 추적**하여 근본 원인을 발견했습니다:

**Dual-Path 아키텍처:**
- **표준 경로**: `factor_calculator_complete.py` (54개 팩터 구현됨)
- **최적화 경로**: `backtest_extreme_optimized.py` (재무 팩터 8개만 구현)
- 백테스트는 성능을 위해 **항상 최적화 경로를 사용**
- DEBT_RATIO는 표준 경로에만 있고 **최적화 경로에는 없었음** → 버그 발생

### 전체 팩터 시스템 점검
이 문제를 계기로 `migrate_strategies.py`의 모든 유명 전략(13개)에서 사용하는 팩터를 전수 조사했고, **7개의 누락된 팩터**를 발견했습니다.

**이 인수인계 문서는 그 과정에서 발견된 문제들과 해결 방안을 정리한 것입니다.**

---

## 📚 작업 시작 전 필수 문서

작업을 시작하기 전에 다음 3개 문서를 **반드시 순서대로** 읽어주세요. 전체 맥락을 이해하는 것이 매우 중요합니다.

### 1. `2025-11-21-debt-ratio-root-cause-fix.md` (필독!)
**내용**: DEBT_RATIO 버그 발견 및 수정 과정
**왜 읽어야 하나요?**
- Dual-Path 아키텍처의 존재를 이해
- 왜 동기화가 중요한지 실제 사례로 이해
- 문제 해결 접근법 학습 (로그 디버깅 → 전체 플로우 추적)

### 2. `2025-11-21-missing-factors-analysis.md` (필독!)
**내용**: 13개 유명 전략의 팩터 전수 조사 결과
**왜 읽어야 하나요?**
- 누락된 7개 팩터 목록과 우선순위 파악
- 각 팩터가 어떤 전략에서 사용되는지 이해
- 팩터별 계산 로직과 데이터 요구사항 확인

### 3. `2025-11-21-factor-system-improvement-plan.md` (필독!)
**내용**: 팩터 시스템 전체 개선 계획 (Phase 1, 2, 3)
**왜 읽어야 하나요?**
- Phase 1에서 무엇을 완료했는지 확인
- Phase 2 작업 범위와 예상 시간 파악
- Phase 3 아키텍처 리팩토링 옵션 이해 (현재는 보류)

**이 3개 문서를 읽은 후 이 체크리스트로 돌아와서 작업을 진행하세요!**

---

## 📋 완료된 작업 요약

### ✅ Phase 1: 긴급 팩터 추가 (부분 완료)

#### 🚨 중요! Phase 1 실제 완료 상태

**당초 계획**: 8개 팩터를 표준 경로와 최적화 경로에 모두 추가
**실제 결과**: 표준 경로에만 추가되어 있었고, 최적화 경로는 PSR 하나만 추가됨

**2025-11-21 긴급 버그 발견**:
- 사용자가 OPERATING_INCOME_GROWTH >= 3 조건으로 백테스트 실행
- 결과: **매수 0건** (조건이 전혀 작동하지 않음)
- 원인: DEBT_RATIO와 동일한 문제 - 최적화 경로에 팩터가 없었음
- 문서에는 "완료"라고 적혀있었지만 실제로는 작동 안 함!

**긴급 수정 (2025-11-21 오후)**:
- 4개 성장률 팩터(1Y)를 최적화 경로에 추가
- 데이터 조회 로직 수정 (1년치 → 2년치 재무 데이터 조회)
- 성장률 계산 로직 구현 ((현재 - 이전) / 이전 * 100)
- Docker 재시작 후 사용자 확인: "이제 조건 잘 먹힌다!"

---

#### ✅ 최적화 경로에 실제로 추가된 팩터 (5개):
1. **PSR** (Price to Sales Ratio) - 시가총액 / 매출액
   - ✅ 최적화 경로 추가 완료
2. **OPERATING_INCOME_GROWTH** (영업이익 성장률)
   - ❌ 표준 경로에만 있었음 (백테스트 시 작동 안 함)
   - ✅ **[긴급 수정]** 최적화 경로에 추가 완료
3. **GROSS_PROFIT_GROWTH** (매출총이익 성장률)
   - ❌ 표준 경로에만 있었음 (백테스트 시 작동 안 함)
   - ✅ **[긴급 수정]** 최적화 경로에 추가 완료
4. **REVENUE_GROWTH_1Y** (1년 매출 성장률)
   - ❌ 표준 경로에만 있었음 (백테스트 시 작동 안 함)
   - ✅ **[긴급 수정]** 최적화 경로에 추가 완료
5. **EARNINGS_GROWTH_1Y** (1년 순이익 성장률)
   - ❌ 표준 경로에만 있었음 (백테스트 시 작동 안 함)
   - ✅ **[긴급 수정]** 최적화 경로에 추가 완료

#### ⚠️ 표준 경로에만 있는 팩터 (백테스트 시 작동 불가 - 재검토 필요):
6. **CHANGE_RATE** (일별 변화율)
   - 주가 데이터 필요, 재무 팩터 함수에서 계산 불가능
   - 최적화 경로 추가 불가 (기술적 제약)
7. **REVENUE_GROWTH_3Y** (3년 복합 매출 성장률)
   - 3년치 재무 데이터 필요, 현재 1년치만 조회
   - 구현 복잡도 높음, 긴급 수정 범위 제외
8. **EARNINGS_GROWTH_3Y** (3년 복합 순이익 성장률)
   - 3년치 재무 데이터 필요, 현재 1년치만 조회
   - 구현 복잡도 높음, 긴급 수정 범위 제외

**⚠️ 경고**: 위 3개 팩터는 프론트엔드 팩터 목록에 표시되지만 백테스트에서 실제로 작동하지 않습니다!
**→ Phase 2-A에서 반드시 전수 조사 및 수정/제거 필요**

#### 수정된 파일:

**1. factor_calculator_complete.py** (표준 경로)
- ✅ PSR 추가 (Line 382-383)
- ✅ CHANGE_RATE 추가 (Line 407-435)
- ✅ OPERATING_INCOME_GROWTH 추가 (Line 536-537)
- ✅ GROSS_PROFIT_GROWTH 추가 (Line 538-541)
- ✅ REVENUE_GROWTH_3Y 이미 구현됨 (Line 548)
- ✅ EARNINGS_GROWTH_3Y 이미 구현됨 (Line 553)

**2. backtest_extreme_optimized.py** (최적화 경로) **[2025-11-21 긴급 수정 완료]**

**긴급 수정 내역 (2025-11-21 오후)**:
- ✅ PSR 추가 (Line 544-548) - 기존 완료
- ✅ **데이터 조회 로직 수정** (Line 457-464)
  - 변경 전: `limit(1)` - 최신 1년치 재무 데이터만 조회
  - 변경 후: `limit(2)` - 최신 2년치 재무 데이터 조회 (성장률 계산용)
  - 이전 연도 데이터 저장: `previous_row`
- ✅ **4개 성장률 팩터 계산 로직 추가** (Line 500-525)
  - OPERATING_INCOME_GROWTH: `(현재 영업이익 - 이전 영업이익) / 이전 영업이익 * 100`
  - GROSS_PROFIT_GROWTH: `(현재 매출총이익 - 이전 매출총이익) / 이전 매출총이익 * 100`
  - REVENUE_GROWTH_1Y: `(현재 매출 - 이전 매출) / 이전 매출 * 100`
  - EARNINGS_GROWTH_1Y: `(현재 순이익 - 이전 순이익) / 이전 순이익 * 100`
- ✅ **반환 딕셔너리 업데이트** (Line 550-564)
  - 4개 성장률 팩터를 딕셔너리에 추가
  - 백테스트 엔진이 이 팩터들을 사용할 수 있게 됨

**미구현 (긴급 수정 범위 제외)**:
- ❌ REVENUE_GROWTH_3Y, EARNINGS_GROWTH_3Y
  - 이유: 3년치 데이터 필요 (현재는 2년치만 조회)
  - 구현 시 데이터 조회량 1.5배 증가 → 성능 영향
- ❌ CHANGE_RATE
  - 이유: 주가 데이터 필요 (재무 팩터 함수에서 불가능)
  - 기술적 제약으로 최적화 경로 추가 불가

**3. backtest_integration.py** (통합 레이어)
- ✅ 기본 팩터 세트 업데이트 (Line 187-196)
- 추가된 팩터: OPERATING_MARGIN, NET_MARGIN, CHANGE_RATE, OPERATING_INCOME_GROWTH, GROSS_PROFIT_GROWTH, REVENUE_GROWTH_1Y, REVENUE_GROWTH_3Y, EARNINGS_GROWTH_1Y, EARNINGS_GROWTH_3Y

**4. backtest.py** (백테스트 엔진)
- ✅ 기본 팩터 세트 업데이트 (Line 1341-1349)
- 통합 레이어와 동일한 팩터 추가

**5. 프론트엔드: axios.ts**
- ✅ 타임아웃 30초 → 3분(180000ms)으로 증가
- 백테스트는 1-2분 소요될 수 있음

**6. 디버깅 로그 정리**
- ✅ factor_integration.py (11개 로그 제거)
- ✅ condition_evaluator.py (3개 로그 제거)
- ✅ condition_evaluator_vectorized.py (7개 로그 제거)
- ✅ backtest.py (6개 로그 제거)
- ✅ advanced_backtest.py (3개 로그 제거)
- **총 30개의 디버깅 로그 제거 완료**

---

## 🎯 Phase 2: 팩터 시스템 검증 및 추가 구현 (인수인계 대상)

### 🎯 Phase 2 전체 목표

**1차 목표**: `scripts/migrate_strategies.py`에 있는 유명 전략들(13개)에 사용되는 **모든 조건식 및 팩터를 계산 가능하도록** 하는 것

**단, 다음 경우는 예외 처리**:
- ❌ **계산 비용이 너무 큰 팩터**: 구현 시 성능 저하가 심각한 경우 제외
  - 예: 3년치 재무 데이터 필요 (데이터 조회량 1.5배 증가)
  - 예: 복잡한 데이터 조인이나 계산이 필요한 팩터
- ❌ **백테스트 속도에 악영향을 주는 팩터**: 실시간 계산 시 병목이 되는 경우
  - 예: 매 주가 데이터마다 계산해야 하는 무거운 기술적 지표
- ✅ **대안 고려**: 계산이 쉽지만 유사한 팩터로 교체
  - 예: REVENUE_GROWTH_3Y (3년) → REVENUE_GROWTH_1Y (1년)
  - 예: EV/EBITDA → EV/EBIT (감가상각비 없이 근사 계산)

**판단 기준**:
1. 사용 빈도: 4개 이상 전략에서 사용 → 우선 구현
2. 계산 복잡도: 간단 → 구현, 복잡 → 대안 검토
3. 성능 영향: 백테스트 시간 10% 이상 증가 → 제외 고려
4. 데이터 가용성: DB에 데이터 있음 → 구현, 없음 → 제외

---

### 🚨 Phase 2-A: 팩터 시스템 전수 조사 및 검증 (최우선 필수!)

**배경**:
- 2025-11-21 오후, 사용자가 OPERATING_INCOME_GROWTH >= 3 조건으로 백테스트 실행
- 결과: **매수 0건** (조건이 전혀 작동하지 않음)
- 문서에는 "완료"라고 적혀있었지만 실제로는 최적화 경로에 팩터가 없었음
- **사용자의 핵심 발견**: "많은 팩터들이 실제로 계산되는지 의심됨"

**심각한 문제점**:
1. **프론트엔드 팩터 목록 신뢰성 문제**:
   - 팩터 선택 모달에 표시되는 목록이 서버에서 제공됨
   - 사용자는 이 목록을 보고 "이 팩터들을 사용할 수 있다"고 믿음
   - **하지만 실제로 계산되는지 검증 안 됨** → 사용자를 속이는 것!
   - OPERATING_INCOME_GROWTH, CHANGE_RATE 등 여러 팩터가 작동 안 함
2. **문서와 실제의 괴리**:
   - Phase 1 "완료"라고 적혀있었지만 5개 팩터가 작동 안 함
   - 표준 경로에만 추가하고 최적화 경로는 빠뜨림
   - 코드 리뷰만으로는 발견 못 함 (실제 실행해봐야 알 수 있음)
3. **팩터 분류 혼란**:
   - 현재 분류가 체계적이지 않음
   - 사용자가 원하는 팩터를 찾기 어려움

**작업 내용**:

#### 2-A.1 프론트엔드 팩터 목록 API 확인
- 어떤 API 엔드포인트에서 팩터 목록을 제공하는지 확인
- 팩터 목록이 어디서 생성되는지 추적 (백엔드 코드)

#### 2-A.2 각 팩터의 계산 여부 전수 조사

**매우 중요!** 코드만 보지 말고 **반드시 실제 백테스트로 테스트**하세요!

**테스트 방법**:
1. 프론트엔드 팩터 목록에서 팩터 하나만 선택
2. 조건 설정 (예: `OPERATING_INCOME_GROWTH >= 3`)
3. 백테스트 실행
4. 결과 확인:
   - ✅ 매수 거래가 발생하면 → 정상 작동
   - ❌ 매수 0건이면 → 팩터가 계산 안 되는 것 (버그!)

**각 팩터에 대해 다음 4가지 모두 확인**:
- [ ] `factor_calculator_complete.py` (표준 경로)에 구현되어 있는가?
- [ ] `backtest_extreme_optimized.py` (최적화 경로)에 구현되어 있는가?
  - 재무 팩터인 경우 필수!
  - 성장률, 기술적 팩터는 표준 경로만 있어도 됨
- [ ] 기본 팩터 세트에 포함되어 있는가?
  - `backtest_integration.py` Line 187-196
  - `backtest.py` Line 1341-1349
  - **두 파일 모두 확인!** (한 곳만 있으면 특정 전략에서 버그 발생)
- [ ] **실제 백테스트 실행 시 정상 작동하는가?** (가장 중요!)
  - 위 3개 체크가 다 완료되어도 실제로 작동 안 할 수 있음
  - **반드시 실제 백테스트로 테스트할 것!**

**예상 버그 케이스** (반드시 확인):
- CHANGE_RATE: 최적화 경로에 추가 불가능 (주가 데이터 필요)
- REVENUE_GROWTH_3Y, EARNINGS_GROWTH_3Y: 최적화 경로에 미구현 (3년치 데이터 필요)
- 기타 표준 경로에만 있는 재무 팩터들

#### 2-A.3 작동 안 하는 팩터 수정 또는 제거

**수정 vs 제거 vs 대체 판단 기준**:

1. **수정 우선** (Dual-Path에 추가):
   - 4개 이상 전략에서 사용
   - 계산 복잡도 낮음 (기존 데이터로 간단히 계산 가능)
   - 성능 영향 미미 (백테스트 시간 5% 이내 증가)
   - 예: OPERATING_INCOME_GROWTH, GROSS_PROFIT_GROWTH (긴급 수정 완료)

2. **대체 고려** (유사하지만 계산이 쉬운 팩터로 교체):
   - 중요한 팩터지만 계산 비용이 큰 경우
   - 예: REVENUE_GROWTH_3Y → REVENUE_GROWTH_1Y
   - 예: EV/EBITDA → EV/EBIT (감가상각비 없이 근사)
   - **장점**: 전략의 본질은 유지하면서 성능 개선

3. **제거 고려** (프론트엔드 목록에서 삭제):
   - 사용 빈도 낮음 (1-2개 전략만 사용)
   - 구현 복잡도 높음 (3년치 데이터, 복잡한 조인 필요)
   - 성능 영향 큼 (백테스트 시간 10% 이상 증가)
   - 대체 불가능 (유사한 팩터도 없음)
   - 예: REVENUE_GROWTH_3Y, EARNINGS_GROWTH_3Y (3년치 데이터 필요)

4. **프론트엔드 동기화 필수**:
   - 제거된 팩터는 API 응답에서 제외
   - 대체된 팩터는 새 팩터명으로 업데이트
   - 사용자에게 명확한 팩터 설명 제공

5. **🚨 전략 동기화 필수 (매우 중요!)**:
   - 팩터를 제거하거나 대체했으면 **해당 팩터를 사용하는 모든 전략을 수정**해야 함
   - **반드시 수정해야 할 곳**:
     - ✅ `migrate_strategies.py`: 전략 정의에서 팩터 제거/대체
     - ✅ DB 업데이트: `python scripts/migrate_strategies.py` 실행
     - ✅ 프론트엔드: 전략 설명 UI 업데이트 (필요 시)
   - **왜 중요한가?**:
     - 팩터 제거했는데 전략에서 계속 사용하면 → 백테스트 실패!
     - 전략과 팩터 구현이 align 안 맞으면 → 디버깅에 한세월!
   - **전략 사용 플로우**:
     ```
     migrate_strategies.py 수정
     ↓
     python scripts/migrate_strategies.py 실행
     ↓
     DB investment_strategies 테이블 업데이트
     ↓
     추후 전략 사용 시 DB에서 로드
     ```

**작업 결과물**:
- 📋 작동 안 하는 팩터 목록 (원인, 판단, 조치 방안)
- 📋 대체 팩터 매핑 테이블 (구 팩터 → 신 팩터)
- 📋 제거 팩터 목록 (이유 포함)
- 📋 **수정된 전략 목록** (어떤 전략에서 어떤 팩터를 제거/대체했는지)

#### 2-A.4 팩터 분류 체계 정리
- 현재 분류가 개판이라면 다음 카테고리로 재분류:
  - **가치 지표**: PER, PBR, PSR, PCR, PEG 등
  - **재무 건전성**: DEBT_RATIO, CURRENT_RATIO, QUICK_RATIO 등
  - **수익성**: ROE, ROA, GPM, OPM, NPM 등
  - **성장성**: REVENUE_GROWTH, EARNINGS_GROWTH 등
  - **현금흐름**: FCF_YIELD, OCF_RATIO 등
  - **기술적 지표**: RSI, MACD, BOLLINGER 등
  - **모멘텀**: MOMENTUM_1M, MOMENTUM_3M 등

**예상 작업 시간**: 2-3시간 (매우 중요!)

**우선순위**: 🔴 **최우선** - Phase 2-B보다 먼저 수행!

---

### 💡 Phase 2-B: 추가 팩터 구현

**⚠️ 반드시 Phase 2-A 완료 후 진행하세요!**

Phase 2-A에서 작동 안 하는 팩터를 모두 수정/제거한 후, 아래 3개 팩터를 추가 구현합니다.

**이 3개 팩터 선정 이유**:
- ✅ 사용 빈도 높음 (각각 4개, 4개, 1개 전략 사용)
- ✅ 계산 복잡도 낮음 (기존 데이터로 계산 가능)
- ✅ 성능 영향 적음 (재무 팩터로 한 번만 계산)
- ✅ 전략의 핵심 팩터 (가치투자, 배당투자 전략의 핵심)

#### 미구현 팩터 (3개):

#### 2.1 FCF_YIELD (잉여현금흐름 수익률)
**사용 전략**: warren_buffett, bill_ackman, glenn_greenberg, undervalued_dividend (4개)
**우선순위**: 높음 (4개 전략 사용)

**판단 기준 적용**:
- ✅ 사용 빈도: 4개 전략 → **구현 필수**
- ✅ 계산 복잡도: 간단한 뺄셈과 나눗셈 → **구현 가능**
- ✅ 성능 영향: 재무 팩터 (한 번만 계산) → **영향 미미**
- ❓ 데이터 가용성: 투자활동현금흐름 DB 확인 필요 → **확인 후 결정**

**데이터 요구사항:**
- ✅ 영업활동현금흐름 (이미 있음)
- ❓ 투자활동현금흐름 (DB 확인 필요) ← **Phase 2-A에서 확인**
- ✅ 시가총액 (이미 있음)

**계산 로직:**
```python
# FCF = 영업활동현금흐름 - 투자활동현금흐름
# FCF_YIELD = (FCF / 시가총액) × 100
fcf_yield = np.nan
operating_cf = row.get('영업활동현금흐름')
investing_cf = row.get('투자활동현금흐름')  # ← DB 스키마 확인 필요
market_cap = row.get('market_cap')
if operating_cf and investing_cf and market_cap and market_cap > 0:
    fcf = operating_cf - abs(investing_cf)
    fcf_yield = (fcf / market_cap) * 100
```

**추가 위치:**
- ✅ `factor_calculator_complete.py` → `_calculate_profitability_factors()` 메서드
- ⚠️ **Dual-Path 동기화 필요**: 이 팩터가 자주 사용되면 `backtest_extreme_optimized.py`에도 추가 고려

**예상 작업 시간:** 30분 (DB 확인 포함)

---

#### 2.2 DIVIDEND_YIELD (배당수익률)
**사용 전략**: peter_lynch, bill_ackman, undervalued_dividend, long_term_dividend (4개)
**우선순위**: 높음 (4개 전략 사용)

**판단 기준 적용**:
- ✅ 사용 빈도: 4개 전략 (배당투자 전략의 핵심!) → **구현 필수**
- ✅ 계산 복잡도: 간단한 나눗셈 → **구현 가능**
- ✅ 성능 영향: 재무 팩터 (한 번만 계산) → **영향 미미**
- ❓ 데이터 가용성: 배당금 데이터 확인 필요 → **확인 후 결정**
  - DB에 없으면 외부 데이터 수집 필요 (네이버 금융, KRX)
  - 수집 불가능하면 **제거 고려**

**데이터 요구사항:**
- ❓ 주당 배당금 (DB 스키마 확인 필요) ← **Phase 2-A에서 반드시 확인!**
- ✅ 현재 주가 (이미 있음)

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
- ⚠️ DB에 배당금 데이터가 있는지 **반드시 확인** 필요
- 없으면 외부 데이터 수집 필요 (네이버 금융, KRX 등)
- 배당금 데이터가 없으면 이 팩터는 **구현 불가** (우선순위 하향 조정 필요)

**추가 위치:**
- ✅ `factor_calculator_complete.py` → `_build_basic_factors()` 또는 별도 메서드
- ⚠️ **Dual-Path 동기화 필요**: 이 팩터가 자주 사용되면 `backtest_extreme_optimized.py`에도 추가 고려

**예상 작업 시간:** 1-2시간 (데이터 수집 포함 가능)

---

#### 2.3 EV_EBITDA
**사용 전략**: glenn_welling (1개)
**우선순위**: 중간 (1개 전략만 사용)

**판단 기준 적용**:
- ⚠️ 사용 빈도: 1개 전략만 사용 → **우선순위 낮음**
- ✅ 계산 복잡도: 간단한 사칙연산 → **구현 가능**
- ✅ 성능 영향: 재무 팩터 (한 번만 계산) → **영향 미미**
- ❓ 데이터 가용성: 감가상각비 확인 필요 → **대안 고려**
  - DB에 감가상각비 없으면 **EV/EBIT로 대체** (근사 계산)
  - 영업이익만으로도 충분히 유사한 지표

**대체 전략** (감가상각비 없을 경우):
- EV/EBITDA 대신 **EV/EBIT** 사용
- EBIT = 영업이익 (이미 있는 데이터)
- 의미: 감가상각비를 제외한 영업이익 기준으로 기업가치 평가
- 대부분의 경우 EV/EBITDA와 유사한 결과

**데이터 요구사항:**
- ✅ 시가총액 (이미 있음)
- ✅ 부채총계 (이미 있음)
- ✅ 현금및현금성자산 (이미 있음)
- ✅ 영업이익 (이미 있음)
- ❓ 감가상각비 (DB 확인 필요) ← **없으면 EV/EBIT로 대체**

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
depreciation = row.get('감가상각비', 0)  # ← DB 스키마 확인 필요

if market_cap and total_debt and operating_income and operating_income > 0:
    ev = market_cap + total_debt - cash
    ebitda = operating_income + depreciation
    if ebitda > 0:
        ev_ebitda = ev / ebitda
```

**주의사항:**
- 감가상각비 데이터가 없으면 영업이익만으로 근사 계산 (EV/EBIT)
- 1개 전략만 사용하므로 우선순위는 낮음

**추가 위치:**
- ✅ `factor_calculator_complete.py` → `_calculate_profitability_factors()` 메서드
- ❌ `backtest_extreme_optimized.py` 추가 불필요 (사용 빈도 낮음)

**예상 작업 시간:** 30-45분

---

## 📊 데이터베이스 스키마 확인 필요

Phase 2 작업을 시작하기 전에 **반드시** DB 스키마를 확인하세요!

### 확인해야 할 데이터:
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

## 🔄 전략 관리 플로우 (필수 이해!)

### 전략 시스템 구조

현재 시스템은 **"전략을 DB에 저장하고 사용"**하는 방식입니다.

```
scripts/migrate_strategies.py (전략 정의)
         ↓
   파이썬 스크립트 실행
         ↓
DB investment_strategies 테이블 (전략 저장)
         ↓
   백테스트 실행 시
         ↓
DB에서 전략 로드 → 조건 평가 → 매수/매도 결정
```

### 왜 전략 동기화가 중요한가?

**시나리오 1: 팩터 제거했는데 전략에서 계속 사용**
```
1. REVENUE_GROWTH_3Y 팩터 제거 (계산 불가능)
2. migrate_strategies.py는 수정 안 함 (여전히 REVENUE_GROWTH_3Y 사용)
3. DB 업데이트 안 함
4. 사용자가 전략 실행
   → 백테스트 실패! (팩터를 찾을 수 없음)
   → 또는 조건 평가 오류!
```

**시나리오 2: 팩터 대체했는데 전략은 옛날 팩터 사용**
```
1. REVENUE_GROWTH_3Y → REVENUE_GROWTH_1Y로 대체
2. migrate_strategies.py는 수정 안 함 (여전히 REVENUE_GROWTH_3Y 사용)
3. DB에는 옛날 팩터로 저장됨
4. 사용자가 전략 실행
   → 조건이 전혀 작동 안 함!
   → 사용자: "이 전략 왜 매수 안 해?"
```

### 팩터 변경 시 필수 체크리스트

팩터를 제거하거나 대체하기로 결정했으면:

**Step 1: 영향받는 전략 찾기**
```bash
# migrate_strategies.py에서 해당 팩터 사용하는 전략 검색
grep -n "REVENUE_GROWTH_3Y" scripts/migrate_strategies.py
```

**Step 2: migrate_strategies.py 수정**
- 팩터 제거: 해당 조건식 완전 삭제
- 팩터 대체: 옛날 팩터 → 새 팩터로 교체
- 예시:
  ```python
  # 변경 전
  {"field": "REVENUE_GROWTH_3Y", "operator": "GT", "value": 10}

  # 변경 후 (대체)
  {"field": "REVENUE_GROWTH_1Y", "operator": "GT", "value": 10}

  # 변경 후 (제거)
  # 조건식 자체를 삭제
  ```

**Step 3: DB 업데이트 (필수!)**
```bash
cd /path/to/SL-Back-end
python scripts/migrate_strategies.py
```
- 이 스크립트가 DB investment_strategies 테이블을 업데이트함
- **반드시 실행해야 함!** 안 하면 옛날 전략 계속 사용됨

**Step 4: 검증**
```bash
# DB에서 전략 확인
# PostgreSQL 접속 후
SELECT strategy_name, buy_conditions
FROM investment_strategies
WHERE strategy_name = 'peter_lynch';

# 수정된 팩터가 반영되었는지 확인
```

**Step 5: 백테스트 테스트**
- 수정된 전략으로 백테스트 실행
- 정상 작동하는지 확인 (매수 거래 발생하는지)

**Step 6: 프론트엔드 확인 (필요 시)**
- 전략 설명 UI에 옛날 팩터 언급되어 있으면 수정
- 사용자에게 보이는 전략 설명과 실제 구현이 일치하는지 확인

### 예시: REVENUE_GROWTH_3Y 제거 시 전체 플로우

```bash
# 1. 영향받는 전략 찾기
grep -rn "REVENUE_GROWTH_3Y" scripts/migrate_strategies.py
# 결과: peter_lynch, bill_ackman 전략에서 사용

# 2. migrate_strategies.py 수정
# peter_lynch 전략에서 REVENUE_GROWTH_3Y 조건 제거
# bill_ackman 전략에서 REVENUE_GROWTH_3Y → REVENUE_GROWTH_1Y 대체

# 3. DB 업데이트
python scripts/migrate_strategies.py

# 4. 검증
# - DB에서 전략 확인
# - peter_lynch 백테스트 실행 (REVENUE_GROWTH_3Y 조건 없이)
# - bill_ackman 백테스트 실행 (REVENUE_GROWTH_1Y 조건으로)

# 5. 문서화
# - 어떤 전략에서 어떤 팩터를 제거/대체했는지 기록
```

---

## 🎓 팩터 추가 표준 프로세스

### Step 1: 팩터 분석
1. 어떤 전략에서 사용하는가?
2. 계산에 필요한 데이터는 무엇인가?
3. DB에 데이터가 있는가?

### Step 2: 표준 경로 구현
1. `factor_calculator_complete.py` 수정
   - 적절한 메서드 선택 (`_build_basic_factors()`, `_calculate_growth_factors()` 등)
   - 계산 로직 추가
   - **주석으로 계산 공식 명시** (중요!)

### Step 3: 최적화 경로 구현 (재무 팩터 중 자주 사용되는 것만)
1. `backtest_extreme_optimized.py` 수정
   - `_calculate_financial_factors_once()` 메서드
   - 반환 딕셔너리에 팩터 추가
   - 주석으로 계산 공식 명시
   - ⚠️ **주의**: Line 14-37의 경고 메시지 참고!
   - **판단 기준**: 4개 이상 전략에서 사용되면 추가 고려

### Step 4: 기본 팩터 세트 업데이트 (⚠️ 매우 중요!)
**반드시 두 파일 모두 업데이트:**
1. `backtest_integration.py` 수정 (Line 187-196)
   - `required_factors` 세트에 추가
2. `backtest.py` 수정 (Line 1341-1349)
   - `required_factors` 세트에 추가
   - **이 두 파일이 동기화되지 않으면 버그 발생!**

### Step 5: 검증
1. Docker 재시작: `docker restart sl_backend_dev`
2. 백테스트 실행
3. 로그 확인하여 팩터 정상 계산 검증
4. 전략별 테스트

---

## ⚠️ 중요 주의사항

### 🔴 Critical: Dual-Path 동기화
**DEBT_RATIO 버그의 교훈을 잊지 마세요!**

1. **재무 팩터 중 자주 사용되는 것**:
   - 반드시 **두 곳 모두** 구현:
     - `factor_calculator_complete.py` (표준 경로)
     - `backtest_extreme_optimized.py` (최적화 경로)
   - 판단 기준: 4개 이상 전략에서 사용되면 최적화 경로에도 추가

2. **성장률 팩터, 기술적 팩터**:
   - **표준 경로만** 구현
   - 최적화 경로는 기본 재무 팩터만 다룸

3. **Phase 2의 3개 팩터**:
   - FCF_YIELD: 4개 전략 사용 → 양쪽 추가 고려
   - DIVIDEND_YIELD: 4개 전략 사용 → 양쪽 추가 고려
   - EV_EBITDA: 1개 전략만 사용 → 표준 경로만

### 🟡 Important: 기본 팩터 세트 동기화
**반드시 두 파일 모두 업데이트:**
- `backtest_integration.py` (Line 187-196)
- `backtest.py` (Line 1341-1349)

**동기화되지 않으면 특정 전략에서 팩터를 찾지 못하는 버그 발생!**

### 🟢 Recommended: 문서화
- 계산 로직에 주석 추가
- 데이터 출처 명시
- 특이 케이스 처리 방법 설명

---

## 📁 관련 문서

**작업 시작 전 필수 읽기:**
- `2025-11-21-debt-ratio-root-cause-fix.md` - DEBT_RATIO 버그 수정 과정
- `2025-11-21-missing-factors-analysis.md` - 누락 팩터 상세 분석
- `2025-11-21-factor-system-improvement-plan.md` - 전체 개선 계획

---

## 🔑 핵심 교훈

### 1. Dual-Path 동기화의 중요성
- **DEBT_RATIO 버그** (2025-11-21 오전):
  - 증상: "부채비율 < 200" 조건 선택 시 매수 거래 0건
  - 원인: 최적화 경로에 DEBT_RATIO 팩터가 없었음
  - 해결: 최적화 경로에 팩터 추가
- **OPERATING_INCOME_GROWTH 버그** (2025-11-21 오후):
  - 증상: "영업이익 성장률 >= 3" 조건 선택 시 매수 거래 0건
  - 원인: **동일한 문제 재발!** 최적화 경로에 5개 팩터가 모두 누락
  - 해결: 4개 1Y 성장률 팩터를 최적화 경로에 긴급 추가
  - **충격적 발견**: 문서에 "완료"라고 적혀있었지만 실제로는 작동 안 함!
- **교훈**:
  - 성능 최적화를 위한 코드 분리(Dual-Path)는 유지보수 비용을 크게 증가시킴
  - 한 곳만 수정하고 다른 곳은 잊어버리기 쉬움
  - **반드시 두 경로 모두 동기화해야 함**

### 2. 검증의 중요성 (가장 중요!)
**문서를 맹신하지 마세요!**

- **Phase 1 "완료"의 진실**:
  - 문서: "8개 팩터 추가 완료" ✅
  - 실제: 표준 경로만 추가, 최적화 경로는 1개만 추가 ❌
  - 결과: 사용자가 백테스트 돌려보고 나서야 버그 발견
- **프론트엔드 팩터 목록의 문제**:
  - 서버에서 팩터 목록 제공 → 사용자에게 선택지로 표시
  - 하지만 **실제로 계산되는지 검증 안 됨**
  - CHANGE_RATE, REVENUE_GROWTH_3Y, EARNINGS_GROWTH_3Y는 백테스트에서 작동 안 함
- **반드시 해야 할 검증**:
  1. ✅ 코드에 구현되어 있는가? (표준 경로 + 최적화 경로)
  2. ✅ 기본 팩터 세트에 포함되어 있는가?
  3. ✅ **실제로 백테스트 돌려서 매수 거래가 발생하는가?**
  4. ✅ 로그에서 팩터 값이 제대로 계산되는가?
- **Phase 2-A가 최우선인 이유**:
  - 더 이상 "문서만 완료"인 팩터를 양산하지 않기 위해
  - 모든 팩터를 실제로 테스트해서 작동 여부 확인
  - 작동 안 하는 팩터는 프론트엔드 목록에서 제거

### 3. 전체 플로우 이해의 중요성
- 로그 디버깅만으로는 근본 원인을 찾지 못함
- **시작점부터 끝까지** 전체 코드 경로를 추적해야 함
- 특히 **런타임 교체**(메서드 주입) 같은 패턴에 주의

### 4. 단계적 개선
- Phase 1 (긴급, 부분 완료) → Phase 2-A (전수 조사, 최우선!) → Phase 2-B (추가 팩터)
- 각 단계마다 검증 및 테스트
- 남은 개발 기간(4일) 고려하여 우선순위 조정
- **Phase 3 아키텍처 리팩토링은 보류** (성능 영향 없음)

### 5. 문서화의 가치
- 코드 주석으로 미래 개발자에게 경고
- 상세한 작업 계획으로 우선순위 명확화
- 인수인계 문서로 지식 전달
- **하지만 문서를 맹신하지 말 것!** 실제 작동 여부를 항상 검증

---

## ✅ 인수인계 체크리스트

### 📚 사전 준비
- [ ] `2025-11-21-debt-ratio-root-cause-fix.md` 읽기 (필수!)
- [ ] `2025-11-21-missing-factors-analysis.md` 읽기 (필수!)
- [ ] `2025-11-21-factor-system-improvement-plan.md` 읽기 (필수!)

### 💻 코드 이해
- [ ] `factor_calculator_complete.py` 구조 파악
- [ ] `backtest_extreme_optimized.py` 최적화 로직 이해
- [ ] Dual-path 동기화 필요성 이해
- [ ] 기본 팩터 세트 위치 파악 (2개 파일)

### 🗄️ 데이터베이스
- [ ] DB 스키마 확인 (배당금, 투자활동현금흐름, 감가상각비)
- [ ] 외부 데이터 소스 확인 (필요 시)

### 🎯 Phase 2-A 작업 (최우선!)
- [ ] 프론트엔드 팩터 목록 API 확인
- [ ] 전체 팩터 계산 여부 전수 조사
- [ ] 작동 안 하는 팩터 수정 또는 제거
- [ ] **전략 동기화 (필수!)**
  - [ ] `migrate_strategies.py`에서 제거/대체된 팩터 사용하는 전략 수정
  - [ ] `python scripts/migrate_strategies.py` 실행 (DB 업데이트)
  - [ ] 수정된 전략 백테스트 테스트
  - [ ] 수정 내역 문서화
- [ ] 팩터 분류 체계 정리

### 🎯 Phase 2-B 작업 (Phase 2-A 완료 후)
- [ ] FCF_YIELD 구현 (우선순위: 높음)
- [ ] DIVIDEND_YIELD 구현 (우선순위: 높음, 데이터 확인 필수)
- [ ] EV_EBITDA 구현 (우선순위: 중간)

### ✅ 검증
- [ ] Docker 재시작 및 코드 적용 확인
- [ ] 전략별 백테스트 테스트
- [ ] 로그 확인하여 팩터 정상 계산 검증
- [ ] 문서 업데이트 (작업 완료 후)

---

## 🚀 작업 우선순위 (남은 개발 기간: 4일)

### Day 1: 팩터 시스템 전수 조사 (Phase 2-A) 🔴 최우선
**목표**: 프론트엔드에 표시되는 모든 팩터가 실제로 작동하는지 검증

1. **프론트엔드 팩터 목록 API 확인** (30분)
   - 팩터 목록 API 엔드포인트 찾기
   - 현재 몇 개 팩터가 목록에 있는지 확인
   - 백엔드 코드에서 목록 생성 로직 추적

2. **전체 팩터 계산 여부 전수 조사** (1.5-2시간)
   - **Step 1**: 표준 경로 확인 (코드 리뷰)
     - `factor_calculator_complete.py`에 각 팩터 구현 여부 체크
   - **Step 2**: 최적화 경로 확인 (코드 리뷰)
     - `backtest_extreme_optimized.py`에 재무 팩터 구현 여부 체크
     - 재무 팩터인데 최적화 경로에 없으면 → **버그!**
   - **Step 3**: 기본 팩터 세트 확인 (코드 리뷰)
     - `backtest_integration.py`, `backtest.py` 두 파일 모두 확인
   - **Step 4**: 실제 백테스트 테스트 (가장 중요!)
     - 각 팩터마다 조건 하나만 넣고 백테스트 실행
     - 매수 0건이면 → 작동 안 하는 것 (버그 리스트에 추가)

3. **작동 안 하는 팩터 정리** (1시간)
   - 버그 리스트 작성 (팩터명, 원인, 수정 방안)
   - 수정 가능한 팩터 vs 제거해야 할 팩터 분류
   - 긴급 수정 계획 수립

### Day 2: 전략 동기화 및 팩터 분류 정리
**⚠️ 매우 중요한 날!** 팩터와 전략이 align 맞지 않으면 모든 작업이 무의미!

1. **전략 동기화** (1.5시간) 🔴 **최우선**
   - `migrate_strategies.py`에서 제거/대체된 팩터 사용하는 전략 찾기
     ```bash
     grep -n "REVENUE_GROWTH_3Y" scripts/migrate_strategies.py
     ```
   - 해당 전략 수정 (팩터 제거 or 대체)
   - DB 업데이트 실행
     ```bash
     python scripts/migrate_strategies.py
     ```
   - 각 전략별 백테스트 테스트 (정상 작동 확인)
   - 수정 내역 문서화 (어떤 전략에서 어떤 팩터를 제거/대체했는지)

2. **팩터 분류 체계 정리** (1시간)
   - 현재 분류 체계 검토
   - 새로운 분류로 재정리 (가치지표, 재무건전성, 수익성 등)

3. **프론트엔드 팩터 목록 동기화** (30분)
   - 제거된 팩터는 API 응답에서 제외
   - 대체된 팩터는 새 이름으로 업데이트

4. **DB 스키마 확인** (1시간)
   - 배당금, 투자활동현금흐름, 감가상각비 데이터 확인
   - Phase 2-B 팩터 구현 가능 여부 판단

### Day 3: 추가 팩터 구현 (Phase 2-B)
- FCF_YIELD 구현 (30분)
- DIVIDEND_YIELD 구현 (1시간, 데이터 수집 포함)
- EV_EBITDA 구현 (30분)
- 테스트 및 검증 (1시간)

### Day 4: 통합 테스트 및 문서화
- 13개 전략 전체 테스트 (1.5시간)
- 버그 수정 (필요 시, 1시간)
- 문서 업데이트 (30분)

**Phase 3 아키텍처 리팩토링은 시간 관계상 보류합니다.**
- 이유: 성능에 직접 영향 없음, 유지보수 편의성 개선일 뿐
- 주의만 하면 동기화 이슈 피할 수 있음
- 남은 4일 동안 더 중요한 기능 개발에 집중

---

**인수인계 완료!** 🎉

**기억하세요:**
- 🚨 **Phase 2-A 최우선!** 더 이상 "문서만 완료"인 팩터를 양산하지 마세요
- ⚠️ **Dual-Path 동기화 필수** (DEBT_RATIO, OPERATING_INCOME_GROWTH 버그 사례)
- ⚠️ 기본 팩터 세트 2개 파일 모두 업데이트 (`backtest_integration.py`, `backtest.py`)
- 🔄 **전략 동기화 필수!** 팩터 제거/대체 시 반드시:
  1. `migrate_strategies.py` 수정
  2. `python scripts/migrate_strategies.py` 실행 (DB 업데이트)
  3. 각 전략 백테스트 테스트
  4. 팩터와 전략이 align 안 맞으면 디버깅에 한세월!
- 📚 작업 전 3개 문서 반드시 읽기 (DEBT_RATIO 버그 수정 과정 이해 필수!)
- ✅ **문서를 맹신하지 말고 항상 실제 백테스트로 작동 여부를 검증하세요!**
- 🔍 **검증 = 코드 구현 + 실제 백테스트 실행 + 매수 거래 발생 확인**

궁금한 점이나 추가 설명이 필요한 부분이 있으면 언제든지 문의하세요.
