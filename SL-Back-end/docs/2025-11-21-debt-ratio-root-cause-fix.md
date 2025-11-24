# DEBT_RATIO 팩터 누락 문제 - 근본 원인 해결

**작성일**: 2025-11-21
**작업자**: AI Assistant
**이슈**: 백테스트에서 "부채비율 < 200" 조건 선택 시 매수 거래 0건 발생

---

## 📋 문제 요약

### 증상
- 사용자가 매수 조건으로 "부채비율(DEBT_RATIO) < 200"을 선택
- 조건 파싱 및 쿼리 생성은 정상적으로 작동
- 하지만 **매수 거래가 0건** 발생
- PER, PBR 등 다른 재무 팩터는 정상 작동

### 이전 시도들 (실패)
1. `factor_integration.py`에 디버깅 로그 추가
2. `condition_evaluator_vectorized.py`에 DEBT_RATIO 확인 로그 추가
3. `factor_calculator_complete.py`에 `get_factor_data_for_date()` 메서드 추가

**문제점**: 모든 시도가 로그 확인에만 집중하여 근본 원인을 찾지 못함

---

## 🎯 근본 원인 분석

### 사용자 피드백의 핵심
> "PER, PBR는 잘 계산됨. 부채비율은 계산이 안됨.
> 그렇다면 (1) 부채비율 계산 공식 자체가 문제인지, (2) 팩터를 등록하는 곳이 있는데 거기에 등록을 안한건지.
> 백테스트에서 조건식을 계산하고 적용해서 매수를 진행하는 **모든 과정**에 대해 처음부터 철저하게 조사해야 함."

### 전체 플로우 추적

#### 1단계: 백테스트 엔진 시작점
**파일**: `backtest.py`
**라인**: 438

```python
factor_data = await self._calculate_all_factors_optimized(
    price_data, financial_data, start_date, end_date,
    buy_conditions=backtest_conditions,
    priority_factor=priority_factor
)
```

→ 백테스트는 `_calculate_all_factors_optimized()` 메서드를 사용

#### 2단계: 필요한 팩터 추출
**파일**: `backtest.py`
**라인**: 1352-1360

```python
required_factors = self._extract_required_factors(buy_conditions or [], priority_factor)
```

**로그 확인**:
```
필요한 팩터: {'PER', 'DEBT_RATIO'}
극한 최적화 모드 활성화 (Extreme Performance - 모든 팩터)
```

→ ✅ DEBT_RATIO는 정상적으로 추출됨!

#### 3단계: 최적화 주입
**파일**: `backtest_integration.py`
**라인**: 405

```python
# 극한 최적화 함수 주입
backtest_engine._calculate_all_factors_optimized = (
    create_optimized_factor_calculator(backtest_engine.db)
)
```

→ 백테스트 엔진의 팩터 계산 메서드가 **런타임에 교체됨**

#### 4단계: 극한 최적화 모드 실행
**파일**: `backtest_extreme_optimized.py`
**라인**: 312 → 337

```python
async def calculate_all_indicators_batch_extreme(...):
    # ...
    financial_factors = await _calculate_financial_factors_once(
        db, stock_codes, end_date, required_factors
    )
```

→ 재무 팩터는 **한 번만 계산**하고 캐싱 (분기별 데이터이므로)

#### 5단계: 🚨 **근본 원인 발견**
**파일**: `backtest_extreme_optimized.py`
**라인**: 481-488

```python
financial_factors[stock_code] = {
    'PER': per_val,
    'PBR': pbr_val,
    'ROE': roe_val,
    'ROA': roa_val,
    'OPERATING_MARGIN': operating_margin,
    'NET_MARGIN': net_margin,
}
```

→ **DEBT_RATIO가 딕셔너리에 없음!**

### 왜 이런 일이 발생했는가?

1. **두 개의 계산 경로 존재**:
   - **표준 경로**: `factor_calculator_complete.py` (DEBT_RATIO 계산 로직 있음)
   - **최적화 경로**: `backtest_extreme_optimized.py` (DEBT_RATIO 계산 로직 **없음**)

2. **백테스트는 항상 최적화 경로 사용**:
   - 5일 이상의 백테스트는 자동으로 극한 최적화 모드 활성화
   - 최적화 경로에서 재무 팩터 계산 시 DEBT_RATIO를 누락

3. **이전 수정이 효과 없었던 이유**:
   - `factor_calculator_complete.py`를 수정했지만
   - 실제 실행 시에는 `backtest_extreme_optimized.py`가 사용됨
   - 따라서 수정한 코드가 **전혀 실행되지 않음**

---

## ✅ 해결 방법

### 1. 극한 최적화 모드에 DEBT_RATIO 추가

**파일**: `backtest_extreme_optimized.py`

#### 수정 1: 부채총계 데이터 추출 (Line 443)
```python
total_debt = row.get('부채총계')
```

#### 수정 2: DEBT_RATIO 계산 로직 추가 (Lines 465-468)
```python
# 부채비율 = 부채총계 / 자본총계 × 100
debt_ratio = np.nan
if total_debt is not None and total_equity is not None and total_equity > 0:
    debt_ratio = (float(total_debt) / float(total_equity)) * 100
```

#### 수정 3: 반환 딕셔너리에 추가 (Line 492)
```python
financial_factors[stock_code] = {
    'PER': per_val,
    'PBR': pbr_val,
    'ROE': roe_val,
    'ROA': roa_val,
    'DEBT_RATIO': debt_ratio,  # ⬅️ 추가됨
    'OPERATING_MARGIN': operating_margin,
    'NET_MARGIN': net_margin,
}
```

### 2. 기본 팩터 세트에 DEBT_RATIO 추가

**파일**: `backtest_integration.py` (Line 188)

```python
if not required_factors:
    required_factors = {
        'PER', 'PBR', 'ROE', 'ROA', 'DEBT_RATIO',  # ⬅️ 추가됨
        'MOMENTUM_1M', 'MOMENTUM_3M', 'MOMENTUM_6M', 'MOMENTUM_12M',
        'VOLATILITY', 'AVG_TRADING_VALUE', 'TURNOVER_RATE',
        'BOLLINGER_POSITION', 'BOLLINGER_WIDTH', 'RSI', 'MACD',
        'OPERATING_MARGIN', 'NET_MARGIN'
    }
```

---

## 🔄 수정된 데이터 플로우

### Before (문제 상황)
```
backtest.py
  └─> _calculate_all_factors_optimized() (런타임 교체됨)
        └─> backtest_extreme_optimized.py
              └─> _calculate_financial_factors_once()
                    └─> financial_factors = {
                          'PER', 'PBR', 'ROE', 'ROA', 'OPERATING_MARGIN', 'NET_MARGIN'
                          ❌ DEBT_RATIO 없음!
                        }
```

### After (수정 후)
```
backtest.py
  └─> _calculate_all_factors_optimized() (런타임 교체됨)
        └─> backtest_extreme_optimized.py
              └─> _calculate_financial_factors_once()
                    └─> debt_ratio = (부채총계 / 자본총계) × 100
                          └─> financial_factors = {
                                'PER', 'PBR', 'ROE', 'ROA', 'DEBT_RATIO', ✅
                                'OPERATING_MARGIN', 'NET_MARGIN'
                              }
```

---

## 📊 검증 방법

### Docker 재시작
```bash
docker restart sl_backend_dev
```

### 코드 적용 확인
```bash
# DEBT_RATIO 계산 로직 확인
docker exec sl_backend_dev grep -B3 "debt_ratio = (float(total_debt)" /app/app/services/backtest_extreme_optimized.py

# 반환 딕셔너리 확인
docker exec sl_backend_dev grep "DEBT_RATIO.*debt_ratio" /app/app/services/backtest_extreme_optimized.py

# 기본 팩터 세트 확인
docker exec sl_backend_dev grep "'PER', 'PBR', 'ROE', 'ROA', 'DEBT_RATIO'" /app/app/services/backtest_integration.py
```

### 백테스트 실행 테스트
1. 프론트엔드에서 "부채비율 < 200" 조건으로 백테스트 실행
2. 로그에서 다음을 확인:
   ```
   필요한 팩터: {'PER', 'DEBT_RATIO'}
   극한 최적화 모드 활성화
   ```
3. 매수 거래가 발생하는지 확인 (0건 → N건)

---

## 📝 관련 파일

| 파일 | 변경 내용 | 라인 |
|------|----------|------|
| `backtest_extreme_optimized.py` | `total_debt` 추출 추가 | 443 |
| `backtest_extreme_optimized.py` | DEBT_RATIO 계산 로직 추가 | 465-468 |
| `backtest_extreme_optimized.py` | 반환 딕셔너리에 DEBT_RATIO 추가 | 492 |
| `backtest_integration.py` | 기본 팩터 세트에 DEBT_RATIO 추가 | 188 |

---

## 🎯 핵심 교훈

### 1. 로그 디버깅의 한계
- **로그만 확인하는 것은 증상 파악**일 뿐, 근본 원인을 찾지 못함
- 여러 번 로그를 추가해도 **실행 흐름을 이해하지 못하면 무의미**

### 2. 전체 플로우 이해의 중요성
- **시작점부터 끝까지** 전체 코드 경로를 추적해야 함
- 특히 **런타임 교체**(메서드 주입) 같은 패턴에 주의

### 3. 아키텍처 패턴 파악
- **최적화 경로와 표준 경로가 분리된 아키텍처**
- 최적화를 위해 별도 구현이 존재할 때, **동기화 누락** 주의

### 4. 문제 해결 접근법
- **증상 → 원인 → 해결** 순서가 아니라
- **전체 이해 → 원인 특정 → 해결** 순서가 더 효과적

### 5. 사용자 피드백의 가치
> "PER, PBR는 되는데 DEBT_RATIO는 안되는 것부터 단순하게 생각하자"

- 이 간단한 관찰이 핵심 힌트였음
- "왜 이 팩터만 안될까?" → 계산 경로가 다르기 때문

---

## 🚀 향후 권장 사항

### 1. 팩터 추가 프로세스 정립
새로운 재무 팩터 추가 시 **반드시 두 곳에 추가**:
- ✅ `factor_calculator_complete.py` (표준 경로)
- ✅ `backtest_extreme_optimized.py` (최적화 경로)

### 2. 자동화된 동기화 체크
- 두 경로에서 계산되는 팩터 목록이 일치하는지 단위 테스트 추가
- CI/CD에서 팩터 목록 일치 여부 검증

### 3. 코드 문서화
- `backtest_extreme_optimized.py` 파일 상단에 주석 추가:
  ```python
  """
  ⚠️ 주의: 새로운 재무 팩터 추가 시
  factor_calculator_complete.py와 함께 이 파일도 수정 필요!
  """
  ```

### 4. 아키텍처 리팩토링 고려
- 재무 팩터 계산 로직을 **단일 소스**로 통합
- 최적화 경로에서도 표준 계산 로직을 재사용하도록 구조 변경

---

## ✅ 작업 완료 상태

- [x] 근본 원인 파악 (극한 최적화 모드에서 DEBT_RATIO 누락)
- [x] `backtest_extreme_optimized.py` 수정 (DEBT_RATIO 계산 추가)
- [x] `backtest_integration.py` 수정 (기본 팩터 세트에 추가)
- [x] Docker 재시작 및 코드 적용 확인
- [ ] 사용자 백테스트 실행 검증 대기 중

---

**다음 단계**: 사용자가 "부채비율 < 200" 조건으로 백테스트를 실행하여 매수 거래가 정상 발생하는지 확인.
