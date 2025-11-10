# 팩터 테이블 설계 문서

## 1. 팩터 마스터 테이블 (factor_master)

```sql
CREATE TABLE factor_master (
    factor_id SERIAL PRIMARY KEY,
    factor_code VARCHAR(50) UNIQUE NOT NULL,  -- 'PER', 'PBR', 'ROE' 등
    factor_name VARCHAR(100) NOT NULL,        -- '주가수익비율', '주가순자산비율' 등
    factor_category VARCHAR(50),              -- 'VALUE', 'GROWTH', 'MOMENTUM' 등
    description TEXT,
    calculation_method TEXT,                  -- 계산 방법 설명
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. 일별 팩터 값 테이블 (daily_factor_values)

```sql
CREATE TABLE daily_factor_values (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    factor_id INTEGER REFERENCES factor_master(factor_id),
    trade_date DATE NOT NULL,
    factor_value DECIMAL(20, 6),
    factor_rank INTEGER,                      -- 해당 날짜의 팩터 순위
    factor_percentile DECIMAL(5, 2),          -- 백분위 (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_code, factor_id, trade_date),
    INDEX idx_factor_date (factor_id, trade_date),
    INDEX idx_stock_date (stock_code, trade_date)
);
```

## 3. 팩터 스코어 테이블 (factor_scores)

종목별 종합 팩터 스코어를 저장하는 테이블

```sql
CREATE TABLE factor_scores (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    composite_score DECIMAL(10, 6),           -- 종합 팩터 스코어
    value_score DECIMAL(10, 6),               -- 가치 팩터 스코어
    growth_score DECIMAL(10, 6),              -- 성장 팩터 스코어
    momentum_score DECIMAL(10, 6),             -- 모멘텀 팩터 스코어
    quality_score DECIMAL(10, 6),             -- 퀄리티 팩터 스코어
    score_rank INTEGER,                       -- 종합 스코어 순위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_code, trade_date),
    INDEX idx_date_score (trade_date, composite_score DESC)
);
```

## 4. 백테스트 팩터 조건 테이블 (backtest_factor_conditions)

각 백테스트에서 사용된 팩터 조건을 저장

```sql
CREATE TABLE backtest_factor_conditions (
    id SERIAL PRIMARY KEY,
    backtest_id UUID NOT NULL,
    condition_type VARCHAR(10),               -- 'BUY' or 'SELL'
    factor_id INTEGER REFERENCES factor_master(factor_id),
    operator VARCHAR(10),                     -- '<', '>', '<=', '>=', '=', '!='
    threshold_value DECIMAL(20, 6),
    condition_order INTEGER,                  -- 조건 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_backtest (backtest_id)
);
```

## 5. 백테스트 팩터 스냅샷 테이블 (backtest_factor_snapshots)

백테스트 시점의 팩터 값 스냅샷 저장 (재현성 보장)

```sql
CREATE TABLE backtest_factor_snapshots (
    id SERIAL PRIMARY KEY,
    backtest_id UUID NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    factor_values JSONB,                      -- 모든 팩터 값을 JSON으로 저장
    selection_reason TEXT,                     -- 종목 선정 이유
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_backtest_date (backtest_id, trade_date)
);
```

## 팩터 테이블 활용 예시

### 1. 팩터 값 조회 (특정 날짜, 특정 팩터)

```python
async def get_factor_values(
    date: datetime.date,
    factor_code: str,
    top_n: int = 20
) -> List[FactorValue]:
    query = """
        SELECT
            dfv.stock_code,
            s.stock_name,
            dfv.factor_value,
            dfv.factor_rank,
            dfv.factor_percentile
        FROM daily_factor_values dfv
        JOIN stocks s ON dfv.stock_code = s.stock_code
        JOIN factor_master fm ON dfv.factor_id = fm.factor_id
        WHERE dfv.trade_date = :date
          AND fm.factor_code = :factor_code
          AND dfv.factor_rank <= :top_n
        ORDER BY dfv.factor_rank
    """
    # ... 실행 로직
```

### 2. 복합 팩터 조건으로 종목 선정

```python
async def select_stocks_by_factors(
    date: datetime.date,
    conditions: List[FactorCondition]
) -> List[str]:
    # 동적 쿼리 생성
    query = """
        WITH factor_data AS (
            SELECT
                stock_code,
                MAX(CASE WHEN fm.factor_code = 'PER' THEN factor_value END) as per,
                MAX(CASE WHEN fm.factor_code = 'PBR' THEN factor_value END) as pbr,
                MAX(CASE WHEN fm.factor_code = 'ROE' THEN factor_value END) as roe
            FROM daily_factor_values dfv
            JOIN factor_master fm ON dfv.factor_id = fm.factor_id
            WHERE trade_date = :date
            GROUP BY stock_code
        )
        SELECT stock_code
        FROM factor_data
        WHERE 1=1
    """

    # 조건 추가
    for condition in conditions:
        query += f" AND {condition.factor_code} {condition.operator} {condition.value}"

    # ... 실행 로직
```

### 3. 팩터 업데이트 배치 작업

```python
async def update_daily_factors(date: datetime.date):
    """매일 실행되는 팩터 계산 배치 작업"""

    # 1. 재무 데이터 가져오기
    financial_data = await fetch_financial_data(date)

    # 2. 가격 데이터 가져오기
    price_data = await fetch_price_data(date)

    # 3. 팩터별 계산
    factors = {
        'PER': calculate_per(financial_data, price_data),
        'PBR': calculate_pbr(financial_data, price_data),
        'ROE': calculate_roe(financial_data),
        'MOMENTUM_1M': calculate_momentum(price_data, period=20),
        # ... 기타 팩터들
    }

    # 4. DB에 저장
    for factor_code, values in factors.items():
        await save_factor_values(date, factor_code, values)

    # 5. 순위 및 백분위 계산
    await calculate_factor_ranks(date)

    # 6. 종합 스코어 계산
    await calculate_composite_scores(date)
```

## 팩터 테이블의 장점

1. **성능 향상**
   - 백테스트 실행 시간 단축 (팩터 재계산 불필요)
   - 인덱스를 통한 빠른 조회

2. **데이터 품질**
   - 일관된 팩터 값 보장
   - 팩터 계산 오류 사전 감지 가능

3. **분석 기능 강화**
   - 팩터 백테스팅 (factor backtesting) 가능
   - 팩터 타이밍 전략 구현 가능
   - 팩터 모멘텀 분석 가능

4. **확장성**
   - 새로운 팩터 추가 용이
   - 커스텀 팩터 정의 가능
   - 팩터 조합 실험 용이

## 구현 우선순위

1. **Phase 1**: 기본 팩터 테이블 생성
   - factor_master 테이블
   - daily_factor_values 테이블
   - 기본 팩터 계산 로직

2. **Phase 2**: 팩터 스코어링
   - factor_scores 테이블
   - 종합 스코어 계산 로직
   - 순위 계산 로직

3. **Phase 3**: 백테스트 통합
   - backtest_factor_conditions 테이블
   - backtest_factor_snapshots 테이블
   - 백테스트 엔진 수정

4. **Phase 4**: 최적화
   - 인덱스 튜닝
   - 파티셔닝 (날짜별)
   - 캐싱 전략