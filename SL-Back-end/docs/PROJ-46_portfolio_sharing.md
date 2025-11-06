# PROJ-46: Portfolio Sharing & Ranking System

> **작성일**: 2025-11-06
> **작성자**: Claude Code
> **관련 이슈**: PROJ-46
> **태그**: `portfolio`, `ranking`, `sharing`, `privacy`

## 📋 목차

1. [개요](#개요)
2. [데이터베이스 스키마 변경](#데이터베이스-스키마-변경)
3. [백엔드 구현](#백엔드-구현)
4. [API 엔드포인트](#api-엔드포인트)
5. [마이그레이션 실행](#마이그레이션-실행)
6. [테스트 가이드](#테스트-가이드)

---

## 개요

### 목적

사용자가 생성한 투자전략(Portfolio Strategy)을 관리하고 공유할 수 있는 시스템을 구현합니다. 주요 기능은 다음과 같습니다:

1. **내 투자전략 관리**: 사용자가 생성한 모든 투자전략을 한 곳에서 확인
2. **공개 랭킹**: 높은 수익률을 기록한 공개 투자전략 랭킹 제공
3. **프라이버시 제어**: 익명 설정, 전략 내용 숨김 등의 세밀한 공개 설정

### 주요 요구사항

- 투자전략 소유자 추적 (`user_id`)
- 공개/비공개 설정 (`is_public`)
- 익명 여부 설정 (`is_anonymous`)
- 전략 내용 숨김 설정 (`hide_strategy_details`)
- 랭킹 정렬: 총 수익률 or 연환산 수익률

---

## 데이터베이스 스키마 변경

### 변경된 테이블: `portfolio_strategies`

#### 추가된 컬럼

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `user_id` | VARCHAR(36) | NULL, INDEX | 전략 생성자 ID (UUID) |
| `is_public` | BOOLEAN | NOT NULL, DEFAULT FALSE | 공개 여부 (랭킹 집계) |
| `is_anonymous` | BOOLEAN | NOT NULL, DEFAULT FALSE | 익명 여부 |
| `hide_strategy_details` | BOOLEAN | NOT NULL, DEFAULT FALSE | 전략 내용 숨김 여부 |

#### 추가된 인덱스

```sql
CREATE INDEX idx_portfolio_strategies_user ON portfolio_strategies(user_id);
CREATE INDEX idx_portfolio_strategies_public ON portfolio_strategies(is_public, user_id);
```

### ERD 업데이트

```
┌─────────────────────────┐
│   users                 │
├─────────────────────────┤
│ user_id (PK, UUID)      │
│ name                    │
│ email                   │
└─────────────────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────┐
│ portfolio_strategies    │
├─────────────────────────┤
│ strategy_id (PK, UUID)  │
│ user_id (FK) ◄──────────┼─── 새로 추가
│ strategy_name           │
│ is_public ◄─────────────┼─── 새로 추가
│ is_anonymous ◄──────────┼─── 새로 추가
│ hide_strategy_details ◄─┼─── 새로 추가
│ ...                     │
└─────────────────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────┐
│ simulation_sessions     │
├─────────────────────────┤
│ session_id (PK)         │
│ strategy_id (FK)        │
└─────────────────────────┘
            │
            │ 1:1
            ▼
┌─────────────────────────┐
│ simulation_statistics   │
├─────────────────────────┤
│ session_id (FK)         │
│ total_return            │
│ annualized_return       │
│ sharpe_ratio            │
│ ...                     │
└─────────────────────────┘
```

---

## 백엔드 구현

### 1. 모델 변경

#### 파일: `app/models/simulation.py`

**PortfolioStrategy 클래스 업데이트** (63-106 라인)

```python
class PortfolioStrategy(Base):
    """포트폴리오 전략 테이블"""
    __tablename__ = "portfolio_strategies"

    strategy_id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_name = Column(String(200), nullable=False)
    strategy_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # ✨ 새로 추가된 필드
    user_id = Column(String(36), nullable=True, index=True, comment="전략 생성자 ID (UUID)")
    is_public = Column(Boolean, default=False, nullable=False, comment="공개 여부 (랭킹 집계)")
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")
    hide_strategy_details = Column(Boolean, default=False, nullable=False, comment="전략 내용 숨김 여부")

    # 기존 필드들...
    backtest_start_date = Column(Date, nullable=True)
    backtest_end_date = Column(Date, nullable=True)
    universe_type = Column(String(50), nullable=True)
    initial_capital = Column(DECIMAL(15, 2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # ✨ 새로 추가된 인덱스
    __table_args__ = (
        Index('idx_portfolio_strategies_type', 'strategy_type'),
        Index('idx_portfolio_strategies_user', 'user_id'),
        Index('idx_portfolio_strategies_public', 'is_public', 'user_id'),
        {"comment": "포트폴리오 전략 테이블"}
    )
```

### 2. Pydantic 스키마

#### 파일: `app/schemas/portfolio.py` (새로 생성)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class PortfolioSharingSettings(BaseModel):
    """포트폴리오 공개 설정"""
    is_public: bool = Field(default=False, description="공개 여부 (랭킹 집계)")
    is_anonymous: bool = Field(default=False, description="익명 여부")
    hide_strategy_details: bool = Field(default=False, description="전략 내용 숨김 여부")


class PortfolioSharingUpdate(BaseModel):
    """포트폴리오 공개 설정 업데이트 (PATCH용)"""
    is_public: Optional[bool] = None
    is_anonymous: Optional[bool] = None
    hide_strategy_details: Optional[bool] = None


class PortfolioStatisticsSummary(BaseModel):
    """포트폴리오 통계 요약"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    total_return: Optional[float] = Field(None, serialization_alias="totalReturn")
    annualized_return: Optional[float] = Field(None, serialization_alias="annualizedReturn")
    max_drawdown: Optional[float] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[float] = Field(None, serialization_alias="sharpeRatio")
    win_rate: Optional[float] = Field(None, serialization_alias="winRate")


class PortfolioDetailItem(BaseModel):
    """내 투자전략 상세 정보"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")
    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    description: Optional[str] = None

    is_public: bool = Field(..., serialization_alias="isPublic")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")
    hide_strategy_details: bool = Field(..., serialization_alias="hideStrategyDetails")

    initial_capital: Optional[float] = Field(None, serialization_alias="initialCapital")
    backtest_start_date: Optional[date] = Field(None, serialization_alias="backtestStartDate")
    backtest_end_date: Optional[date] = Field(None, serialization_alias="backtestEndDate")

    statistics: Optional[PortfolioStatisticsSummary] = None

    created_at: datetime = Field(..., serialization_alias="createdAt")
    updated_at: datetime = Field(..., serialization_alias="updatedAt")


class PortfolioRankingItem(BaseModel):
    """공개 랭킹 아이템"""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    strategy_id: str = Field(..., serialization_alias="strategyId")
    strategy_name: str = Field(..., serialization_alias="strategyName")

    owner_name: Optional[str] = Field(None, serialization_alias="ownerName")
    is_anonymous: bool = Field(..., serialization_alias="isAnonymous")

    strategy_type: Optional[str] = Field(None, serialization_alias="strategyType")
    description: Optional[str] = None
    hide_strategy_details: bool = Field(..., serialization_alias="hideStrategyDetails")

    backtest_start_date: Optional[date] = Field(None, serialization_alias="backtestStartDate")
    backtest_end_date: Optional[date] = Field(None, serialization_alias="backtestEndDate")

    total_return: float = Field(..., serialization_alias="totalReturn")
    annualized_return: float = Field(..., serialization_alias="annualizedReturn")
    max_drawdown: Optional[float] = Field(None, serialization_alias="maxDrawdown")
    sharpe_ratio: Optional[float] = Field(None, serialization_alias="sharpeRatio")
    volatility: Optional[float] = None
    win_rate: Optional[float] = Field(None, serialization_alias="winRate")
    total_trades: Optional[int] = Field(None, serialization_alias="totalTrades")

    created_at: datetime = Field(..., serialization_alias="createdAt")


class MyPortfoliosResponse(BaseModel):
    """내 투자전략 목록 응답"""
    portfolios: List[PortfolioDetailItem]
    total: int


class PortfolioRankingResponse(BaseModel):
    """공개 랭킹 응답"""
    rankings: List[PortfolioRankingItem]
    total: int
    page: int
    limit: int
    sort_by: str = Field(..., serialization_alias="sortBy")
```

### 3. API 라우터

#### 파일: `app/api/routes/portfolio.py` (새로 생성)

**주요 엔드포인트**:

1. **GET `/portfolios/my`** - 내 투자전략 목록 조회
2. **GET `/portfolios/public/ranking`** - 공개 랭킹 조회
3. **PATCH `/portfolios/{strategy_id}/settings`** - 공개 설정 변경

**핵심 로직**:

```python
@router.get("/portfolios/my", response_model=MyPortfoliosResponse)
async def get_my_portfolios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    내 투자전략 목록 조회
    - 로그인한 사용자의 모든 전략 반환
    - 각 전략의 최신 백테스트 결과 통계 포함
    """
    # user_id로 전략 조회
    # 각 전략의 최신 완료된 시뮬레이션 통계 조회
    # PortfolioDetailItem으로 변환하여 반환
```

```python
@router.get("/portfolios/public/ranking", response_model=PortfolioRankingResponse)
async def get_public_portfolios_ranking(
    sort_by: Literal["total_return", "annualized_return"] = Query(default="annualized_return"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    공개 투자전략 랭킹 조회
    - is_public=True인 전략만 조회
    - 익명 설정 및 전략 내용 숨김 설정 반영
    - 정렬: total_return (총 수익률) or annualized_return (연환산 수익률)
    """
    # Subquery로 각 전략의 최신 완료된 시뮬레이션 찾기
    # strategy + session + statistics + user 조인
    # 정렬 및 페이지네이션 적용
    # 익명/숨김 설정에 따라 필드 마스킹
```

```python
@router.patch("/portfolios/{strategy_id}/settings")
async def update_portfolio_sharing_settings(
    strategy_id: str,
    settings: PortfolioSharingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    투자전략 공개 설정 변경
    - 본인이 소유한 전략만 수정 가능
    - is_public, is_anonymous, hide_strategy_details 변경
    """
    # 전략 조회 및 권한 확인 (user_id 체크)
    # 설정 업데이트
    # commit 및 응답
```

### 4. 백테스트 API 수정

#### 파일: `app/api/routes/backtest.py` (수정)

**BacktestRequest 스키마에 공개 설정 추가**:

```python
class BacktestRequest(BaseModel):
    """백테스트 실행 요청"""
    # 기본 설정
    user_id: str
    strategy_name: str
    # ... 기존 필드들 ...

    # ✨ 공개 설정 추가 (선택 사항)
    is_public: Optional[bool] = False
    is_anonymous: Optional[bool] = False
    hide_strategy_details: Optional[bool] = False
```

**전략 생성 시 공개 설정 포함**:

```python
@router.post("/backtest/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: AsyncSession = Depends(get_db)):
    # 전략 생성
    strategy = PortfolioStrategy(
        strategy_id=strategy_id,
        strategy_name=request.strategy_name,
        # ... 기존 필드들 ...
        user_id=request.user_id,  # ✨
        is_public=request.is_public or False,  # ✨
        is_anonymous=request.is_anonymous or False,  # ✨
        hide_strategy_details=request.hide_strategy_details or False  # ✨
    )
```

### 5. main.py 라우터 등록

#### 파일: `app/main.py` (수정)

```python
from app.api.routes import backtest, auth, portfolio  # ✨ portfolio 추가

# 라우터 등록
app.include_router(
    portfolio.router,  # ✨ 추가
    prefix=settings.API_V1_PREFIX,
    tags=["Portfolio"]
)
```

---

## API 엔드포인트

### 1. 내 투자전략 목록 조회

**Endpoint**: `GET /api/v1/portfolios/my`

**인증**: 필요 (Bearer Token)

**Request**: 없음

**Response**: `200 OK`

```json
{
  "portfolios": [
    {
      "strategyId": "abc123-...",
      "strategyName": "가치주 투자전략",
      "strategyType": "FACTOR_BASED",
      "description": "PBR 기반 저평가 가치주 투자",
      "isPublic": true,
      "isAnonymous": false,
      "hideStrategyDetails": false,
      "initialCapital": 50000000.0,
      "backtestStartDate": "2020-01-01",
      "backtestEndDate": "2024-12-31",
      "statistics": {
        "totalReturn": 125.5,
        "annualizedReturn": 18.3,
        "maxDrawdown": -22.1,
        "sharpeRatio": 1.45,
        "winRate": 62.5
      },
      "createdAt": "2024-12-01T10:30:00Z",
      "updatedAt": "2025-01-06T15:20:00Z"
    }
  ],
  "total": 1
}
```

---

### 2. 공개 투자전략 랭킹 조회

**Endpoint**: `GET /api/v1/portfolios/public/ranking`

**인증**: 불필요 (공개 API)

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `sort_by` | string | X | `annualized_return` | 정렬 기준 (`total_return` or `annualized_return`) |
| `page` | integer | X | 1 | 페이지 번호 |
| `limit` | integer | X | 20 | 페이지당 항목 수 (최대 100) |

**Request Example**:

```
GET /api/v1/portfolios/public/ranking?sort_by=annualized_return&page=1&limit=20
```

**Response**: `200 OK`

```json
{
  "rankings": [
    {
      "strategyId": "xyz789-...",
      "strategyName": "성장주 모멘텀 전략",
      "ownerName": "김투자",
      "isAnonymous": false,
      "strategyType": "MOMENTUM",
      "description": "매출성장률 기반 성장주 투자",
      "hideStrategyDetails": false,
      "backtestStartDate": "2020-01-01",
      "backtestEndDate": "2024-12-31",
      "totalReturn": 215.8,
      "annualizedReturn": 26.5,
      "maxDrawdown": -18.2,
      "sharpeRatio": 1.82,
      "volatility": 15.3,
      "winRate": 68.2,
      "totalTrades": 145,
      "createdAt": "2024-11-15T09:00:00Z"
    },
    {
      "strategyId": "abc456-...",
      "strategyName": "밸류 투자전략",
      "ownerName": null,
      "isAnonymous": true,
      "strategyType": null,
      "description": null,
      "hideStrategyDetails": true,
      "backtestStartDate": "2020-01-01",
      "backtestEndDate": "2024-12-31",
      "totalReturn": 185.3,
      "annualizedReturn": 23.1,
      "maxDrawdown": -25.5,
      "sharpeRatio": 1.55,
      "volatility": 18.7,
      "winRate": 59.3,
      "totalTrades": 98,
      "createdAt": "2024-10-20T14:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 20,
  "sortBy": "annualized_return"
}
```

**참고**:
- `isAnonymous=true`인 경우 `ownerName`은 `null`
- `hideStrategyDetails=true`인 경우 `strategyType`, `description`은 `null`

---

### 3. 투자전략 공개 설정 변경

**Endpoint**: `PATCH /api/v1/portfolios/{strategy_id}/settings`

**인증**: 필요 (Bearer Token)

**Path Parameters**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `strategy_id` | string | 전략 ID (UUID) |

**Request Body**:

```json
{
  "is_public": true,
  "is_anonymous": false,
  "hide_strategy_details": true
}
```

**Response**: `200 OK`

```json
{
  "message": "공개 설정이 업데이트되었습니다",
  "strategy_id": "abc123-...",
  "settings": {
    "is_public": true,
    "is_anonymous": false,
    "hide_strategy_details": true
  }
}
```

**Error Responses**:

- `404 Not Found`: 전략을 찾을 수 없음
- `403 Forbidden`: 본인의 전략이 아님 (권한 없음)

---

## 마이그레이션 실행

### SQL 마이그레이션 파일

**파일 위치**: `SL-Back-end/migrations/add_portfolio_sharing_fields.sql`

```sql
-- Migration: Add portfolio sharing and user ownership fields
-- Date: 2025-01-06

BEGIN;

-- Add user_id column
ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);

-- Add public sharing settings
ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS hide_strategy_details BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comments
COMMENT ON COLUMN portfolio_strategies.user_id IS '전략 생성자 ID (UUID)';
COMMENT ON COLUMN portfolio_strategies.is_public IS '공개 여부 (랭킹 집계)';
COMMENT ON COLUMN portfolio_strategies.is_anonymous IS '익명 여부';
COMMENT ON COLUMN portfolio_strategies.hide_strategy_details IS '전략 내용 숨김 여부';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolio_strategies_user ON portfolio_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_strategies_public ON portfolio_strategies(is_public, user_id);

COMMIT;
```

### 실행 방법

#### 1. 로컬 PostgreSQL

```bash
cd SL-Back-end

# PostgreSQL 클라이언트로 실행
psql -U postgres -d quant_investment_db -f migrations/add_portfolio_sharing_fields.sql

# 또는 환경 변수 사용
psql $DATABASE_URL -f migrations/add_portfolio_sharing_fields.sql
```

#### 2. Docker 환경

```bash
# Docker 컨테이너 내부에서 실행
docker exec -i postgres psql -U postgres -d quant_investment_db < SL-Back-end/migrations/add_portfolio_sharing_fields.sql

# 또는 컨테이너 접속 후 실행
docker exec -it postgres bash
psql -U postgres -d quant_investment_db -f /path/to/migrations/add_portfolio_sharing_fields.sql
```

#### 3. Docker Compose 사용

```bash
# docker-compose.yml이 있는 디렉토리에서
docker-compose exec postgres psql -U postgres -d quant_investment_db -f /app/migrations/add_portfolio_sharing_fields.sql
```

### 마이그레이션 확인

```sql
-- 컬럼이 추가되었는지 확인
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'portfolio_strategies'
  AND column_name IN ('user_id', 'is_public', 'is_anonymous', 'hide_strategy_details');

-- 인덱스 확인
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'portfolio_strategies'
  AND indexname LIKE 'idx_portfolio_strategies_%';
```

**예상 출력**:

```
       column_name        |     data_type     | is_nullable | column_default
--------------------------+-------------------+-------------+----------------
 user_id                  | character varying | YES         |
 is_public                | boolean           | NO          | false
 is_anonymous             | boolean           | NO          | false
 hide_strategy_details    | boolean           | NO          | false

                    indexname                     |                           indexdef
-------------------------------------------------+--------------------------------------------------------------
 idx_portfolio_strategies_user                   | CREATE INDEX ... ON portfolio_strategies USING btree (user_id)
 idx_portfolio_strategies_public                 | CREATE INDEX ... ON portfolio_strategies USING btree (is_public, user_id)
```

### 롤백 (필요 시)

```sql
-- 마이그레이션 롤백 스크립트
BEGIN;

DROP INDEX IF EXISTS idx_portfolio_strategies_public;
DROP INDEX IF EXISTS idx_portfolio_strategies_user;

ALTER TABLE portfolio_strategies DROP COLUMN IF EXISTS hide_strategy_details;
ALTER TABLE portfolio_strategies DROP COLUMN IF EXISTS is_anonymous;
ALTER TABLE portfolio_strategies DROP COLUMN IF EXISTS is_public;
ALTER TABLE portfolio_strategies DROP COLUMN IF EXISTS user_id;

COMMIT;
```

---

## 테스트 가이드

### 1. API 테스트 (cURL)

#### 내 투자전략 조회

```bash
# 로그인 후 토큰 획득
TOKEN="your_access_token_here"

# 내 투자전략 목록 조회
curl -X GET "http://localhost:8000/api/v1/portfolios/my" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

#### 공개 랭킹 조회

```bash
# 연환산 수익률 기준 랭킹
curl -X GET "http://localhost:8000/api/v1/portfolios/public/ranking?sort_by=annualized_return&page=1&limit=10"

# 총 수익률 기준 랭킹
curl -X GET "http://localhost:8000/api/v1/portfolios/public/ranking?sort_by=total_return&page=1&limit=10"
```

#### 공개 설정 변경

```bash
# 전략을 공개로 변경
curl -X PATCH "http://localhost:8000/api/v1/portfolios/abc123-.../settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_public": true,
    "is_anonymous": false,
    "hide_strategy_details": false
  }'
```

### 2. 데이터베이스 테스트

#### 샘플 데이터 삽입

```sql
-- 테스트용 전략 생성 (공개)
INSERT INTO portfolio_strategies (
    strategy_id, strategy_name, user_id, is_public, is_anonymous, hide_strategy_details,
    strategy_type, initial_capital, created_at, updated_at
) VALUES (
    'test-001', '테스트 전략 1', 'user-123', TRUE, FALSE, FALSE,
    'VALUE', 50000000, NOW(), NOW()
);

-- 테스트용 전략 생성 (비공개)
INSERT INTO portfolio_strategies (
    strategy_id, strategy_name, user_id, is_public, is_anonymous, hide_strategy_details,
    strategy_type, initial_capital, created_at, updated_at
) VALUES (
    'test-002', '테스트 전략 2', 'user-123', FALSE, FALSE, FALSE,
    'GROWTH', 100000000, NOW(), NOW()
);
```

#### 공개 전략 조회 쿼리

```sql
-- is_public=true인 전략만 조회
SELECT
    ps.strategy_id,
    ps.strategy_name,
    ps.is_public,
    ps.is_anonymous,
    ps.hide_strategy_details,
    u.name as owner_name,
    ss.total_return,
    ss.annualized_return,
    ss.sharpe_ratio
FROM portfolio_strategies ps
LEFT JOIN users u ON ps.user_id = u.user_id
LEFT JOIN (
    -- 각 전략의 최신 세션 찾기
    SELECT strategy_id, MAX(completed_at) as max_completed_at
    FROM simulation_sessions
    WHERE status = 'COMPLETED'
    GROUP BY strategy_id
) latest ON ps.strategy_id = latest.strategy_id
LEFT JOIN simulation_sessions ss_session ON
    ps.strategy_id = ss_session.strategy_id
    AND ss_session.completed_at = latest.max_completed_at
LEFT JOIN simulation_statistics ss ON ss_session.session_id = ss.session_id
WHERE ps.is_public = TRUE
ORDER BY ss.annualized_return DESC
LIMIT 10;
```

### 3. 시나리오 테스트

#### 시나리오 1: 전략 생성 및 공개

1. 백테스트 실행 (is_public=false로 생성)
2. "내 투자전략" 페이지에서 확인
3. 공개 설정 변경 (is_public=true)
4. 랭킹 페이지에서 표시 확인

#### 시나리오 2: 익명 공개

1. 전략 생성 (is_public=true, is_anonymous=true)
2. 랭킹 페이지에서 소유자 이름이 표시되지 않는지 확인

#### 시나리오 3: 전략 내용 숨김

1. 전략 생성 (is_public=true, hide_strategy_details=true)
2. 랭킹 페이지에서 strategyType, description이 null인지 확인

---

## 체크리스트

구현 완료 후 다음 항목들을 확인하세요:

### 백엔드

- [x] 데이터베이스 마이그레이션 실행 완료
- [x] PortfolioStrategy 모델에 필드 추가
- [x] Pydantic 스키마 작성
- [x] 내 투자전략 API 구현
- [x] 공개 랭킹 API 구현
- [x] 공개 설정 변경 API 구현
- [x] 백테스트 API에 공개 설정 추가
- [x] main.py에 라우터 등록
- [ ] API 엔드포인트 테스트 (Postman/cURL)
- [ ] 권한 검증 테스트 (타 사용자 전략 수정 시도)
- [ ] 성능 테스트 (랭킹 조회 속도)

### 프론트엔드

- [ ] TypeScript 타입 정의 추가
- [ ] API 클라이언트 함수 구현
- [ ] 내 투자전략 페이지 구현
- [ ] 공개 랭킹 페이지 구현
- [ ] 백테스트 페이지에 공개 설정 추가
- [ ] 네비게이션 링크 추가
- [ ] UI/UX 테스트

### 보안

- [ ] 인증 토큰 검증
- [ ] 권한 체크 (본인 전략만 수정 가능)
- [ ] SQL Injection 방지 확인
- [ ] 개인정보 보호 (익명 설정 동작 확인)

---

## 참고 문서

- [프론트엔드 구현 가이드](../../front-dashboard.md)
- [API 명세서](../API_SPECIFICATION.md)
- [인증 가이드](../AUTHENTICATION.md)
- [데이터베이스 설정](../DATABASE_SETUP.md)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-11-06 | 1.0.0 | 초기 문서 작성 | Claude Code |

---

**문의**: 이슈 트래커에 PROJ-46 태그로 등록
