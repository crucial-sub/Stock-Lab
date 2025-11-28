# Stock Lab Backend 기술 아키텍처

## 목차
1. [시스템 개요](#시스템-개요)
2. [기술 스택](#기술-스택)
3. [아키텍처 설계](#아키텍처-설계)
4. [데이터베이스 설계](#데이터베이스-설계)
5. [핵심 서비스](#핵심-서비스)
6. [성능 최적화](#성능-최적화)
7. [보안](#보안)
8. [배포 및 운영](#배포-및-운영)

---

## 시스템 개요

### 프로젝트 목적
Stock Lab은 **퀀트 투자 전략 백테스팅 및 자동매매 플랫폼**으로, 개인 투자자가 데이터 기반의 투자 전략을 수립하고 실거래에 적용할 수 있도록 지원합니다.

### 핵심 기능
1. **백테스팅 엔진**: 150+ 팩터 기반 전략 검증
2. **자동매매**: 키움증권 API 연동 실거래 자동화
3. **전략 공유**: 커뮤니티 기반 전략 공유 및 랭킹
4. **AI 챗봇**: 투자 전략 상담 및 추천

### 시스템 요구사항
- **동시 사용자**: 1,000명 이상
- **백테스트 처리량**: 10년 데이터 기준 1분 이내
- **데이터 규모**: 2,000+ 종목 × 10년 × 일별 시세 (약 500만+ 레코드)
- **가용성**: 99.9% (장 시간 09:00-15:30 필수)

---

## 기술 스택

### 백엔드 프레임워크
```
FastAPI 0.109+
- 비동기 I/O 지원
- 자동 API 문서 생성 (Swagger, ReDoc)
- Pydantic 기반 데이터 검증
- WebSocket/SSE 지원
```

### 데이터베이스
```
PostgreSQL 15+
- JSONB 컬럼 지원 (유연한 전략 설정 저장)
- 파티셔닝 (시계열 데이터 분산)
- 인덱싱 최적화 (B-Tree, GIN)
- 트랜잭션 ACID 보장
```

### 캐시
```
Redis 7+
- 랭킹 데이터 (Sorted Set)
- 세션 관리 (토큰 블랙리스트)
- API 응답 캐싱 (TTL: 1분~5분)
- Pub/Sub (실시간 알림)
```

### 데이터 처리
```
Polars
- DataFrame 처리 (Pandas 대비 10배+ 빠름)
- 멀티스레드 병렬 처리
- 대용량 CSV 파싱

NumPy
- 벡터 연산
- 금융 지표 계산

Numba
- JIT 컴파일 (Python → LLVM)
- 백테스팅 핵심 로직 가속화 (10배+ 속도 향상)
```

### 외부 API
```
키움증권 Open API+
- 실시간 시세 조회
- 계좌 정보 조회
- 주문 체결 (매수/매도)

OpenDart API
- 재무제표 데이터
- 공시 정보

공공데이터포털
- 일별 시세 데이터
```

---

## 아키텍처 설계

### 1. 레이어드 아키텍처

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                 │
│  (FastAPI Routes, WebSocket, SSE)              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              Business Logic Layer               │
│  (Services, Repositories)                       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              Data Access Layer                  │
│  (SQLAlchemy ORM, Redis Client)                │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              Infrastructure Layer               │
│  (PostgreSQL, Redis, External APIs)            │
└─────────────────────────────────────────────────┘
```

### 2. 프로젝트 구조

```
SL-Back-end/
├── app/
│   ├── api/
│   │   ├── routes/           # API 엔드포인트
│   │   │   ├── auth.py       # 인증 (9개 엔드포인트)
│   │   │   ├── backtest.py   # 백테스트 (14개)
│   │   │   ├── strategy.py   # 전략 관리 (7개)
│   │   │   ├── auto_trading.py # 자동매매 (14개)
│   │   │   ├── community.py  # 커뮤니티 (16개)
│   │   │   ├── kiwoom.py     # 키움 연동 (7개)
│   │   │   ├── market_quote.py # 시세 (7개)
│   │   │   ├── news.py       # 뉴스 (9개)
│   │   │   └── ...
│   │   └── v1/               # API 버전 관리
│   │
│   ├── core/                 # 핵심 설정
│   │   ├── config.py         # 환경 변수 설정
│   │   ├── database.py       # DB 연결 풀
│   │   ├── cache.py          # Redis 클라이언트
│   │   ├── security.py       # JWT 인증/암호화
│   │   └── dependencies.py   # FastAPI 의존성 주입
│   │
│   ├── models/               # SQLAlchemy 모델 (21개)
│   │   ├── user.py           # 사용자
│   │   ├── simulation.py     # 백테스트 관련 (6개 테이블)
│   │   ├── auto_trading.py   # 자동매매
│   │   ├── community.py      # 커뮤니티
│   │   ├── company.py        # 종목 정보
│   │   ├── stock_price.py    # 시세 데이터
│   │   ├── financial_statement.py # 재무제표
│   │   └── ...
│   │
│   ├── schemas/              # Pydantic 스키마 (요청/응답 DTO)
│   │   ├── user.py
│   │   ├── strategy.py
│   │   ├── backtest.py
│   │   └── ...
│   │
│   ├── services/             # 비즈니스 로직 (35개 서비스)
│   │   ├── backtest.py                    # 백테스트 메인
│   │   ├── backtest_numba_core.py         # Numba 가속화
│   │   ├── factor_calculator_complete.py  # 150+ 팩터 계산
│   │   ├── condition_evaluator_vectorized.py # 조건 평가 (벡터화)
│   │   ├── auto_trading_scheduler.py      # 자동매매 스케줄러
│   │   ├── auto_trading_executor.py       # 주문 실행
│   │   ├── kiwoom_service.py              # 키움 API 래퍼
│   │   ├── ranking_service.py             # 랭킹 관리 (Redis)
│   │   ├── cache_warmer.py                # 캐시 워밍
│   │   └── ...
│   │
│   ├── repositories/         # 데이터 접근 계층
│   │   ├── news_repository.py
│   │   ├── theme_repository.py
│   │   └── ...
│   │
│   ├── utils/                # 유틸리티
│   │   ├── date_utils.py
│   │   ├── market_utils.py
│   │   └── ...
│   │
│   └── main.py               # FastAPI 앱 진입점
│
├── migrations/               # DB 마이그레이션 스크립트
│   ├── add_backtest_indexes_phase1.sql
│   ├── add_investment_strategies.sql
│   └── ...
│
├── scripts/                  # 관리 스크립트
│   ├── init_db.py            # DB 초기화
│   ├── cache_warming_v2.py   # 캐시 워밍
│   ├── warm_famous_strategies.py # 유명 전략 캐싱
│   └── ...
│
└── tests/                    # 테스트 코드
    ├── test_backtest.py
    ├── test_integration.py
    └── ...
```

### 3. API 엔드포인트 통계

총 **106개 엔드포인트** (15개 라우터)

| 라우터 | 엔드포인트 수 | 주요 기능 |
|--------|---------------|----------|
| auth | 9 | 회원가입, 로그인, 로그아웃, 내 정보 |
| backtest | 14 | 백테스트 실행, 상태 조회, 결과 조회, SSE |
| strategy | 7 | 내 전략, 공개 전략, 랭킹, 복제 |
| auto_trading | 14 | 자동매매 생성, 시작/중지, 상태 조회 |
| community | 16 | 게시글, 댓글, 좋아요, 검색 |
| kiwoom | 7 | 계좌 연동, 예수금, 보유 종목, 주문 |
| market_quote | 7 | 시세 조회, 차트 데이터 |
| news | 9 | 뉴스 목록, 상세, 카테고리별 |
| company_info | 2 | 종목 정보, 재무제표 |
| factors | 3 | 팩터 목록, 카테고리별 |
| universes | 3 | 유니버스, 테마, 섹터 |
| user_stock | 6 | 관심 종목, 최근 본 종목 |
| chat_history | 5 | 채팅 세션, 메시지 기록 |
| investment_strategy | 2 | 유명 전략 목록, 상세 |
| backtest_sse | 2 | SSE 스트리밍 |

---

## 데이터베이스 설계

### 1. ERD 주요 테이블

#### 사용자 관련
```sql
users (사용자)
├── user_id (PK, UUID)
├── email (UNIQUE)
├── nickname (UNIQUE)
├── phone_number (UNIQUE)
├── hashed_password
├── kiwoom_app_key
├── kiwoom_access_token
└── ai_recommendation_block
```

#### 백테스트 관련
```sql
portfolio_strategies (전략)
├── strategy_id (PK, UUID)
├── user_id (FK → users)
├── strategy_name
├── is_public (공개 여부)
├── is_anonymous (익명 여부)
└── hide_strategy_details (전략 숨김)

simulation_sessions (시뮬레이션 세션)
├── session_id (PK, UUID)
├── strategy_id (FK → portfolio_strategies)
├── user_id (FK → users)
├── status (PENDING/RUNNING/COMPLETED/FAILED)
├── start_date
├── end_date
├── initial_capital
└── is_portfolio (포트폴리오 저장 여부)

simulation_statistics (백테스트 통계)
├── stat_id (PK)
├── session_id (FK → simulation_sessions)
├── total_return (총 수익률)
├── annualized_return (연환산 수익률)
├── max_drawdown (최대 낙폭)
├── sharpe_ratio (샤프 지수)
├── volatility (변동성)
└── win_rate (승률)

simulation_daily_values (일별 자산 변동)
├── id (PK)
├── session_id (FK → simulation_sessions)
├── date
├── total_value
├── cash
└── stock_value

simulation_trades (거래 기록)
├── trade_id (PK)
├── session_id (FK → simulation_sessions)
├── date
├── stock_code
├── action (BUY/SELL)
├── quantity
├── price
└── commission
```

#### 팩터 관련
```sql
factor_categories (팩터 카테고리)
├── category_id (PK)
├── category_name (가치/성장/퀄리티/모멘텀/규모)
└── description

factors (팩터 정의)
├── factor_id (PK)
├── category_id (FK → factor_categories)
├── factor_name
├── calculation_type (FUNDAMENTAL/TECHNICAL/CUSTOM)
├── formula
└── update_frequency

strategy_factors (전략별 팩터 설정)
├── id (PK)
├── strategy_id (FK → portfolio_strategies)
├── factor_id (FK → factors)
├── usage_type (SCREENING/RANKING/SCORING)
├── operator (GT/LT/EQ/TOP_N/BOTTOM_N)
├── threshold_value
└── weight
```

#### 자동매매 관련
```sql
auto_trading_strategies (자동매매 전략)
├── auto_trading_id (PK, UUID)
├── user_id (FK → users)
├── strategy_id (FK → portfolio_strategies)
├── session_id (FK → simulation_sessions)
├── is_active (활성화 여부)
├── allocated_capital (할당 자본)
├── current_capital (현재 자본)
└── total_return (총 수익률)

auto_trading_holdings (보유 종목)
├── holding_id (PK)
├── auto_trading_id (FK → auto_trading_strategies)
├── stock_code
├── quantity
├── avg_price
└── current_value

auto_trading_trades (거래 기록)
├── trade_id (PK)
├── auto_trading_id (FK → auto_trading_strategies)
├── trade_date
├── stock_code
├── action (BUY/SELL)
├── quantity
├── price
└── order_status
```

#### 커뮤니티 관련
```sql
community_posts (게시글)
├── post_id (PK, UUID)
├── user_id (FK → users)
├── strategy_id (FK → portfolio_strategies, nullable)
├── title
├── content
├── category (STRATEGY/FREE/QNA)
├── view_count
└── like_count

community_comments (댓글)
├── comment_id (PK, UUID)
├── post_id (FK → community_posts)
├── user_id (FK → users)
├── parent_comment_id (FK → community_comments, nullable)
└── content

community_likes (좋아요)
├── like_id (PK)
├── post_id (FK → community_posts)
└── user_id (FK → users)
```

#### 시장 데이터 관련
```sql
companies (종목 정보)
├── stock_code (PK)
├── stock_name
├── market (KOSPI/KOSDAQ/KONEX)
├── sector
├── industry
├── market_cap
└── listed_shares

stock_prices (일별 시세)
├── id (PK)
├── stock_code (FK → companies)
├── date
├── open_price
├── high_price
├── low_price
├── close_price
├── volume
└── UNIQUE(stock_code, date)

financial_statements (재무제표)
├── id (PK)
├── stock_code (FK → companies)
├── quarter (YYYYQ)
├── revenue (매출액)
├── operating_profit (영업이익)
├── net_profit (순이익)
├── total_assets (총자산)
└── total_liabilities (총부채)
```

### 2. 인덱스 전략

#### 복합 인덱스
```sql
-- 사용자별 시뮬레이션 조회 (최신순)
CREATE INDEX idx_simulation_sessions_user_created
ON simulation_sessions(user_id, created_at DESC);

-- 공개 전략 랭킹 조회
CREATE INDEX idx_portfolio_strategies_public
ON portfolio_strategies(is_public, user_id)
WHERE is_public = TRUE;

-- 백테스트 상태별 조회
CREATE INDEX idx_simulation_sessions_status
ON simulation_sessions(status, user_id);
```

#### 부분 인덱스
```sql
-- 완료된 백테스트만 인덱싱
CREATE INDEX idx_simulation_sessions_completed
ON simulation_sessions(strategy_id, completed_at)
WHERE status = 'COMPLETED';

-- 활성화된 자동매매만 인덱싱
CREATE INDEX idx_auto_trading_active
ON auto_trading_strategies(user_id, is_active)
WHERE is_active = TRUE;
```

#### GIN 인덱스 (JSON 컬럼)
```sql
-- 매수/매도 조건 검색
CREATE INDEX idx_trading_rules_buy_condition
ON trading_rules USING GIN (buy_condition);

CREATE INDEX idx_trading_rules_sell_condition
ON trading_rules USING GIN (sell_condition);
```

### 3. 파티셔닝

시계열 데이터는 월별 파티셔닝으로 쿼리 성능 향상:

```sql
-- 일별 시세 테이블 (월별 파티셔닝)
CREATE TABLE stock_prices (
    id SERIAL,
    stock_code VARCHAR(10),
    date DATE,
    close_price DECIMAL(15, 2),
    ...
) PARTITION BY RANGE (date);

CREATE TABLE stock_prices_2023_01
PARTITION OF stock_prices
FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE stock_prices_2023_02
PARTITION OF stock_prices
FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
```

---

## 핵심 서비스

### 1. 백테스팅 엔진

#### 아키텍처
```
┌──────────────────────────────────────────────────┐
│  백테스트 요청 (POST /api/v1/backtest/run)       │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  데이터 로딩 (Polars)                            │
│  - stock_prices (500만+ 레코드)                  │
│  - financial_statements (10만+ 레코드)           │
│  - 필터링: 날짜 범위, 종목 코드                   │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  팩터 계산 (factor_calculator_complete.py)       │
│  - 150+ 팩터 병렬 계산                           │
│  - 캐싱 (Redis): 재무 데이터                     │
│  - 의존성 분석: 팩터 간 계산 순서 최적화          │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  조건 평가 (condition_evaluator_vectorized.py)   │
│  - 매수 조건 벡터화 평가 (NumPy)                 │
│  - 우선순위 정렬 (priority_factor)               │
│  - 매도 조건 평가 (목표가/손절가/보유일)          │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  백테스트 시뮬레이션 (backtest_numba_core.py)    │
│  - Numba JIT 컴파일 (10배+ 가속화)               │
│  - 일별 포트폴리오 밸류 계산                     │
│  - 매수/매도 시그널 생성                         │
│  - 수수료/세금 계산                              │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  통계 계산 (simulation_statistics)               │
│  - 총 수익률, 연환산 수익률                      │
│  - 최대 낙폭 (MDD)                               │
│  - 샤프 지수, 변동성                             │
│  - 승률, 평균 보유 기간                          │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  결과 저장 (PostgreSQL)                          │
│  - simulation_sessions                           │
│  - simulation_statistics                         │
│  - simulation_daily_values (일별 자산)           │
│  - simulation_trades (거래 기록)                 │
└──────────────────────────────────────────────────┘
```

#### 성능 최적화 기법

**1. Polars DataFrame 사용**
```python
# Pandas 대비 10배 빠른 데이터 로딩
df = pl.read_csv("stock_prices.csv",
                 dtypes={"stock_code": pl.Utf8, "close_price": pl.Float64})
df = df.filter(pl.col("date").is_between("2020-01-01", "2023-12-31"))
```

**2. Numba JIT 컴파일**
```python
@njit(parallel=True, cache=True)
def calculate_daily_returns(prices: np.ndarray, quantities: np.ndarray) -> np.ndarray:
    """일별 수익률 계산 (Numba 가속화)"""
    n = len(prices)
    returns = np.zeros(n)
    for i in prange(n):
        returns[i] = prices[i] * quantities[i]
    return returns
```

**3. 벡터화 조건 평가**
```python
# NumPy 벡터 연산 (루프 대비 100배+ 빠름)
mask = (df["per"] < 10) & (df["pbr"] < 1.5) & (df["roe"] > 15)
filtered = df.filter(mask)
```

**4. 캐싱 전략**
```python
# Redis 캐싱 (재무 데이터)
cache_key = f"financial:{stock_code}:{quarter}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# DB 조회 후 캐싱
data = await db.execute(query)
await redis.setex(cache_key, 3600, json.dumps(data))  # TTL: 1시간
```

### 2. 자동매매 시스템

#### 스케줄러 (APScheduler)
```python
scheduler = AsyncIOScheduler()

# 매일 장 시작 직전 (08:50)
scheduler.add_job(
    prepare_trading,
    trigger=CronTrigger(day_of_week='mon-fri', hour=8, minute=50),
    id='prepare_trading'
)

# 매수 체크 (09:05)
scheduler.add_job(
    check_buy_signals,
    trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=5),
    id='check_buy_signals'
)

# 매도 체크 (14:50)
scheduler.add_job(
    check_sell_signals,
    trigger=CronTrigger(day_of_week='mon-fri', hour=14, minute=50),
    id='check_sell_signals'
)
```

#### 주문 실행 흐름
```
1. 매수 시그널 감지
   ↓
2. 매수 조건 평가
   - 현금 잔고 확인
   - 최대 보유 종목 수 확인
   - 종목당 투자 비율 계산
   ↓
3. 키움 API 주문 실행
   - 지정가 주문 (현재가 ± 1%)
   - 주문 번호 저장
   ↓
4. 체결 확인 (폴링)
   - 5초마다 체결 여부 확인
   - 미체결 시 재주문 또는 취소
   ↓
5. 포지션 업데이트
   - auto_trading_holdings 테이블 업데이트
   - auto_trading_trades 거래 기록 저장
```

### 3. 랭킹 시스템 (Redis Sorted Set)

#### 데이터 구조
```python
# Redis Sorted Set (score = total_return)
rankings:all = {
    "session-uuid-1": 125.5,  # 총 수익률 125.5%
    "session-uuid-2": 98.3,
    "session-uuid-3": 87.1,
    ...
}

# 메타데이터 (Hash)
ranking:session-uuid-1 = {
    "strategy_id": "strategy-uuid-1",
    "strategy_name": "피터 린치 전략",
    "total_return": "125.5",
    "annualized_return": "28.3",
    "is_public": "true"
}
```

#### 랭킹 조회 (O(log N))
```python
# 상위 20개 조회
top_sessions = await redis.zrevrange("rankings:all", 0, 19, withscores=True)

# 특정 세션 순위 조회
rank = await redis.zrevrank("rankings:all", session_id)
```

#### DB-Redis 동기화
```python
async def sync_ranking_to_redis(session_id: str, total_return: float, is_public: bool):
    """백테스트 완료 시 Redis 랭킹 업데이트"""
    if is_public:
        await redis.zadd("rankings:all", {session_id: total_return})
        await redis.hset(f"ranking:{session_id}", mapping={
            "strategy_id": strategy_id,
            "total_return": total_return,
            ...
        })
    else:
        await redis.zrem("rankings:all", session_id)
        await redis.delete(f"ranking:{session_id}")
```

### 4. 팩터 계산 시스템

#### 150+ 팩터 분류

**가치 (Value) - 30개**
- PER, PBR, PSR, PCR, PEG
- EV/EBITDA, EV/Sales, EV/FCF
- 배당수익률, 자산수익률
- ...

**성장 (Growth) - 35개**
- 매출 성장률 (1년, 3년, 5년)
- 영업이익 성장률
- 순이익 성장률
- EPS 성장률
- ...

**퀄리티 (Quality) - 30개**
- ROE, ROA, ROIC
- 영업이익률, 순이익률
- 부채비율, 유동비율
- 이자보상배율
- ...

**모멘텀 (Momentum) - 35개**
- 상대강도 (1개월, 3개월, 6개월, 12개월)
- 이동평균 (5일, 20일, 60일, 120일)
- MACD, RSI, Stochastic
- 거래량 증가율
- ...

**규모 (Size) - 20개**
- 시가총액
- 거래대금 (1일, 5일, 20일)
- 유동주식수
- 액면분할 이력
- ...

#### 팩터 의존성 분석

```python
FACTOR_DEPENDENCIES = {
    "peg_ratio": ["per", "eps_growth_1y"],      # PEG = PER / EPS 성장률
    "ev_ebitda": ["market_cap", "debt", "ebitda"],  # EV/EBITDA
    "roic": ["nopat", "invested_capital"],      # ROIC = NOPAT / Invested Capital
    ...
}

# 토폴로지 정렬로 계산 순서 최적화
sorted_factors = topological_sort(FACTOR_DEPENDENCIES)
```

---

## 성능 최적화

### 1. 데이터베이스 최적화

#### 연결 풀 설정
```python
# app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,           # 기본 연결 수
    max_overflow=100,       # 추가 연결 수 (피크 타임)
    pool_timeout=60,        # 연결 대기 시간
    pool_recycle=1800,      # 연결 재활용 주기 (30분)
    echo=False              # SQL 로깅 비활성화
)
```

#### 쿼리 최적화
```python
# N+1 문제 해결 (Eager Loading)
query = (
    select(SimulationSession, PortfolioStrategy, SimulationStatistics)
    .join(PortfolioStrategy)
    .outerjoin(SimulationStatistics)
    .options(selectinload(SimulationSession.trades))  # 거래 기록 한 번에 로딩
)

# 페이지네이션 (오프셋 대신 커서 사용)
query = query.where(SimulationSession.created_at < last_created_at).limit(20)
```

### 2. Redis 캐싱 전략

#### 캐시 TTL 설정
```python
CACHE_TTL = {
    "ranking": 300,          # 랭킹: 5분
    "market_quote": 60,      # 시세: 1분
    "financial_data": 3600,  # 재무 데이터: 1시간
    "factor_list": 86400,    # 팩터 목록: 24시간
}
```

#### 캐시 워밍
```python
# 서버 시작 시 유명 전략 캐싱
async def warm_famous_strategies():
    """피터 린치, 워렌 버핏 등 유명 전략 미리 캐싱"""
    famous_strategies = ["peter_lynch", "warren_buffett", ...]

    for strategy_name in famous_strategies:
        result = await run_backtest(strategy_name)
        await cache.set(f"backtest:{strategy_name}", result, ex=3600)
```

### 3. 비동기 처리

#### 백그라운드 태스크
```python
from fastapi import BackgroundTasks

@router.post("/backtest/run")
async def run_backtest_endpoint(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """백테스트 요청 (비동기 처리)"""
    session = await create_session(request, db)

    # 백그라운드에서 백테스트 실행
    background_tasks.add_task(execute_backtest, session.session_id, request)

    return {"session_id": session.session_id, "status": "RUNNING"}
```

#### 동시성 제어
```python
# 동시 실행 백테스트 수 제한 (Semaphore)
backtest_semaphore = asyncio.Semaphore(2)  # 최대 2개

async def execute_backtest(session_id: str, request: BacktestRequest):
    async with backtest_semaphore:
        # 백테스트 실행
        result = await run_backtest_logic(request)
        await save_result(session_id, result)
```

### 4. SSE (Server-Sent Events) 스트리밍

```python
@router.get("/backtest/{session_id}/stream")
async def stream_backtest_progress(session_id: str):
    """백테스트 진행 상황 실시간 스트리밍"""
    async def event_generator():
        while True:
            # Redis에서 진행 상황 조회
            progress = await redis.get(f"backtest:{session_id}:progress")

            if progress:
                yield {
                    "event": "progress",
                    "data": json.dumps({"progress": float(progress)})
                }

            # 완료 체크
            status = await redis.get(f"backtest:{session_id}:status")
            if status == "COMPLETED":
                yield {
                    "event": "complete",
                    "data": json.dumps({"session_id": session_id})
                }
                break

            await asyncio.sleep(1)  # 1초마다 체크

    return EventSourceResponse(event_generator())
```

---

## 보안

### 1. 인증/인가

#### JWT 토큰 생성
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=10080)  # 7일
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

#### 토큰 검증
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """현재 로그인한 사용자 조회"""
    token = credentials.credentials

    # 토큰 블랙리스트 확인 (Redis)
    is_blacklisted = await redis.exists(f"token_blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(status_code=401, detail="Token is blacklisted")

    # 토큰 디코딩
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 사용자 조회
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

### 2. 비밀번호 암호화

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """비밀번호 해싱 (bcrypt)"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 3. SQL Injection 방어

```python
# ❌ 나쁜 예 (SQL Injection 취약)
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ 좋은 예 (Prepared Statement)
query = select(User).where(User.email == email)
```

### 4. CORS 설정

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stocklab.example.com"],  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/backtest/run")
@limiter.limit("10/minute")  # 분당 10회 제한
async def run_backtest(request: Request, ...):
    ...
```

---

## 배포 및 운영

### 1. 환경 설정

#### .env 파일
```bash
# 배포 환경
DEPLOYMENT_ENV=ec2  # local | ec2

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/stocklab
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Redis
REDIS_HOST=redis-cluster.example.com
REDIS_PORT=6379
REDIS_PASSWORD=secret
REDIS_SSL=true

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 외부 API
DART_API_KEY=your-dart-api-key

# 성능
CHUNK_SIZE=10000
MAX_WORKERS=4
ENABLE_QUERY_CACHE=true
ENABLE_CACHE_WARMING=true
BACKTEST_MAX_CONCURRENT_JOBS=2
```

### 2. Docker 배포

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# Uvicorn 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./SL-Back-end
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/stocklab
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=stocklab
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3. 모니터링

#### 로깅
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log')
    ]
)

logger = logging.getLogger(__name__)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    logger.info(f"← {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")

    return response
```

#### 헬스체크
```python
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    # DB 연결 확인
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    # Redis 연결 확인
    try:
        await redis.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {e}"

    return {
        "status": "healthy" if db_status == "connected" and redis_status == "connected" else "unhealthy",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }
```

### 4. 성능 메트릭

#### 응답 시간 추적
```python
# X-Process-Time 헤더 추가
response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
```

#### 주요 성능 목표
- 백테스트 실행: < 60초 (10년 데이터 기준)
- API 응답 시간: < 200ms (캐시 히트)
- 랭킹 조회: < 100ms (Redis)
- 시세 조회: < 50ms (캐시)

---

## 부록

### A. 기술 부채 및 개선 사항

1. **백테스팅 엔진**
   - 분산 처리 (Celery + RabbitMQ)
   - GPU 가속 (CUDA)
   - 실시간 백테스트 (틱 데이터)

2. **자동매매**
   - 리스크 관리 강화 (VaR, CVaR)
   - 멀티 브로커 지원 (NH투자증권, 미래에셋 등)
   - 알고리즘 트레이딩 (VWAP, TWAP)

3. **인프라**
   - Kubernetes 오케스트레이션
   - ELK 스택 로깅
   - Prometheus + Grafana 모니터링

### B. 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 문서](https://docs.sqlalchemy.org/en/20/)
- [Polars 공식 문서](https://pola-rs.github.io/polars/)
- [Numba 공식 문서](https://numba.readthedocs.io/)
- [Redis 공식 문서](https://redis.io/docs/)

---

**최종 수정일**: 2025-01-15
**작성자**: Backend - 김형욱
