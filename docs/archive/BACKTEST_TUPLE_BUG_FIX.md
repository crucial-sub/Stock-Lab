# 백테스트 Tuple 버그 수정

## 문제 상황
사용자가 백테스트를 실행할 때 다음 에러가 발생:
```
TypeError: unhashable type: 'list'
File "/app/app/services/backtest.py", line 1307, in <listcomp>
    new_buy_candidates = [s for s in buy_candidates if s not in holdings]
                                                       ^^^^^^^^^^^^^^^^^
```

## 원인 분석

### 에러 발생 위치
[SL-Back-end/app/services/backtest.py:1303](SL-Back-end/app/services/backtest.py#L1303)

```python
new_buy_candidates = [s for s in buy_candidates if s not in holdings]
```

### 근본 원인
`buy_candidates`가 `List[str]`이어야 하는데 `Tuple[List[str], Dict]` 형태로 반환됨.

디버그 로그 확인:
```
🔍 buy_candidates 타입: <class 'tuple'>, 내용: ([], {})
🔍 첫 번째 요소 타입: <class 'list'>, 값: []
```

### 버그 추적

1. **[SL-Back-end/app/services/backtest.py:1291-1300](SL-Back-end/app/services/backtest.py#L1291-L1300)**:
   ```python
   buy_candidates = await self._select_buy_candidates(...)
   ```
   - 반환 타입 기대: `List[str]`
   - 실제 반환: `Tuple[List[str], Dict]`

2. **[SL-Back-end/app/services/backtest.py:1648-1712](SL-Back-end/app/services/backtest.py#L1648-L1712)** - `_select_buy_candidates`:
   ```python
   async def _select_buy_candidates(...) -> List[str]:
   ```
   - 함수 시그니처는 `List[str]` 반환 명시

3. **[SL-Back-end/app/services/factor_integration.py:101-106](SL-Back-end/app/services/factor_integration.py#L101-L106)** - **버그 발견!**:
   ```python
   if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
       return self.condition_evaluator.evaluate_buy_conditions(...)
   ```
   - 논리식 조건일 때 `condition_evaluator.evaluate_buy_conditions`의 반환값을 그대로 반환

4. **[SL-Back-end/app/services/condition_evaluator.py:227-233](SL-Back-end/app/services/condition_evaluator.py#L227-L233)** - **문제의 함수**:
   ```python
   def evaluate_buy_conditions(
       ...
   ) -> Tuple[List[str], Dict[str, Dict[str, ConditionResult]]]:
   ```
   - 반환 타입: `Tuple[List[str], Dict]`
   - 첫 번째 요소: 조건 만족 종목 리스트
   - 두 번째 요소: 조건 평가 상세 정보

## 수정 내용

### 파일: [SL-Back-end/app/services/factor_integration.py:99-107](SL-Back-end/app/services/factor_integration.py#L99-L107)

**Before**:
```python
# 논리식 조건인 경우
if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
    return self.condition_evaluator.evaluate_buy_conditions(
        factor_data=factor_data,
        stock_codes=stock_codes,
        buy_expression=buy_conditions,
        trading_date=trading_date
    )
```

**After**:
```python
# 논리식 조건인 경우
if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
    selected_stocks, _ = self.condition_evaluator.evaluate_buy_conditions(
        factor_data=factor_data,
        stock_codes=stock_codes,
        buy_expression=buy_conditions,
        trading_date=trading_date
    )
    return selected_stocks
```

### 변경 사항
- Tuple unpacking 추가: `selected_stocks, _`
- 종목 리스트만 반환: `return selected_stocks`
- 두 번째 요소(상세 정보)는 버림: `_`

## 수정 완료 확인

### 테스트
1. ✅ Docker 재시작
2. ✅ 백엔드 정상 기동 확인
3. ⏳ 실제 백테스트 테스트 대기 (사용자가 진행)

### 영향 범위
- **수정 파일**: `SL-Back-end/app/services/factor_integration.py`
- **영향받는 함수**: `evaluate_buy_conditions_with_factors`
- **영향받는 시나리오**: 논리식 조건(`expression` 포함) 사용 시

### 일반 조건(AND 로직)에는 영향 없음
- 일반 조건 경로는 변경 없음 (Line 108-164)
- 기존 테스트(증권 테마, 삼성전자) 정상 작동 확인됨

## 추가 정리

### 제거한 디버그 로그
[SL-Back-end/app/services/backtest.py:1303-1305](SL-Back-end/app/services/backtest.py#L1303-L1305)에서 다음 로그 제거:
```python
logger.info(f"🔍 buy_candidates 타입: {type(buy_candidates)}, 내용: ...")
logger.info(f"🔍 첫 번째 요소 타입: {type(buy_candidates[0])}, 값: ...")
```

## 결론

**문제**: Tuple을 List로 착각하여 unpacking 없이 반환
**해결**: Tuple unpacking 후 첫 번째 요소(종목 리스트)만 반환
**상태**: ✅ 수정 완료, 테스트 대기 중
