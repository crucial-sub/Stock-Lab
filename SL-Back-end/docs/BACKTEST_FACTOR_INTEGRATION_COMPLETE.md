# 🎯 백테스트 엔진 - 54개 팩터 통합 완료

## ✅ 통합 작업 완료

### 1. **백테스트 엔진 수정** (`backtest.py`)

#### Before (13개 팩터)
```python
# 기존: 자체 팩터 계산 (13개만)
factor_data = await self._calculate_all_factors(
    price_data, financial_data, start_date, end_date
)
```

#### After (54개 팩터)
```python
# 현재: 통합 모듈 사용 (54개 팩터)
from app.services.factor_integration import FactorIntegration
factor_integrator = FactorIntegration(self.db)

factor_data = await factor_integrator.get_integrated_factor_data(
    start_date=start_date,
    end_date=end_date,
    stock_codes=stock_codes
)
```

### 2. **매수 조건 평가 통합**

#### Before
```python
# 기존: 13개 팩터로 평가
evaluator.evaluate_buy_conditions(
    factor_data=date_factors,  # 13개 팩터
    ...
)
```

#### After
```python
# 현재: 54개 팩터로 평가
selected_stocks = factor_integrator.evaluate_buy_conditions_with_factors(
    factor_data=factor_data,  # 54개 팩터
    stock_codes=tradeable_stocks,
    buy_conditions=buy_conditions,
    trading_date=trading_ts
)
```

## 📊 사용 가능한 54개 팩터

### 가치 지표 (Value) - 14개
1. **PER** - Price to Earnings Ratio
2. **PBR** - Price to Book Ratio
3. **PSR** - Price to Sales Ratio
4. **PCR** - Price to Cash Flow Ratio
5. **PEG** - Price/Earnings to Growth
6. **EV_EBITDA** - Enterprise Value / EBITDA
7. **EV_SALES** - Enterprise Value / Sales
8. **EV_FCF** - Enterprise Value / Free Cash Flow
9. **DIVIDEND_YIELD** - 배당수익률
10. **EARNINGS_YIELD** - 이익수익률 (E/P)
11. **FCF_YIELD** - FCF 수익률
12. **BOOK_TO_MARKET** - B/M 비율
13. **CAPE_RATIO** - Cyclically Adjusted PE
14. **PTBV** - Price to Tangible Book Value

### 수익성 지표 (Quality) - 10개
15. **ROE** - Return on Equity
16. **ROA** - Return on Assets
17. **ROIC** - Return on Invested Capital
18. **GPM** - Gross Profit Margin
19. **OPM** - Operating Profit Margin
20. **NPM** - Net Profit Margin
21. **ASSET_TURNOVER** - 자산회전율
22. **INVENTORY_TURNOVER** - 재고회전율
23. **QUALITY_SCORE** - Piotroski F-Score
24. **ACCRUALS_RATIO** - 발생액 비율

### 성장성 지표 (Growth) - 8개
25. **REVENUE_GROWTH_1Y** - 매출성장률 (1년)
26. **REVENUE_GROWTH_3Y** - 매출성장률 (3년 CAGR)
27. **EARNINGS_GROWTH_1Y** - 이익성장률 (1년)
28. **EARNINGS_GROWTH_3Y** - 이익성장률 (3년 CAGR)
29. **OCF_GROWTH_1Y** - 영업현금흐름 성장률
30. **ASSET_GROWTH_1Y** - 자산성장률
31. **BOOK_VALUE_GROWTH_1Y** - 장부가치 성장률
32. **SUSTAINABLE_GROWTH_RATE** - 지속가능성장률

### 모멘텀 지표 (Momentum) - 8개
33. **MOMENTUM_1M** - 1개월 모멘텀
34. **MOMENTUM_3M** - 3개월 모멘텀
35. **MOMENTUM_6M** - 6개월 모멘텀
36. **MOMENTUM_12M** - 12개월 모멘텀
37. **DISTANCE_FROM_52W_HIGH** - 52주 최고가 대비
38. **DISTANCE_FROM_52W_LOW** - 52주 최저가 대비
39. **RELATIVE_STRENGTH** - 시장 대비 상대강도
40. **VOLUME_MOMENTUM** - 거래량 모멘텀

### 안정성 지표 (Stability) - 8개
41. **DEBT_TO_EQUITY** - 부채비율
42. **DEBT_RATIO** - 부채/자산 비율
43. **CURRENT_RATIO** - 유동비율
44. **QUICK_RATIO** - 당좌비율
45. **INTEREST_COVERAGE** - 이자보상배율
46. **ALTMAN_Z_SCORE** - 부도예측 점수
47. **BETA** - 베타 (시장민감도)
48. **EARNINGS_QUALITY** - 이익의 질 (OCF/NI)

### 기술적 지표 (Technical) - 6개
49. **RSI_14** - Relative Strength Index
50. **BOLLINGER_POSITION** - 볼린저밴드 위치
51. **MACD_SIGNAL** - MACD 시그널
52. **STOCHASTIC_14** - 스토캐스틱
53. **VOLUME_ROC** - 거래량 변화율
54. **PRICE_POSITION** - 가격 위치 (0-100)

## 🚀 사용 예시

### 1. 논리식 조건으로 백테스트

```python
from app.services.backtest import BacktestEngineGenPort

# 백테스트 엔진 생성
engine = BacktestEngineGenPort(db)

# 논리식 조건 설정 (54개 팩터 모두 사용 가능)
buy_conditions = {
    "expression": "(A and B and C) or (D and E)",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 30},
        {"id": "D", "factor": "MOMENTUM_3M", "operator": ">", "value": 20},
        {"id": "E", "factor": "QUALITY_SCORE", "operator": ">=", "value": 7}
    ],
    "factor_weights": {
        "PER": -1,        # 낮을수록 좋음
        "ROE": 1,         # 높을수록 좋음
        "DEBT_RATIO": -1, # 낮을수록 좋음
        "MOMENTUM_3M": 1, # 높을수록 좋음
        "QUALITY_SCORE": 1 # 높을수록 좋음
    }
}

# 백테스트 실행
result = await engine.run_backtest(
    backtest_id=uuid4(),
    buy_conditions=buy_conditions,
    sell_conditions=[
        {"type": "STOP_LOSS", "value": 10},
        {"type": "TAKE_PROFIT", "value": 20}
    ],
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31),
    initial_capital=100_000_000,
    rebalance_frequency="MONTHLY",
    max_positions=20
)
```

### 2. 복합 전략 예시

#### Value + Quality 전략
```python
buy_conditions = {
    "expression": "A and B and C and D",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 10},
        {"id": "B", "factor": "PBR", "operator": "<", "value": 1},
        {"id": "C", "factor": "ROE", "operator": ">", "value": 15},
        {"id": "D", "factor": "QUALITY_SCORE", "operator": ">=", "value": 7}
    ]
}
```

#### Growth + Momentum 전략
```python
buy_conditions = {
    "expression": "(A and B) or (C and D)",
    "conditions": [
        {"id": "A", "factor": "REVENUE_GROWTH_3Y", "operator": ">", "value": 15},
        {"id": "B", "factor": "EARNINGS_GROWTH_3Y", "operator": ">", "value": 20},
        {"id": "C", "factor": "MOMENTUM_6M", "operator": ">", "value": 30},
        {"id": "D", "factor": "RSI_14", "operator": "BETWEEN", "value": [30, 70]}
    ]
}
```

#### Low Risk + Dividend 전략
```python
buy_conditions = {
    "expression": "A and B and C and D and E",
    "conditions": [
        {"id": "A", "factor": "BETA", "operator": "<", "value": 1},
        {"id": "B", "factor": "DEBT_RATIO", "operator": "<", "value": 30},
        {"id": "C", "factor": "CURRENT_RATIO", "operator": ">", "value": 2},
        {"id": "D", "factor": "DIVIDEND_YIELD", "operator": ">", "value": 3},
        {"id": "E", "factor": "ALTMAN_Z_SCORE", "operator": ">", "value": 3}
    ]
}
```

## 🔧 통합 아키텍처

```
┌──────────────────┐
│  backtest.py     │
│  (메인 엔진)     │
└────────┬─────────┘
         │
         ▼ 사용
┌──────────────────────┐
│ factor_integration.py│
│   (통합 모듈)        │
└─────┬────────┬───────┘
      │        │
      ▼        ▼
┌──────────┐ ┌─────────────────┐
│condition_│ │factor_calculator│
│evaluator │ │_complete.py     │
│.py       │ │(54개 팩터)      │
└──────────┘ └─────────────────┘
```

## 📈 성능 개선

### Before (13개 팩터)
- 제한된 전략 구성
- 단순한 조건만 가능
- 기본적인 팩터만 사용

### After (54개 팩터)
- ✅ **다양한 전략**: Value, Growth, Momentum, Quality 모두 가능
- ✅ **복합 조건**: 논리식으로 복잡한 조건 구성
- ✅ **전문 지표**: Altman Z-Score, Piotroski F-Score 등
- ✅ **기술적 분석**: RSI, MACD, Bollinger 등 기술적 지표

## ⚙️ 설정 및 실행

### 1. 데이터베이스 테이블 생성
```bash
# 확장 테이블 생성 (필요시)
python scripts/create_extended_backtest_tables.py
```

### 2. API 서버 실행
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. 백테스트 요청
```bash
curl -X POST "http://localhost:8000/api/v1/backtest/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "buy_expression": {
      "expression": "(A and B) or C",
      "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "ROE", "operator": ">", "value": 10},
        {"id": "C", "factor": "MOMENTUM_3M", "operator": ">", "value": 20}
      ]
    },
    "sell_conditions": [
      {"type": "STOP_LOSS", "value": 10}
    ],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000000
  }'
```

## ✅ 최종 상태

- **백테스트 엔진**: 54개 팩터와 완전 통합 ✅
- **조건 평가**: 논리식 지원 ✅
- **팩터 스코어링**: 가중치 기반 순위 ✅
- **데이터 저장**: 모든 결과 DB 저장 ✅

**통합 완료! 이제 GenPort 수준의 전문적인 퀀트 백테스트가 가능합니다.**