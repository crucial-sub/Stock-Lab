# 백테스트 매수 조건 처리 버그 수정

## 문제 상황
백테스트 실행 시 매수가 전혀 발생하지 않음 (매수 후보 0개 계속 발생)

## 원인 분석

### 문제 1: Tuple 반환 버그
**파일**: [SL-Back-end/app/services/factor_integration.py:101](SL-Back-end/app/services/factor_integration.py#L101)

`evaluate_buy_conditions_with_factors` 함수가 논리식 조건일 때 Tuple을 반환하는 문제:

```python
# Before (버그)
if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
    return self.condition_evaluator.evaluate_buy_conditions(...)
    # 반환값: Tuple[List[str], Dict] - 두 값 반환!
```

`condition_evaluator.evaluate_buy_conditions`는 `Tuple[List[str], Dict]`를 반환하는데, 이를 그대로 반환하면 호출자는 `List[str]`를 기대하므로 타입 불일치 발생.

**해결**:
```python
# After (수정)
if isinstance(buy_conditions, dict) and 'expression' in buy_conditions:
    selected_stocks, _ = self.condition_evaluator.evaluate_buy_conditions(...)
    return selected_stocks
    # 반환값: List[str] - 종목 리스트만 반환
```

### 문제 2: 잘못된 논리식 expression 생성
**파일**: [SL-Back-end/app/services/advanced_backtest.py:191-198](SL-Back-end/app/services/advanced_backtest.py#L191-L198)

프론트엔드에서 받은 조건을 논리식으로 변환할 때, `buy_logic` 값("AND" 또는 "OR")을 그대로 expression으로 사용하는 버그:

```python
# Before (버그)
expression_text = buy_logic.strip() if buy_logic else ""
if not expression_text and parsed_conditions:
    expression_text = " and ".join([c["id"] for c in parsed_conditions])
```

**문제점**:
- `buy_logic = "AND"`일 때 → `expression_text = "AND"`
- 이건 논리식이 아님! 조건 ID여야 함
- 예: 조건이 `[{"id": "A", ...}]`이면 `expression = "A"`
- 조건이 `[{"id": "A", ...}, {"id": "B", ...}]`이면 `expression = "A and B"`

**실제 전달된 데이터 예시**:
```
매수 조건: [{'name': 'A', 'exp_left_side': '기본값({pbr})', 'inequality': '>=', 'exp_right_side': 0.0}]
```

파싱 후:
```python
parsed_conditions = [
    {
        "id": "A",
        "factor": "PBR",
        "operator": ">=",
        "value": 0.0,
        "description": "기본값({pbr})"
    }
]
```

원래 코드:
- `buy_logic = "AND"` → `expression_text = "AND"` (잘못됨!)

올바른 결과:
- `expression_text = "A"` (조건 ID 하나)
- 또는 여러 조건이면 `expression_text = "A and B"`

**해결**:
```python
# After (수정)
expression_text = ""
if parsed_conditions:
    if buy_logic and buy_logic.upper() == "OR":
        expression_text = " or ".join([c["id"] for c in parsed_conditions])
    else:
        # 기본값은 AND
        expression_text = " and ".join([c["id"] for c in parsed_conditions])
```

**결과**:
- 조건 1개: `expression_text = "A"`
- 조건 2개 (AND): `expression_text = "A and B"`
- 조건 2개 (OR): `expression_text = "A or B"`

### 문제 3: buy_condition_payload 생성 로직
**파일**: [SL-Back-end/app/services/advanced_backtest.py:203-210](SL-Back-end/app/services/advanced_backtest.py#L203-L210)

```python
# Before (불명확)
if parsed_conditions:
    buy_condition_payload = {
        "expression": expression_text or parsed_conditions[0]["id"],
        ...
    }
```

fallback으로 `parsed_conditions[0]["id"]`를 사용하지만, 이제 `expression_text`가 항상 제대로 생성되므로 불필요.

**해결**:
```python
# After (명확하게)
if parsed_conditions and expression_text:
    buy_condition_payload = {
        "expression": expression_text,
        ...
    }
```

## 수정 파일

### 1. [SL-Back-end/app/services/factor_integration.py](SL-Back-end/app/services/factor_integration.py#L99-L107)
**변경**: Tuple unpacking 추가

### 2. [SL-Back-end/app/services/advanced_backtest.py](SL-Back-end/app/services/advanced_backtest.py#L191-L214)
**변경**:
- 논리식 expression 생성 로직 수정
- 디버그 로그 추가

## 수정 후 동작 흐름

1. **프론트엔드**: 조건 전송
   ```json
   {
     "buy_conditions": [
       {"name": "A", "exp_left_side": "기본값({pbr})", "inequality": ">=", "exp_right_side": 0.0}
     ],
     "buy_logic": "AND"
   }
   ```

2. **advanced_backtest.py**: 조건 파싱
   ```python
   parsed_conditions = [
       {"id": "A", "factor": "PBR", "operator": ">=", "value": 0.0}
   ]
   expression_text = "A"  # 조건 1개이므로
   ```

3. **buy_condition_payload 생성**:
   ```python
   {
       "expression": "A",
       "conditions": [
           {"id": "A", "factor": "PBR", "operator": ">=", "value": 0.0}
       ]
   }
   ```

4. **condition_evaluator.py**: 논리식 평가
   - expression "A"를 파싱
   - 조건 "A"는 `PBR >= 0.0`
   - 각 종목의 PBR 값 확인
   - 조건 만족 종목 리스트 반환

5. **factor_integration.py**: Tuple unpacking
   ```python
   selected_stocks, _ = condition_evaluator.evaluate_buy_conditions(...)
   return selected_stocks  # List[str]만 반환
   ```

6. **backtest.py**: 매수 후보 선정
   ```python
   buy_candidates = await self._select_buy_candidates(...)
   # buy_candidates는 List[str] (정상)
   new_buy_candidates = [s for s in buy_candidates if s not in holdings]
   # 에러 없음!
   ```

## 테스트 결과

### 수정 전
- ❌ `TypeError: unhashable type: 'list'`
- ❌ 매수 후보 0개 계속 발생
- ❌ 거래 전혀 발생 안함

### 수정 후
- ✅ Tuple unpacking으로 타입 에러 해결
- ⏳ 논리식 expression 제대로 생성
- ⏳ 조건 평가 정상 작동 예상
- ⏳ 매수 거래 발생 예상 (사용자 테스트 필요)

## 추가 디버그 로그

새로 추가된 로그로 문제 추적 가능:
```
📊 파싱된 조건: [...]
📊 생성된 expression: A
📊 최종 buy_condition_payload: {...}
```

## 다음 단계

1. ✅ 수정 완료
2. ✅ Docker 재시작
3. ⏳ 사용자가 백테스트 재실행
4. ⏳ 로그 확인하여 조건 평가 정상 작동 검증
5. ⏳ 매수 거래 발생 확인
