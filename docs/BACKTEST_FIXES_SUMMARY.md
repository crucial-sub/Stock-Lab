# 백테스트 수정 내역 총정리

## 문제 발견 경로
1. 사용자: "백테스트 에러났는데"
2. API 필드명 불일치 발견 (snake_case vs camelCase)
3. 팩터 값이 정규화되어 조건 비교 불가
4. 문자열 '증권' → float 변환 에러
5. 리밸런싱이 작동하지 않음
6. 결과 조회 시 validation 에러

## 수정한 파일들

### 1. `/Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end/app/api/routes/backtest.py`

#### 수정 1: API 응답 필드명 camelCase 추가
```python
# Line 139-150: BacktestResultStatistics
class BacktestResultStatistics(BaseModel):
    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: float = Field(..., serialization_alias="maxDrawdown")
    volatility: float = Field(..., serialization_alias="volatility")
    sharpe_ratio: float = Field(..., serialization_alias="sharpeRatio")
    win_rate: float = Field(..., serialization_alias="winRate")
    profit_factor: float = Field(..., serialization_alias="profitFactor")
    total_trades: int = Field(..., serialization_alias="totalTrades")
    winning_trades: int = Field(..., serialization_alias="winningTrades")
    losing_trades: int = Field(..., serialization_alias="losingTrades")
    initial_capital: float = Field(..., serialization_alias="initialCapital")  # int → float
    final_capital: float = Field(..., serialization_alias="finalCapital")      # int → float
```

#### 수정 2: BacktestTrade 필드명
```python
# Line 153-164
class BacktestTrade(BaseModel):
    stock_name: str = Field(..., serialization_alias="stockName")
    stock_code: str = Field(..., serialization_alias="stockCode")
    buy_price: float = Field(..., serialization_alias="buyPrice")
    sell_price: float = Field(..., serialization_alias="sellPrice")
    profit: float = Field(..., serialization_alias="profit")
    profit_rate: float = Field(..., serialization_alias="profitRate")
    buy_date: str = Field(..., serialization_alias="buyDate")
    sell_date: str = Field(..., serialization_alias="sellDate")
    weight: float = Field(..., serialization_alias="weight")
    valuation: float = Field(..., serialization_alias="valuation")
```

### 2. `/Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end/app/services/backtest.py`

#### 수정 1: 팩터 정규화 비활성화 (Line 807-810)
```python
if not factor_df.empty:
    # 팩터 순위 계산 (정규화는 스킵 - 원본 값 사용)
    # factor_df = self._normalize_factors(factor_df)  # 정규화 비활성화
    factor_df = self._calculate_factor_ranks(factor_df)
```

**이유**: 정규화하면 PBR 값이 -0.4 ~ 0.2 같은 z-score로 변환됨.
사용자가 "PBR >= 3.0" 같은 조건을 입력하면 절대 만족 안됨.

#### 수정 2: 문자열 컬럼 float 변환 에러 수정 (Line 1674-1692)
```python
# 거래 시점 팩터 값 추출
trade_factors = {}
if factor_data is not None and not factor_data.empty:
    stock_mask = factor_data['stock_code'] == stock_code
    date_mask = pd.to_datetime(factor_data['date']) == pd.Timestamp(trading_day)
    stock_factors = factor_data[stock_mask & date_mask]
    if not stock_factors.empty:
        # 메타데이터 컬럼 (문자열 타입) 제외
        meta_columns = {'date', 'stock_code', 'industry', 'size_bucket', 'market_type'}
        for col in stock_factors.columns:
            if col in meta_columns or col.endswith('_RANK'):
                continue
            value = stock_factors[col].iloc[0]
            if pd.notna(value):
                try:
                    trade_factors[col] = float(value)
                except (ValueError, TypeError):
                    # 숫자로 변환 불가능한 값은 스킵
                    continue
```

**이유**: 'industry' 컬럼의 '증권' 문자열을 float()로 변환하려다가 에러

#### 수정 3: 리밸런싱 로직 수정 (Line 1196-1273)
```python
# 리밸런싱 체크 (매수는 리밸런싱 날짜에만)
if pd.Timestamp(trading_day) in [pd.Timestamp(d) for d in rebalance_dates]:
    # 1단계: 리밸런싱 - 조건 불만족 종목 매도
    from app.services.factor_integration import FactorIntegration
    factor_integrator = FactorIntegration(self.db)

    # 현재 보유 종목 중 조건 만족하는 종목 확인
    if holdings:
        holding_stocks = list(holdings.keys())
        valid_holdings = factor_integrator.evaluate_buy_conditions_with_factors(
            factor_data=factor_data,
            stock_codes=holding_stocks,
            buy_conditions=buy_conditions,
            trading_date=pd.Timestamp(trading_day)
        )

        # 조건 불만족 종목 매도
        stocks_to_sell = [stock for stock in holding_stocks if stock not in valid_holdings]
        for stock_code in stocks_to_sell:
            # ... 매도 실행 로직
            logger.info(f"🔄 리밸런싱 매도: {stock_code} (조건 불만족)")

    # 2단계: 매수 종목 선정
    buy_candidates = await self._select_buy_candidates(...)

    # 이미 보유 중인 종목은 매수 후보에서 제외 (리밸런싱에서는 유지)
    new_buy_candidates = [s for s in buy_candidates if s not in holdings]

    logger.info(f"💰 매수 후보(전체): {len(buy_candidates)}개")
    logger.info(f"💰 매수 후보(신규): {len(new_buy_candidates)}개")
    logger.info(f"💼 현재 보유: {len(holdings)}개")

    buy_candidates = new_buy_candidates
```

**문제**: 기존 로직은 보유 종목을 절대 재평가 안하고, 매수 후보에서도 제외함
**해결**:
1. 리밸런싱 시 보유 종목 재평가
2. 조건 불만족 → 매도
3. 신규 종목만 매수 후보로 선정

#### 수정 4: _select_buy_candidates에서 보유 종목 제외 제거 (Line 1467-1477)
```python
# 거래 가능한 종목 필터링
tradeable_stocks = price_data[
    (price_data['date'] == trading_day) &
    (price_data['volume'] > 0) &
    (price_data['close_price'] > 0)
]['stock_code'].unique().tolist()

# 리밸런싱 시에는 보유 종목도 재평가해야 하므로 제외하지 않음
# (기존 로직: tradeable_stocks = [s for s in tradeable_stocks if s not in holdings])
# 포지션 사이징에서 available_slots로 신규 매수 수량 제한
```

**문제**: 보유 종목을 아예 평가 대상에서 제외
**해결**: 보유 종목도 평가 대상에 포함, 대신 매수 실행 시에만 제외

#### 수정 5: Timestamp 타입 불일치 수정 (Line 2184)
```python
hold_days=(pd.Timestamp(latest_date).date() -
           (holding.entry_date.date() if hasattr(holding.entry_date, 'date')
            else holding.entry_date)).days if latest_date else 0
```

**이유**: datetime.date - Timestamp 연산 불가

### 3. `/Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end/app/services/factor_integration.py`

#### 수정 1: 대소문자 구분 없이 팩터 검색 (Line 130-140)
```python
for condition in buy_conditions:
    factor_name = condition['factor']
    operator = condition['operator']
    threshold = condition['value']

    # 대소문자 구분 없이 팩터 값 가져오기
    factor_name_upper = factor_name.upper()

    if factor_name_upper in stock_data.columns:
        factor_value = float(stock_data[factor_name_upper].iloc[0])
        logger.debug(f"종목 {stock_code}: {factor_name_upper} = {factor_value} {operator} {threshold}")
    elif f"{factor_name_upper}_RANK" in stock_data.columns:
        factor_value = float(stock_data[f"{factor_name_upper}_RANK"].iloc[0])
        logger.debug(f"종목 {stock_code}: {factor_name_upper}_RANK = {factor_value} {operator} {threshold}")
    else:
        logger.debug(f"종목 {stock_code}: {factor_name_upper} 팩터 없음 ...")
```

**이유**: 조건에서 'pbr' 소문자 사용, DataFrame에는 'PBR' 대문자 존재

#### 수정 2: 디버그 로그 추가 (Line 113-120)
```python
# 디버그: 첫 번째 종목의 팩터 데이터 확인
if stock_codes and not factor_data.empty:
    first_stock = stock_codes[0]
    stock_mask = (factor_data['stock_code'] == first_stock)
    date_mask = (pd.to_datetime(factor_data['date']) == trading_date)
    sample_data = factor_data[stock_mask & date_mask]
    if not sample_data.empty:
        logger.info(f"📊 샘플 종목 {first_stock} 팩터 데이터: {sample_data.iloc[0].to_dict()}")
```

## 검증 결과

### ✅ 해결된 문제
1. API 필드명 불일치 → camelCase serialization_alias 추가
2. 팩터 정규화 문제 → 정규화 비활성화
3. 문자열 float 변환 에러 → meta_columns 제외 + try-except
4. 리밸런싱 미작동 → 보유 종목 재평가 로직 추가
5. capital 타입 에러 → int → float 변경

### ⚠️ 알려진 제약사항
1. **PER 값 NaN 문제**: 증권 종목들의 net_income이 음수라 PER 계산 불가
   - 이는 데이터 문제이지 로직 문제 아님
   - 해결방안: PER 조건 제거 또는 다른 팩터 사용

### 🧪 테스트 결과
- 삼성전자 단독 테스트: ✅ 성공
  - 첫 리밸런싱: 매수 성공
  - 이후 리밸런싱: 조건 만족 → 보유 유지
  - 최종 수익률: -28.23% (삼성전자 실제 하락 반영)

## 추가 권장사항

### 단순화 필요
현재 너무 많은 수정이 들어가서 복잡합니다. 다음 단계 권장:

1. **디버그 로그 정리**: 샘플 데이터 출력 로그는 production에서 제거
2. **테스트 코드 정리**: test_backtest_verification.py, test_samsung_only.py 정리
3. **문서화**: 각 수정사항의 근거와 영향 범위 명확히 문서화

### 검토 필요 사항
1. 리밸런싱 로직이 이제 너무 복잡함 → 단순화 고려
2. factor_integration 2번 호출 (보유 종목 재평가 + 신규 종목 선정) → 성능 이슈?
3. 전체 백테스트 플로우 재검증 필요
