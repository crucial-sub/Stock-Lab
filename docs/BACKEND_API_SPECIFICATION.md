# Stock Lab Backend API 명세서

## 목차
1. [개요](#개요)
2. [인증 (Authentication)](#인증-authentication)
3. [백테스트 (Backtest)](#백테스트-backtest)
4. [전략 관리 (Strategy)](#전략-관리-strategy)
5. [자동매매 (Auto Trading)](#자동매매-auto-trading)
6. [시장 데이터 (Market Data)](#시장-데이터-market-data)
7. [커뮤니티 (Community)](#커뮤니티-community)
8. [키움증권 연동 (Kiwoom)](#키움증권-연동-kiwoom)
9. [오류 코드](#오류-코드)

---

## 개요

### 기본 정보
- **Base URL**: `/api/v1`
- **프로토콜**: HTTPS
- **인증 방식**: JWT Bearer Token
- **응답 형식**: JSON
- **문자 인코딩**: UTF-8

### 기술 스택
- **프레임워크**: FastAPI 0.109+
- **데이터베이스**: PostgreSQL 15+
- **캐시**: Redis 7+
- **비동기 처리**: asyncio, asyncpg
- **데이터 분석**: Polars, NumPy, Numba

### 주요 기능
1. **퀀트 백테스팅**: 150+ 팩터 기반 전략 백테스트
2. **자동매매**: 키움증권 API 연동 실거래 자동화
3. **전략 공유**: 공개 전략 랭킹 및 복제 기능
4. **커뮤니티**: 전략 공유, 게시판, 댓글 시스템

---

## 인증 (Authentication)

### 1. 회원가입
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "홍길동",
  "nickname": "길동이",
  "email": "hong@example.com",
  "phone_number": "01012345678",
  "password": "SecurePassword123!"
}
```

**응답 (201 Created)**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "nickname": "길동이",
  "email": "hong@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:30:00Z",
  "has_kiwoom_account": false,
  "ai_recommendation_block": false
}
```

**오류 응답**
- `400 Bad Request`: 이메일/닉네임/전화번호 중복
- `422 Unprocessable Entity`: 유효성 검증 실패

---

### 2. 로그인
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

email=hong@example.com&password=SecurePassword123!
```

**응답 (200 OK)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**토큰 사용 예시**
```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**오류 응답**
- `401 Unauthorized`: 이메일 또는 비밀번호 불일치
- `403 Forbidden`: 비활성화된 계정

**주의사항**
- 토큰 만료 시간: 7일 (10,080분)
- 로그인 시 키움 토큰 자동 갱신 시도
- Redis 연결 시 토큰 블랙리스트 관리 가능

---

### 3. 로그아웃
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "message": "로그아웃되었습니다 (토큰 무효화됨)",
  "redis_enabled": true
}
```

---

### 4. 내 정보 조회
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "nickname": "길동이",
  "email": "hong@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-15T10:30:00Z",
  "has_kiwoom_account": true,
  "ai_recommendation_block": false
}
```

---

### 5. 닉네임 중복 확인
```http
GET /api/v1/auth/check-nickname/{nickname}
```

**응답 (200 OK)**
```json
{
  "nickname": "길동이",
  "available": false
}
```

---

### 6. 닉네임 변경
```http
PATCH /api/v1/auth/update-nickname?new_nickname=새닉네임
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "nickname": "새닉네임",
  ...
}
```

---

### 7. 회원탈퇴
```http
DELETE /api/v1/auth/delete-account
Content-Type: application/json

{
  "email": "hong@example.com",
  "password": "SecurePassword123!",
  "phone_number": "01012345678"
}
```

**응답 (200 OK)**
```json
{
  "message": "회원탈퇴가 정상적으로 처리되었습니다",
  "email": "hong@example.com"
}
```

**주의사항**
- 실제 데이터 삭제가 아닌 소프트 삭제 (`is_active = False`)
- 이메일, 비밀번호, 전화번호 3가지 모두 일치해야 탈퇴 가능

---

## 백테스트 (Backtest)

### 1. 백테스트 실행
```http
POST /api/v1/backtest/run
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "strategy_name": "피터 린치 전략",
  "description": "PEG 레이쇼 기반 가치 성장 전략",
  "start_date": "20200101",
  "end_date": "20231231",
  "initial_capital": 100000000,
  "commission_rate": 0.015,
  "buy_conditions": [
    {
      "factor_id": "peg_ratio",
      "operator": "LT",
      "value": 1.0
    }
  ],
  "buy_logic": "AND",
  "priority_factor": "market_cap",
  "priority_order": "desc",
  "max_holdings": 20,
  "per_stock_ratio": 5.0,
  "sell_conditions": {
    "target_and_loss": {
      "target_profit": 30.0,
      "stop_loss": 15.0
    },
    "hold_days": 60
  },
  "trade_targets": {
    "use_all_stocks": false,
    "selected_themes": ["IT", "BIO"],
    "selected_stocks": ["005930", "000660"]
  }
}
```

**응답 (200 OK)**
```json
{
  "session_id": "abc-123-def-456",
  "status": "RUNNING",
  "message": "백테스트가 시작되었습니다"
}
```

**백테스트 파라미터 설명**
- `start_date`, `end_date`: YYYYMMDD 형식
- `initial_capital`: 초기 자본금 (원)
- `commission_rate`: 수수료율 (%)
- `buy_conditions`: 매수 조건 배열
  - `factor_id`: 팩터 ID (150+ 팩터 지원)
  - `operator`: GT(초과), LT(미만), GTE(이상), LTE(이하), EQ(같음)
  - `value`: 비교 값
- `buy_logic`: AND(모두 만족) 또는 OR(하나라도 만족)
- `priority_factor`: 우선순위 팩터 (매수 종목 정렬 기준)
- `priority_order`: asc(오름차순) 또는 desc(내림차순)
- `max_holdings`: 최대 보유 종목 수
- `per_stock_ratio`: 종목당 투자 비율 (%)
- `sell_conditions`: 매도 조건
  - `target_and_loss`: 목표 수익률/손절 비율 (%)
  - `hold_days`: 보유 기간 (일)
  - `condition_sell`: 조건 매도 (buy_conditions 반대)

---

### 2. 백테스트 상태 조회
```http
GET /api/v1/backtest/{session_id}/status
Authorization: Bearer {access_token}
```

**응답 (200 OK) - 진행 중**
```json
{
  "session_id": "abc-123-def-456",
  "status": "RUNNING",
  "progress": 45.5,
  "message": "백테스트 진행 중... (2021-05-15)"
}
```

**응답 (200 OK) - 완료**
```json
{
  "session_id": "abc-123-def-456",
  "status": "COMPLETED",
  "progress": 100.0,
  "completed_at": "2025-01-15T10:35:00Z"
}
```

**상태 값**
- `PENDING`: 대기 중
- `RUNNING`: 실행 중
- `COMPLETED`: 완료
- `FAILED`: 실패

---

### 3. 백테스트 결과 조회
```http
GET /api/v1/backtest/{session_id}/result
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "session_id": "abc-123-def-456",
  "strategy_name": "피터 린치 전략",
  "status": "COMPLETED",
  "backtest_period": {
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "trading_days": 980
  },
  "statistics": {
    "total_return": 125.5,
    "annualized_return": 28.3,
    "max_drawdown": -18.2,
    "sharpe_ratio": 1.85,
    "volatility": 22.1,
    "win_rate": 62.5,
    "total_trades": 324,
    "avg_holding_period": 45
  },
  "daily_values": [
    {
      "date": "2020-01-02",
      "total_value": 100000000,
      "cash": 100000000,
      "stock_value": 0,
      "return": 0.0
    },
    ...
  ],
  "trades": [
    {
      "date": "2020-01-15",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "action": "BUY",
      "quantity": 100,
      "price": 58000,
      "amount": 5800000,
      "commission": 870
    },
    ...
  ],
  "holdings": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 100,
      "avg_price": 58000,
      "current_price": 72000,
      "return": 24.1
    }
  ]
}
```

**주요 지표 설명**
- `total_return`: 총 수익률 (%)
- `annualized_return`: 연환산 수익률 (%)
- `max_drawdown`: 최대 낙폭 (%)
- `sharpe_ratio`: 샤프 지수 (위험 대비 수익)
- `volatility`: 변동성 (표준편차, %)
- `win_rate`: 승률 (%)

---

### 4. 백테스트 SSE 스트리밍
```http
GET /api/v1/backtest/{session_id}/stream
Authorization: Bearer {access_token}
Accept: text/event-stream
```

**SSE 이벤트 스트림**
```
event: progress
data: {"progress": 10.5, "message": "2020-03-15 백테스트 중..."}

event: progress
data: {"progress": 50.0, "message": "2021-06-20 백테스트 중..."}

event: complete
data: {"session_id": "abc-123-def-456", "status": "COMPLETED"}

event: error
data: {"error": "백테스트 실행 중 오류 발생"}
```

---

## 전략 관리 (Strategy)

### 1. 내 전략 목록 조회
```http
GET /api/v1/strategies/my?page=1&limit=20
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "strategies": [
    {
      "session_id": "abc-123-def-456",
      "strategy_id": "strategy-uuid-1",
      "strategy_name": "피터 린치 전략",
      "is_active": false,
      "is_public": true,
      "status": "COMPLETED",
      "source_session_id": null,
      "total_return": 125.5,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "has_next": true
}
```

---

### 2. 공개 전략 랭킹 조회
```http
GET /api/v1/strategies/public/ranking?sort_by=annualized_return&page=1&limit=20
```

**Query Parameters**
- `sort_by`: `total_return` (총 수익률) 또는 `annualized_return` (연환산 수익률)
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)

**응답 (200 OK)**
```json
{
  "rankings": [
    {
      "strategy_id": "strategy-uuid-1",
      "strategy_name": "피터 린치 전략",
      "owner_name": "홍길동",
      "is_anonymous": false,
      "strategy_type": "VALUE_GROWTH",
      "description": "PEG 레이쇼 기반 가치 성장 전략",
      "hide_strategy_details": false,
      "backtest_start_date": "2020-01-01",
      "backtest_end_date": "2023-12-31",
      "total_return": 125.5,
      "annualized_return": 28.3,
      "max_drawdown": -18.2,
      "sharpe_ratio": 1.85,
      "volatility": 22.1,
      "win_rate": 62.5,
      "total_trades": 324,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1523,
  "page": 1,
  "limit": 20,
  "sort_by": "annualized_return"
}
```

**캐싱**
- Redis 캐시 TTL: 5분
- 캐시 키: `strategy_ranking:{sort_by}:page_{page}:limit_{limit}`

---

### 3. 공개 전략 목록 조회 (최신순)
```http
GET /api/v1/strategies/public?page=1&limit=20
```

**응답 (200 OK)**
```json
{
  "strategies": [
    {
      "strategy_id": "strategy-uuid-1",
      "strategy_name": "피터 린치 전략",
      "description": "PEG 레이쇼 기반 가치 성장 전략",
      "is_anonymous": false,
      "hide_strategy_details": false,
      "owner_name": "홍길동",
      "session_id": "abc-123-def-456",
      "total_return": 125.5,
      "annualized_return": 28.3,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 1523,
  "page": 1,
  "limit": 20,
  "has_next": true
}
```

---

### 4. 전략 정보 수정
```http
PATCH /api/v1/strategies/{strategy_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "strategy_name": "피터 린치 전략 v2",
  "description": "개선된 PEG 레이쇼 전략"
}
```

**응답 (200 OK)**
```json
{
  "message": "투자전략이 수정되었습니다.",
  "strategyName": "피터 린치 전략 v2"
}
```

---

### 5. 전략 공개 설정 변경
```http
PATCH /api/v1/strategies/{strategy_id}/settings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "is_public": true,
  "is_anonymous": false,
  "hide_strategy_details": false
}
```

**응답 (200 OK)**
```json
{
  "message": "공개 설정이 업데이트되었습니다",
  "strategy_id": "strategy-uuid-1",
  "settings": {
    "is_public": true,
    "is_anonymous": false,
    "hide_strategy_details": false
  }
}
```

**설정 옵션**
- `is_public`: 공개 여부 (랭킹 집계 대상)
- `is_anonymous`: 익명 여부 (소유자 이름 숨김)
- `hide_strategy_details`: 전략 내용 숨김 (매수/매도 조건 비공개)

**주의사항**
- 백테스트 진행 중 또는 실패한 전략은 공개 불가
- 공개 설정 변경 시 Redis 랭킹 자동 동기화
- 랭킹 캐시 자동 무효화

---

### 6. 백테스트 세션 삭제
```http
DELETE /api/v1/strategies/sessions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "session_ids": [
    "session-uuid-1",
    "session-uuid-2"
  ]
}
```

**응답 (200 OK)**
```json
{
  "message": "2개의 백테스트가 삭제되었습니다",
  "deleted_session_ids": ["session-uuid-1", "session-uuid-2"],
  "deleted_count": 2
}
```

**주의사항**
- 본인 소유 세션만 삭제 가능
- 관련 통계 데이터(SimulationStatistics) 함께 삭제
- Redis 랭킹에서 자동 제거

---

### 7. 전략 복제 데이터 조회
```http
GET /api/v1/strategies/sessions/{session_id}/clone-data
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "strategy_name": "피터 린치 전략 (복제)",
  "is_day_or_month": "daily",
  "initial_investment": 10000,
  "start_date": "20200101",
  "end_date": "20231231",
  "commission_rate": 0.015,
  "slippage": 0.1,
  "buy_conditions": [...],
  "buy_logic": "AND",
  "priority_factor": "market_cap",
  "priority_order": "desc",
  "per_stock_ratio": 5.0,
  "max_holdings": 20,
  "max_buy_value": null,
  "max_daily_stock": null,
  "buy_price_basis": "CLOSE",
  "buy_price_offset": 0.0,
  "target_and_loss": {...},
  "hold_days": 60,
  "condition_sell": null,
  "trade_targets": {...}
}
```

**접근 권한**
- 본인 소유 세션
- 공개된 전략의 세션

---

## 자동매매 (Auto Trading)

### 1. 자동매매 전략 생성
```http
POST /api/v1/auto-trading
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "strategy_id": "strategy-uuid-1",
  "session_id": "session-uuid-1",
  "strategy_name": "피터 린치 자동매매",
  "allocated_capital": 50000000,
  "max_positions": 10
}
```

**응답 (201 Created)**
```json
{
  "auto_trading_id": "auto-trading-uuid-1",
  "strategy_id": "strategy-uuid-1",
  "strategy_name": "피터 린치 자동매매",
  "is_active": false,
  "allocated_capital": 50000000,
  "current_capital": 50000000,
  "total_return": 0.0,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 2. 자동매매 시작/중지
```http
PATCH /api/v1/auto-trading/{auto_trading_id}/toggle
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "auto_trading_id": "auto-trading-uuid-1",
  "is_active": true,
  "message": "자동매매가 시작되었습니다"
}
```

---

### 3. 자동매매 상태 조회
```http
GET /api/v1/auto-trading/{auto_trading_id}
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "auto_trading_id": "auto-trading-uuid-1",
  "strategy_name": "피터 린치 자동매매",
  "is_active": true,
  "allocated_capital": 50000000,
  "current_capital": 52500000,
  "total_return": 5.0,
  "status": "RUNNING",
  "last_execution_at": "2025-01-15T09:00:00Z",
  "holdings": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 50,
      "avg_price": 70000,
      "current_price": 72000,
      "return": 2.86
    }
  ],
  "recent_trades": [
    {
      "trade_date": "2025-01-15",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "action": "BUY",
      "quantity": 50,
      "price": 70000,
      "amount": 3500000
    }
  ]
}
```

---

### 4. 자동매매 목록 조회
```http
GET /api/v1/auto-trading/my?page=1&limit=20
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "strategies": [
    {
      "auto_trading_id": "auto-trading-uuid-1",
      "strategy_name": "피터 린치 자동매매",
      "is_active": true,
      "allocated_capital": 50000000,
      "current_capital": 52500000,
      "total_return": 5.0,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 20
}
```

---

### 5. 자동매매 삭제
```http
DELETE /api/v1/auto-trading/{auto_trading_id}
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "message": "자동매매 전략이 삭제되었습니다"
}
```

**주의사항**
- 활성화된 자동매매는 삭제 불가 (먼저 중지 필요)
- 관련 거래 기록은 보존됨

---

## 시장 데이터 (Market Data)

### 1. 팩터 목록 조회
```http
GET /api/v1/factors
```

**응답 (200 OK)**
```json
{
  "categories": [
    {
      "category_id": "VALUE",
      "category_name": "가치",
      "factors": [
        {
          "factor_id": "per",
          "factor_name": "PER (주가수익비율)",
          "calculation_type": "FUNDAMENTAL",
          "formula": "주가 / 주당순이익",
          "description": "주가가 주당순이익의 몇 배인지 나타내는 지표",
          "update_frequency": "QUARTERLY"
        },
        {
          "factor_id": "pbr",
          "factor_name": "PBR (주가순자산비율)",
          "calculation_type": "FUNDAMENTAL",
          "formula": "주가 / 주당순자산",
          "description": "주가가 주당순자산의 몇 배인지 나타내는 지표",
          "update_frequency": "QUARTERLY"
        }
      ]
    },
    {
      "category_id": "GROWTH",
      "category_name": "성장",
      "factors": [...]
    }
  ]
}
```

**팩터 카테고리**
- VALUE: 가치 (PER, PBR, PEG, PCR, PSR, EV/EBITDA 등)
- GROWTH: 성장 (매출성장률, 영업이익성장률, 순이익성장률 등)
- QUALITY: 퀄리티 (ROE, ROA, ROIC, 부채비율, 유동비율 등)
- MOMENTUM: 모멘텀 (상대강도, 이동평균, MACD, RSI 등)
- SIZE: 규모 (시가총액, 거래대금, 유동주식수 등)

---

### 2. 종목 정보 조회
```http
GET /api/v1/companies/{stock_code}
```

**응답 (200 OK)**
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "market": "KOSPI",
  "sector": "전기전자",
  "industry": "반도체",
  "market_cap": 450000000000000,
  "listed_shares": 5969782550,
  "current_price": 72000,
  "change_rate": 1.2,
  "trading_volume": 15000000,
  "trading_value": 1080000000000
}
```

---

### 3. 시세 조회
```http
GET /api/v1/market-quote/{stock_code}
```

**응답 (200 OK)**
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "current_price": 72000,
  "change_price": 800,
  "change_rate": 1.12,
  "open_price": 71500,
  "high_price": 72500,
  "low_price": 71000,
  "volume": 15000000,
  "timestamp": "2025-01-15T15:30:00Z"
}
```

---

### 4. 뉴스 목록 조회
```http
GET /api/v1/news?page=1&limit=20&category=IT
```

**응답 (200 OK)**
```json
{
  "news": [
    {
      "news_id": "news-uuid-1",
      "title": "삼성전자, 신규 반도체 공장 착공",
      "summary": "삼성전자가 경기도 평택에 신규 반도체 공장을 착공...",
      "category": "IT",
      "published_at": "2025-01-15T14:00:00Z",
      "source": "한국경제",
      "url": "https://example.com/news/123"
    }
  ],
  "total": 523,
  "page": 1,
  "limit": 20
}
```

---

### 5. 유니버스 조회
```http
GET /api/v1/universes/themes
```

**응답 (200 OK)**
```json
{
  "themes": [
    {
      "theme_id": "IT",
      "theme_name": "정보기술",
      "stock_count": 352,
      "avg_market_cap": 1500000000000
    },
    {
      "theme_id": "BIO",
      "theme_name": "바이오",
      "stock_count": 128,
      "avg_market_cap": 500000000000
    }
  ]
}
```

---

## 커뮤니티 (Community)

### 1. 게시글 목록 조회
```http
GET /api/v1/community/posts?page=1&limit=20&category=FREE
```

**응답 (200 OK)**
```json
{
  "posts": [
    {
      "post_id": "post-uuid-1",
      "title": "피터 린치 전략 공유합니다",
      "content": "PEG 레이쇼 기반 전략입니다...",
      "category": "STRATEGY",
      "author": {
        "user_id": "user-uuid-1",
        "nickname": "길동이"
      },
      "view_count": 523,
      "like_count": 45,
      "comment_count": 12,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1523,
  "page": 1,
  "limit": 20
}
```

---

### 2. 게시글 작성
```http
POST /api/v1/community/posts
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "피터 린치 전략 공유합니다",
  "content": "PEG 레이쇼 기반 전략입니다...",
  "category": "STRATEGY",
  "strategy_id": "strategy-uuid-1"
}
```

**응답 (201 Created)**
```json
{
  "post_id": "post-uuid-1",
  "title": "피터 린치 전략 공유합니다",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 3. 댓글 작성
```http
POST /api/v1/community/posts/{post_id}/comments
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "좋은 전략 감사합니다!"
}
```

**응답 (201 Created)**
```json
{
  "comment_id": "comment-uuid-1",
  "content": "좋은 전략 감사합니다!",
  "author": {
    "user_id": "user-uuid-1",
    "nickname": "길동이"
  },
  "created_at": "2025-01-15T10:35:00Z"
}
```

---

### 4. 좋아요
```http
POST /api/v1/community/posts/{post_id}/like
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "message": "좋아요가 추가되었습니다",
  "like_count": 46
}
```

---

## 키움증권 연동 (Kiwoom)

### 1. 키움 계좌 연동
```http
POST /api/v1/kiwoom/connect
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "app_key": "PS1234567890ABCD",
  "app_secret": "1234567890ABCDEFGHIJKLMNOPQRSTUV"
}
```

**응답 (200 OK)**
```json
{
  "message": "키움증권 계좌 연동이 완료되었습니다",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-01-16T10:30:00Z"
}
```

---

### 2. 예수금 조회
```http
GET /api/v1/kiwoom/deposit
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "deposit": 10000000,
  "withdrawable": 9500000,
  "order_possible": 9500000
}
```

---

### 3. 보유 종목 조회
```http
GET /api/v1/kiwoom/holdings
Authorization: Bearer {access_token}
```

**응답 (200 OK)**
```json
{
  "holdings": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 100,
      "avg_price": 70000,
      "current_price": 72000,
      "eval_amount": 7200000,
      "profit_loss": 200000,
      "profit_loss_rate": 2.86
    }
  ],
  "total_eval_amount": 7200000,
  "total_profit_loss": 200000
}
```

---

### 4. 주문 실행
```http
POST /api/v1/kiwoom/order
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "stock_code": "005930",
  "order_type": "BUY",
  "quantity": 10,
  "price": 72000,
  "order_condition": "LIMIT"
}
```

**응답 (200 OK)**
```json
{
  "order_id": "order-20250115-001",
  "message": "주문이 접수되었습니다",
  "stock_code": "005930",
  "order_type": "BUY",
  "quantity": 10,
  "price": 72000
}
```

**주문 유형**
- `BUY`: 매수
- `SELL`: 매도

**주문 조건**
- `LIMIT`: 지정가
- `MARKET`: 시장가

---

## 오류 코드

### HTTP 상태 코드
- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청 (유효성 검증 실패)
- `401 Unauthorized`: 인증 실패 (토큰 없음 또는 만료)
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `409 Conflict`: 중복 데이터
- `422 Unprocessable Entity`: 처리 불가능한 엔티티
- `500 Internal Server Error`: 서버 오류

### 오류 응답 형식
```json
{
  "detail": "오류 메시지",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### 주요 오류 코드
- `INVALID_TOKEN`: 유효하지 않은 토큰
- `TOKEN_EXPIRED`: 토큰 만료
- `INSUFFICIENT_PERMISSION`: 권한 부족
- `DUPLICATE_EMAIL`: 이메일 중복
- `DUPLICATE_NICKNAME`: 닉네임 중복
- `BACKTEST_RUNNING`: 백테스트 진행 중
- `BACKTEST_FAILED`: 백테스트 실패
- `KIWOOM_API_ERROR`: 키움 API 오류
- `DATABASE_ERROR`: 데이터베이스 오류
- `CACHE_ERROR`: 캐시 오류

---

## 부록

### A. 성능 최적화
1. **Redis 캐싱**
   - 랭킹 데이터: 5분 TTL
   - 시장 데이터: 1분 TTL
   - 팩터 데이터: 1시간 TTL

2. **데이터베이스 인덱싱**
   - 복합 인덱스: (user_id, created_at)
   - 부분 인덱스: (status='COMPLETED')
   - GIN 인덱스: JSON 컬럼

3. **비동기 처리**
   - 백테스트: 백그라운드 태스크
   - 자동매매: APScheduler
   - SSE: asyncio 스트림

### B. 보안
1. **인증/인가**
   - JWT 토큰: HS256 알고리즘
   - 토큰 만료: 7일
   - 비밀번호: bcrypt 해싱

2. **API 제한**
   - Rate Limiting: 100 req/min
   - CORS: 허용 도메인 설정
   - SQL Injection 방어: Prepared Statement

### C. 모니터링
1. **로깅**
   - 요청/응답 로깅
   - 오류 추적 (Sentry)
   - 성능 모니터링 (X-Process-Time 헤더)

2. **헬스체크**
   - `/health`: 서버 상태
   - `/debug/config`: 설정 정보 (개발 전용)

---

**최종 수정일**: 2025-01-15
**작성자**: Backend - 김형욱
