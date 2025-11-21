# 150개 팩터 전체 정의
**작성일**: 2025-11-22
**목적**: 모든 팩터를 표준 경로 + 최적화 경로에 구현

---

## 팩터 분류 및 총 개수

### 1. 가치 지표 (Valuation) - 15개
1. PER (Price to Earnings Ratio)
2. PBR (Price to Book Ratio)
3. PSR (Price to Sales Ratio)
4. PCR (Price to Cashflow Ratio)
5. PEG (PER to Growth Ratio)
6. DIVIDEND_YIELD (배당수익률)
7. EARNINGS_YIELD (이익수익률 = 1/PER)
8. FCF_YIELD (잉여현금흐름 수익률)
9. EV (Enterprise Value - 기업가치)
10. EV_EBITDA (EV / EBITDA)
11. EV_EBIT (EV / EBIT)
12. EV_SALES (EV / Sales)
13. BOOK_TO_MARKET (PBR의 역수)
14. SALES_TO_PRICE (PSR의 역수)
15. CASH_TO_PRICE (PCR의 역수)

### 2. 수익성 지표 (Profitability) - 15개
16. ROE (자기자본이익률)
17. ROA (총자산이익률)
18. ROIC (투자자본수익률)
19. GPM (매출총이익률)
20. OPM (영업이익률)
21. NPM (순이익률)
22. EBITDA_MARGIN (EBITDA 마진)
23. EBIT_MARGIN (EBIT 마진)
24. GROSS_PROFIT_MARGIN (매출총이익률 - GPM과 동일)
25. OPERATING_MARGIN (영업이익률 - OPM과 동일)
26. NET_MARGIN (순이익률 - NPM과 동일)
27. ASSET_TURNOVER (자산회전율)
28. EQUITY_MULTIPLIER (자기자본승수)
29. OCF_RATIO (영업현금흐름비율)
30. FCF_MARGIN (잉여현금흐름 마진)

### 3. 재무 건전성 (Financial Health) - 20개
31. DEBT_RATIO (부채비율)
32. DEBT_TO_EQUITY (부채/자본 비율)
33. EQUITY_RATIO (자기자본비율)
34. CURRENT_RATIO (유동비율)
35. QUICK_RATIO (당좌비율)
36. CASH_RATIO (현금비율)
37. INTEREST_COVERAGE (이자보상배율)
38. WORKING_CAPITAL_RATIO (운전자본비율)
39. ALTMAN_Z_SCORE (알트만 Z 스코어)
40. DEBT_TO_ASSETS (부채/자산 비율)
41. EQUITY_TO_ASSETS (자본/자산 비율)
42. LONG_TERM_DEBT_RATIO (장기부채비율)
43. SHORT_TERM_DEBT_RATIO (단기부채비율)
44. DEBT_SERVICE_COVERAGE (부채상환능력비율)
45. CASH_DEBT_COVERAGE (현금부채비율)
46. NET_DEBT (순부채)
47. NET_DEBT_TO_EQUITY (순부채/자본)
48. NET_DEBT_TO_EBITDA (순부채/EBITDA)
49. TANGIBLE_EQUITY_RATIO (유형자본비율)
50. LIABILITIES_TO_EQUITY (부채/자본)

### 4. 성장성 지표 (Growth) - 20개
51. REVENUE_GROWTH_1Y (1년 매출 성장률)
52. REVENUE_GROWTH_3Y (3년 매출 CAGR)
53. REVENUE_GROWTH_5Y (5년 매출 CAGR)
54. EARNINGS_GROWTH_1Y (1년 순이익 성장률)
55. EARNINGS_GROWTH_3Y (3년 순이익 CAGR)
56. EARNINGS_GROWTH_5Y (5년 순이익 CAGR)
57. OPERATING_INCOME_GROWTH (영업이익 성장률)
58. GROSS_PROFIT_GROWTH (매출총이익 성장률)
59. ASSET_GROWTH_1Y (1년 자산 성장률)
60. EQUITY_GROWTH_1Y (1년 자본 성장률)
61. EPS_GROWTH_1Y (1년 주당순이익 성장률)
62. BPS_GROWTH_1Y (1년 주당순자산 성장률)
63. SALES_GROWTH_QOQ (전분기 대비 매출 성장률)
64. EARNINGS_GROWTH_QOQ (전분기 대비 순이익 성장률)
65. OCF_GROWTH_1Y (영업현금흐름 성장률)
66. FCF_GROWTH_1Y (잉여현금흐름 성장률)
67. DIVIDEND_GROWTH_1Y (배당 성장률)
68. REVENUE_GROWTH_RATE (평균 매출 성장률)
69. EARNINGS_GROWTH_RATE (평균 순이익 성장률)
70. SUSTAINABLE_GROWTH_RATE (지속가능 성장률)

### 5. 효율성 지표 (Efficiency) - 10개
71. INVENTORY_TURNOVER (재고자산회전율)
72. RECEIVABLES_TURNOVER (매출채권회전율)
73. PAYABLES_TURNOVER (매입채무회전율)
74. FIXED_ASSET_TURNOVER (고정자산회전율)
75. TOTAL_ASSET_TURNOVER (총자산회전율)
76. WORKING_CAPITAL_TURNOVER (운전자본회전율)
77. DAYS_INVENTORY_OUTSTANDING (재고회전일수)
78. DAYS_SALES_OUTSTANDING (매출채권회전일수)
79. DAYS_PAYABLE_OUTSTANDING (매입채무회전일수)
80. CASH_CONVERSION_CYCLE (현금전환주기)

### 6. 현금흐름 지표 (Cash Flow) - 10개
81. OCF (영업활동현금흐름)
82. ICF (투자활동현금흐름)
83. FCF (잉여현금흐름)
84. OCF_TO_SALES (영업현금흐름/매출)
85. FCF_TO_SALES (잉여현금흐름/매출)
86. OCF_TO_NET_INCOME (영업현금흐름/순이익)
87. CAPEX_TO_SALES (자본지출/매출)
88. CAPEX_TO_OCF (자본지출/영업현금흐름)
89. FREE_CASHFLOW_TO_EQUITY (주주잉여현금흐름)
90. CASH_RETURN_ON_ASSETS (현금자산수익률)

### 7. 모멘텀 지표 (Momentum) - 10개
91. MOMENTUM_1M (1개월 모멘텀)
92. MOMENTUM_3M (3개월 모멘텀)
93. MOMENTUM_6M (6개월 모멘텀)
94. MOMENTUM_12M (12개월 모멘텀)
95. PRICE_MOMENTUM (가격 모멘텀)
96. EARNINGS_MOMENTUM (이익 모멘텀)
97. REVENUE_MOMENTUM (매출 모멘텀)
98. DISTANCE_FROM_52W_HIGH (52주 고가 대비 거리)
99. DISTANCE_FROM_52W_LOW (52주 저가 대비 거리)
100. PRICE_POSITION (52주 가격 포지션)

### 8. 변동성 지표 (Volatility) - 10개
101. VOLATILITY_20D (20일 변동성)
102. VOLATILITY_60D (60일 변동성)
103. VOLATILITY_90D (90일 변동성)
104. BETA (베타)
105. STANDARD_DEVIATION (표준편차)
106. DOWNSIDE_DEVIATION (하방편차)
107. MAX_DRAWDOWN (최대낙폭)
108. SHARPE_RATIO (샤프비율)
109. SORTINO_RATIO (소르티노비율)
110. CALMAR_RATIO (칼마비율)

### 9. 거래량 지표 (Volume) - 10개
111. AVG_TRADING_VALUE (평균 거래대금)
112. TURNOVER_RATE (회전율)
113. VOLUME_RATIO_20D (20일 거래량 비율)
114. TRADING_VOLUME (거래량)
115. DOLLAR_VOLUME (거래대금)
116. LIQUIDITY_RATIO (유동성 비율)
117. AMIHUD_ILLIQUIDITY (아미후드 비유동성)
118. VOLUME_MOMENTUM (거래량 모멘텀)
119. RELATIVE_VOLUME (상대 거래량)
120. TRADING_FREQUENCY (거래 빈도)

### 10. 기술적 지표 (Technical) - 15개
121. RSI_14 (14일 RSI)
122. RSI_28 (28일 RSI)
123. MACD (MACD)
124. MACD_SIGNAL (MACD 시그널)
125. MACD_HISTOGRAM (MACD 히스토그램)
126. BOLLINGER_POSITION (볼린저 밴드 포지션)
127. BOLLINGER_WIDTH (볼린저 밴드 폭)
128. STOCHASTIC_14 (14일 스토캐스틱)
129. VOLUME_ROC (거래량 변화율)
130. PRICE_TO_MA_20 (20일 이동평균 대비 가격)
131. PRICE_TO_MA_60 (60일 이동평균 대비 가격)
132. PRICE_TO_MA_200 (200일 이동평균 대비 가격)
133. MA_20_50_CROSS (20일/50일 이평선 교차)
134. MA_50_200_CROSS (50일/200일 이평선 교차)
135. ADX (Average Directional Index)

### 11. 품질 지표 (Quality) - 10개
136. ACCRUALS_RATIO (발생액 비율)
137. EARNINGS_QUALITY (이익 품질)
138. QUALITY_SCORE (품질 점수)
139. LEVERAGE (레버리지)
140. PIOTROSKI_F_SCORE (피오트로스키 F 스코어)
141. ALTMAN_Z (알트만 Z - 간소화)
142. BENEISH_M_SCORE (베니시 M 스코어)
143. OPERATING_CASH_FLOW_RATIO (영업현금흐름비율)
144. ASSET_QUALITY (자산 품질)
145. EARNINGS_PERSISTENCE (이익 지속성)

### 12. 기타 지표 (Others) - 5개
146. MARKET_CAP (시가총액)
147. ENTERPRISE_VALUE (기업가치)
148. SHARES_OUTSTANDING (발행주식수)
149. FLOAT_SHARES (유동주식수)
150. CHANGE_RATE (일별 변화율)

---

## 구현 우선순위

### Phase 1: 최우선 팩터 (전략 사용 빈도 4회 이상) - 6개
1. FCF_YIELD (4회)
2. CURRENT_RATIO (4회)
3. DIVIDEND_YIELD (3회)
4. PER (8회) - ✅ 완료
5. DEBT_RATIO (7회) - ✅ 완료
6. PBR (6회) - ✅ 완료

### Phase 2: 핵심 팩터 (전략 사용 빈도 2-3회) - 10개 ✅ 완료
7. ROE (5회) - ✅ 완료
8. PSR (2회) - ✅ 완료
9. OPERATING_INCOME_GROWTH (2회) - ✅ 완료
10. GROSS_PROFIT_GROWTH (1회) - ✅ 완료
11. REVENUE_GROWTH_1Y (2회) - ✅ 완료
12. EARNINGS_GROWTH_1Y (3회) - ✅ 완료
13. OPERATING_MARGIN (이미 구현됨) - ✅ 완료
14. NET_MARGIN (이미 구현됨) - ✅ 완료
15. ROA (1회) - ✅ 완료
16. GPM - ✅ 완료
17. NPM - ✅ 완료
18. QUICK_RATIO - ✅ 완료
19. CASH_RATIO - ✅ 완료
20. DEBT_TO_EQUITY - ✅ 완료
21. EQUITY_RATIO - ✅ 완료
22. INTEREST_COVERAGE - ✅ 완료
23. WORKING_CAPITAL_RATIO - ✅ 완료
24. OCF_RATIO - ✅ 완료
25. ASSET_TURNOVER - ✅ 완료

**Phase 2 완료 (2025-11-22): 표준 경로 + 최적화 경로 모두 구현됨**

### Phase 3: 표준 팩터 세트 (기본 팩터 세트에 있는 것들) - 30개 ✅ 완료
- 가치: PCR ✅, EARNINGS_YIELD ✅, BOOK_TO_MARKET ✅, EV_SALES ✅, EV_EBITDA ✅
- 수익성: GPM ✅, OPM ✅, NPM ✅, ASSET_TURNOVER ✅, EQUITY_MULTIPLIER ✅, OCF_RATIO ✅
- 건전성: QUICK_RATIO ✅, CASH_RATIO ✅, DEBT_TO_EQUITY ✅, INTEREST_COVERAGE ✅, WORKING_CAPITAL_RATIO ✅, EQUITY_RATIO ✅
- 성장성: REVENUE_GROWTH_3Y ✅, EARNINGS_GROWTH_3Y ✅, ASSET_GROWTH_1Y ✅, EQUITY_GROWTH_1Y ✅
- 모멘텀: MOMENTUM_1M ✅, MOMENTUM_6M ✅, MOMENTUM_12M ✅, DISTANCE_FROM_52W_HIGH ✅, DISTANCE_FROM_52W_LOW ✅, PRICE_POSITION ✅
- 변동성: VOLATILITY_20D ✅, VOLATILITY_60D ✅, VOLATILITY_90D ✅
- 거래량: AVG_TRADING_VALUE ✅, TURNOVER_RATE ✅, VOLUME_RATIO_20D ✅
- 기술적: RSI_14 ✅, BOLLINGER_POSITION ✅, BOLLINGER_WIDTH ✅, STOCHASTIC_14 ✅, VOLUME_ROC ✅, PRICE_TO_MA_20 ✅, MACD ✅
- 품질: ACCRUALS_RATIO ✅, EARNINGS_QUALITY ✅, QUALITY_SCORE ✅, LEVERAGE ✅
- 기타: CHANGE_RATE ✅, MARKET_CAP ✅

**Phase 3 완료 (2025-11-22):
- 표준 경로: 12개 신규 팩터 추가 (PCR, EARNINGS_YIELD, BOOK_TO_MARKET, EV_SALES, EV_EBITDA, VOLATILITY_20D, VOLATILITY_60D, VOLUME_RATIO_20D, BOLLINGER_WIDTH, MACD 등)
- 최적화 경로: 10개 팩터 추가 (PCR, EARNINGS_YIELD, BOOK_TO_MARKET, EV_SALES, EV_EBITDA, VOLATILITY placeholders, VOLUME_RATIO_20D, MARKET_CAP)
- 총 구현 팩터: Phase 1 (6) + Phase 2 (19) + Phase 3 (30) = 55개**

### Phase 4: 확장 팩터 (나머지 100개)
- 모든 비율, 성장률, 회전율, 기술적 지표 완성

---

## 구현 전략

### 1. 재무 데이터 정규화 함수
```python
def normalize_account_name(raw_name: str) -> str:
    """
    다양한 형태의 계정명을 표준 이름으로 정규화
    예: "Ⅰ. 매출액", "Ⅰ.매출", "매출액" → "매출액"
    """
    pass
```

### 2. 팩터 계산 헬퍼 함수
```python
def safe_divide(numerator, denominator):
    """0으로 나누기 방지"""

def calculate_growth_rate(current, previous):
    """성장률 계산"""

def calculate_cagr(current, past, years):
    """연평균 성장률 계산"""
```

### 3. 배치 구현
- 한 번에 10-20개씩 구현
- 표준 경로 → 최적화 경로 → 기본 팩터 세트 순서
- 각 배치마다 Docker 재시작 및 테스트

---

## 다음 단계
1. ✅ 150개 팩터 목록 정의 완료
2. ⏳ Phase 1 최우선 팩터 3개 구현 (FCF_YIELD, CURRENT_RATIO, DIVIDEND_YIELD)
3. ⏳ Phase 2 핵심 팩터 10개 구현
4. ⏳ Phase 3 표준 팩터 30개 구현
5. ⏳ Phase 4 확장 팩터 100개 구현
