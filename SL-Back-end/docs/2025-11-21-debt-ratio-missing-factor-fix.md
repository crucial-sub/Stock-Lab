# DEBT_RATIO 팩터 누락 문제 해결

**작성일**: 2025-11-21
**작업자**: AI Assistant
**이슈**: 백테스트에서 "부채비율 < 200" 조건 선택 시 매수 거래 0건 발생

---

## 📋 문제 상황

### 증상
사용자가 매수 조건으로 "부채비율(DEBT_RATIO) < 200"을 선택했을 때:
- 조건이 올바르게 파싱됨: `{'factor': 'DEBT_RATIO', 'operator': '<', 'value': 200.0}`
- 벡터화 쿼리가 올바르게 생성됨: `(\`DEBT_RATIO\`.notna() and \`DEBT_RATIO\` < 200.0)`
- 하지만 **매수 거래가 0건** 발생

### 근본 원인
로깅을 통해 확인한 결과, `factor_data` DataFrame에 **DEBT_RATIO 컬럼이 완전히 누락**되어 있었습니다.

**실제 컬럼 목록** (로그에서 확인):
```python
['date', 'stock_code', 'MOMENTUM_1M', 'MOMENTUM_3M', 'RSI',
 'BOLLINGER_POSITION', 'BOLLINGER_WIDTH', 'MACD', 'MACD_SIGNAL',
 'MACD_HISTOGRAM', 'PER', 'PBR', 'ROE', 'ROA', 'OPERATING_MARGIN',
 'NET_MARGIN', 'industry', 'market_type']
```

→ **DEBT_RATIO가 없음!**

---

## 🔍 원인 분석

### 팩터 데이터 파이프라인 추적

**1단계: 통합 레이어** (`factor_integration.py`)
```python
# Line 67
daily_factors = await self.factor_calculator.get_factor_data_for_date(
    date=trading_day,
    factor_names=None  # 모든 팩터
)
```

**2단계: Import 추적** (`factor_integration.py`)
```python
# Line 12
from app.services.factor_calculator_complete import CompleteFactorCalculator
```

**3단계: 문제 발견** (`factor_calculator_complete.py`)
- ❌ `get_factor_data_for_date()` 메서드가 **존재하지 않음**
- ✅ `calculate_all_factors()` 메서드는 존재
- ✅ `_build_basic_factors()` 메서드에 DEBT_RATIO 계산 로직 존재 (Line 381)

```python
# Line 381 - DEBT_RATIO 계산 코드는 존재함
merged['DEBT_RATIO'] = merged.apply(
    lambda row: _safe_ratio(row.get('부채총계'), row.get('자본총계')) * 100
    if _safe_ratio(row.get('부채총계'), row.get('자본총계')) is not None
    else None,
    axis=1
)
```

**4단계: 아키텍처 미스매치 발견**
- `factor_calculator_complete_old.py`에는 `get_factor_data_for_date()` 메서드 존재 (Line 635)
- `factor_calculator_complete.py`는 리팩토링 과정에서 계산 로직만 남기고 **통합 메서드가 누락됨**

---

## ✅ 해결 방법

### 1. 누락된 통합 메서드 추가

`factor_calculator_complete.py`에 두 개의 메서드 추가 (Lines 833-871):

#### `get_factor_data_for_date()` 메서드
```python
async def get_factor_data_for_date(
    self,
    date: datetime,
    factor_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """특정 날짜의 팩터 데이터 조회"""

    # 모든 활성 종목 가져오기
    stock_codes = await self._get_active_stocks(date)

    # 모든 팩터 계산
    all_factors = await self.calculate_all_factors(stock_codes, date)

    # 특정 팩터만 필터링 (요청된 경우)
    if factor_names:
        columns_to_keep = ['stock_code', 'stock_name'] + factor_names
        columns_to_keep = [col for col in columns_to_keep if col in all_factors.columns]
        all_factors = all_factors[columns_to_keep]

    # 날짜 컬럼 추가
    all_factors['date'] = date

    return all_factors
```

#### `_get_active_stocks()` 헬퍼 메서드
```python
async def _get_active_stocks(self, date: datetime) -> List[str]:
    """활성 종목 리스트 조회"""
    from sqlalchemy import text

    query = text("""
    SELECT DISTINCT c.stock_code
    FROM stock_prices sp
    JOIN companies c ON sp.company_id = c.company_id
    WHERE sp.trade_date = :date
    AND sp.volume > 0
    AND sp.close_price > 0
    """)

    result = await self.db.execute(query, {"date": date.date()})
    return [row[0] for row in result.fetchall()]
```

### 2. 디버깅 로그 추가

`condition_evaluator_vectorized.py`에 임시 디버깅 로그 추가:

```python
# Line 86-94: DEBT_RATIO 쿼리 확인
if 'DEBT_RATIO' in query_str:
    logger.info(f"🔍 DEBT_RATIO 쿼리 확인:")
    logger.info(f"  📝 쿼리: {query_str}")
    logger.info(f"  📊 데이터 컬럼: {list(date_data.columns)}")
    logger.info(f"  ✅ DEBT_RATIO in columns? {'DEBT_RATIO' in date_data.columns}")
    if 'DEBT_RATIO' in date_data.columns:
        logger.info(f"  📈 DEBT_RATIO 샘플 값: {date_data['DEBT_RATIO'].head(3).tolist()}")
        logger.info(f"  📊 DEBT_RATIO < 200 개수: {(date_data['DEBT_RATIO'] < 200).sum()}")
```

---

## 🔄 수정된 데이터 플로우

### Before (문제 상황)
```
factor_integration.py
  └─> factor_calculator.get_factor_data_for_date()  ❌ 메서드 없음!
        └─> ??? (알 수 없는 폴백 로직)
              └─> 불완전한 factor_data 반환 (DEBT_RATIO 없음)
```

### After (수정 후)
```
factor_integration.py
  └─> factor_calculator.get_factor_data_for_date()  ✅ 추가됨
        └─> calculate_all_factors()
              └─> _build_basic_factors()
                    └─> DEBT_RATIO 계산 (Line 381)
                          └─> 완전한 factor_data 반환 (DEBT_RATIO 포함)
```

---

## 📊 검증 방법

### 다음 백테스트 실행 시 확인할 로그

1. **DEBT_RATIO 컬럼 존재 확인**
```
🔍 DEBT_RATIO 쿼리 확인:
  📊 데이터 컬럼: [..., 'DEBT_RATIO', ...]
  ✅ DEBT_RATIO in columns? True
```

2. **DEBT_RATIO 데이터 확인**
```
  📈 DEBT_RATIO 샘플 값: [150.5, 45.2, 220.8]
  📊 DEBT_RATIO < 200 개수: 85
```

3. **매수 거래 발생 확인**
```
✅ 벡터화 평가 완료: 85/121개 종목 선택
```

---

## 📝 관련 파일

| 파일 | 변경 내용 | 라인 |
|------|----------|------|
| `factor_calculator_complete.py` | `get_factor_data_for_date()` 메서드 추가 | 833-855 |
| `factor_calculator_complete.py` | `_get_active_stocks()` 메서드 추가 | 857-871 |
| `condition_evaluator_vectorized.py` | 디버깅 로그 추가 | 86-102 |

---

## 🎯 향후 작업

### 1. 로그 검증 후 정리
- 백테스트 실행 후 DEBT_RATIO가 정상적으로 포함되는지 확인
- 확인 완료 후 임시 디버깅 로그 제거

### 2. 유사 문제 방지
- 다른 팩터들도 정상적으로 계산되는지 검증
- 팩터 계산 파이프라인에 대한 통합 테스트 추가 권장

### 3. 아키텍처 정리
- `factor_calculator_complete_old.py` 파일의 필요성 검토
- 리팩토링 과정에서 누락된 다른 메서드가 있는지 확인

---

## 🔑 핵심 교훈

1. **통합 레이어의 중요성**: 계산 로직이 존재해도 통합 메서드가 없으면 호출할 수 없음
2. **리팩토링 시 주의**: 코드 분리 시 의존성 체인을 꼼꼼히 확인해야 함
3. **디버깅 로깅**: 컬럼 목록 로깅이 문제 발견의 핵심이었음
4. **데이터 파이프라인 추적**: import 체인을 따라가며 실제 호출되는 코드 확인 필요

---

**작업 완료!** 🎉

다음 백테스트 실행 결과를 확인하여 DEBT_RATIO가 정상적으로 작동하는지 검증 필요.
