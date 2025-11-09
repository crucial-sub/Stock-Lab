# 투자전략 공유 기능 가이드

## 📋 목차
1. [기능 개요](#기능-개요)
2. [마이그레이션](#마이그레이션)
3. [API 엔드포인트](#api-엔드포인트)
4. [사용 예시](#사용-예시)
5. [프라이버시 설정](#프라이버시-설정)

---

## 🎯 기능 개요

### 추가된 기능

#### 1. **내 투자전략 대시보드**
- 내가 만든 모든 투자전략 조회
- 상태별 필터링 (완료/실행중/실패)
- 수익률 통계 확인

#### 2. **투자전략 공유 설정**
- **공개 여부**: 랭킹에 노출
- **익명 여부**: 작성자 이름 숨김
- **전략 공개**: 팩터 조건 공개
- **설명 추가**: 투자전략 소개

#### 3. **랭킹 시스템**
- 오늘의 TOP 투자전략
- 전체 기간 명예의 전당
- 정렬 옵션: 수익률/샤프비율/좋아요

#### 4. **커뮤니티 기능**
- 조회수 추적
- 좋아요 기능
- 공유 링크 생성
- 댓글 (향후 추가)

---

## 🔧 마이그레이션

### 1. DB 마이그레이션 실행

```bash
# PostgreSQL 접속
psql -U postgres -d quant_investment_db

# 마이그레이션 실행
\i migrations/add_strategy_sharing_features.sql
```

### 2. 기존 데이터 처리

기존 `simulation_sessions` 데이터가 있는 경우:

```sql
-- 1. 임시 시스템 유저 생성
INSERT INTO users (user_id, name, email, phone_number, hashed_password, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'Legacy System',
    'legacy@system.com',
    '00000000000',
    '$2b$12$dummyhashforlegacyuser',
    TRUE
);

-- 2. 기존 세션에 user_id 할당
UPDATE simulation_sessions
SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- 3. user_id를 NOT NULL로 변경
ALTER TABLE simulation_sessions
ALTER COLUMN user_id SET NOT NULL;
```

### 3. 모델 재생성 (선택)

```bash
# Alembic 사용 시
alembic revision --autogenerate -m "add strategy sharing features"
alembic upgrade head
```

---

## 📡 API 엔드포인트

### 기본 URL
```
Base URL: http://localhost:8000/api/v1/strategys
```

### 인증
모든 엔드포인트는 JWT 토큰 필요:
```http
Authorization: Bearer <access_token>
```

---

### 1️⃣ **내 투자전략 목록 조회**

```http
GET /api/v1/strategys/my-strategys
```

**쿼리 파라미터:**
- `status_filter` (optional): COMPLETED, RUNNING, FAILED

**응답 예시:**
```json
[
  {
    "sessionId": "abc123-def456",
    "sessionName": "저PER 가치투자 전략",
    "description": "PER 10 이하 종목 매수",
    "status": "COMPLETED",
    "startDate": "2023-01-01",
    "endDate": "2024-12-31",
    "createdAt": "2025-01-06T10:30:00",
    "totalReturn": 25.5,
    "sharpeRatio": 1.2,
    "maxDrawdown": -15.3,
    "isPublic": true,
    "isAnonymous": false,
    "viewCount": 150,
    "likeCount": 23
  }
]
```

---

### 2️⃣ **공유 설정 업데이트**

```http
PATCH /api/v1/strategys/{session_id}/share-settings
```

**요청 본문:**
```json
{
  "is_public": true,
  "is_anonymous": false,
  "show_strategy": true,
  "description": "3년간 연평균 25% 수익을 낸 가치투자 전략입니다."
}
```

**응답:**
```json
{
  "session_id": "abc123-def456",
  "is_public": true,
  "is_anonymous": false,
  "show_strategy": true,
  "description": "3년간 연평균 25% 수익을 낸 가치투자 전략입니다.",
  "share_url": "abc123de-x7K9mP2Q",
  "view_count": 0,
  "like_count": 0
}
```

---

### 3️⃣ **오늘의 TOP 투자전략 랭킹**

```http
GET /api/v1/strategys/rankings/today
```

**쿼리 파라미터:**
- `limit` (default: 10): 조회 개수
- `sort_by` (default: total_return): total_return, sharpe_ratio, like_count

**응답 예시:**
```json
[
  {
    "rank": 1,
    "sessionId": "xyz789",
    "sessionName": "퀄리티 성장주 전략",
    "description": "ROE 15% 이상, 매출 성장률 20% 이상",
    "authorName": "투자왕김씨",
    "isAnonymous": false,
    "totalReturn": 45.2,
    "annualizedReturn": 18.5,
    "sharpeRatio": 1.8,
    "maxDrawdown": -12.3,
    "volatility": 18.5,
    "totalTrades": 45,
    "winRate": 65.5,
    "showStrategy": true,
    "strategySummary": "45회 거래, 승률 65.5%",
    "viewCount": 523,
    "likeCount": 87,
    "createdAt": "2025-01-06T09:15:00"
  },
  {
    "rank": 2,
    "sessionId": "def456",
    "sessionName": "모멘텀 전략",
    "authorName": "익명",
    "isAnonymous": true,
    "totalReturn": 38.7,
    "annualizedReturn": 15.2,
    "sharpeRatio": 1.5,
    "maxDrawdown": -18.9,
    "volatility": 22.3,
    "totalTrades": 78,
    "winRate": 58.3,
    "showStrategy": false,
    "strategySummary": null,
    "viewCount": 312,
    "likeCount": 54,
    "createdAt": "2025-01-06T11:20:00"
  }
]
```

---

### 4️⃣ **전체 기간 명예의 전당**

```http
GET /api/v1/strategys/rankings/all-time
```

**쿼리 파라미터:**
- `limit` (default: 50)
- `sort_by` (default: total_return)
- `min_trades` (default: 10): 최소 거래 횟수

---

### 5️⃣ **공유 링크로 투자전략 상세 조회**

```http
GET /api/v1/strategys/shared/{share_url}
```

**인증 불필요** (공개 엔드포인트)

**응답:**
```json
{
  "sessionId": "abc123",
  "sessionName": "저PER 가치투자",
  "description": "3년간 연평균 25% 수익",
  "authorName": "투자왕김씨",
  "isAnonymous": false,
  "startDate": "2023-01-01",
  "endDate": "2024-12-31",
  "initialCapital": 100000000,
  "benchmark": "KOSPI",
  "totalReturn": 25.5,
  "annualizedReturn": 8.3,
  "sharpeRatio": 1.2,
  "maxDrawdown": -15.3,
  "volatility": 18.5,
  "winRate": 62.5,
  "showStrategy": true,
  "buyConditions": [
    {"factor": "PER", "operator": "LT", "value": 10},
    {"factor": "ROE", "operator": "GT", "value": 10}
  ],
  "sellConditions": [
    {"factor": "PROFIT_RATE", "operator": "GT", "value": 20}
  ],
  "viewCount": 524,
  "likeCount": 87,
  "createdAt": "2025-01-05T14:30:00"
}
```

---

### 6️⃣ **좋아요 토글**

```http
POST /api/v1/strategys/{session_id}/like
```

**응답:**
```json
{
  "sessionId": "abc123",
  "likeCount": 88,
  "isLiked": true
}
```

---

### 7️⃣ **투자전략 삭제**

```http
DELETE /api/v1/strategys/{session_id}
```

**응답:** 204 No Content

---

## 💡 사용 예시

### 시나리오 1: 투자전략 공개하기

```python
import requests

# 1. 로그인
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"email": "user@example.com", "password": "password123"}
)
token = login_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 2. 내 투자전략 목록 조회
strategys = requests.get(
    "http://localhost:8000/api/v1/strategys/my-strategys",
    headers=headers
).json()

session_id = strategys[0]["sessionId"]

# 3. 공유 설정 업데이트 (공개 + 익명)
requests.patch(
    f"http://localhost:8000/api/v1/strategys/{session_id}/share-settings",
    headers=headers,
    json={
        "is_public": True,
        "is_anonymous": True,  # 익명으로 공개
        "show_strategy": False,  # 전략은 비공개
        "description": "안정적인 수익을 내는 전략입니다."
    }
)
```

### 시나리오 2: 랭킹 조회

```python
# 오늘의 TOP 10 (수익률 순)
top_strategys = requests.get(
    "http://localhost:8000/api/v1/strategys/rankings/today",
    params={"limit": 10, "sort_by": "total_return"}
).json()

for strategy in top_strategys:
    print(f"{strategy['rank']}위: {strategy['sessionName']}")
    print(f"  작성자: {strategy['authorName']}")
    print(f"  수익률: {strategy['totalReturn']}%")
    print(f"  좋아요: {strategy['likeCount']}")
    print()
```

### 시나리오 3: 공유 링크로 조회

```python
# 공유 링크 받기
share_url = "abc123de-x7K9mP2Q"

# 공개 조회 (로그인 불필요)
detail = requests.get(
    f"http://localhost:8000/api/v1/strategys/shared/{share_url}"
).json()

print(f"전략명: {detail['sessionName']}")
print(f"수익률: {detail['totalReturn']}%")

if detail['showStrategy']:
    print(f"매수 조건: {detail['buyConditions']}")
else:
    print("전략 비공개")
```

---

## 🔒 프라이버시 설정

### 공개 설정 조합

| is_public | is_anonymous | show_strategy | 결과 |
|-----------|--------------|---------------|------|
| ❌ False  | -            | -             | 완전 비공개 (본인만 조회) |
| ✅ True   | ❌ False     | ❌ False      | 공개 + 이름 표시 + 전략 비공개 |
| ✅ True   | ❌ False     | ✅ True       | 공개 + 이름 표시 + 전략 공개 |
| ✅ True   | ✅ True      | ❌ False      | 공개 + 익명 + 전략 비공개 |
| ✅ True   | ✅ True      | ✅ True       | 공개 + 익명 + 전략 공개 |

### 전략 공개 시 노출 정보

**show_strategy = true일 때:**
- 매수/매도 조건 (팩터, 연산자, 임계값)
- 리밸런싱 주기
- 포지션 크기 전략
- 손절매/익절매 비율

**show_strategy = false일 때:**
- 수익률 통계만 표시
- 거래 횟수, 승률 같은 요약 정보만

---

## 📊 데이터베이스 구조

### 추가된 컬럼 (simulation_sessions)

```sql
user_id UUID NOT NULL,              -- 사용자 FK
is_public BOOLEAN DEFAULT FALSE,    -- 공개 여부
is_anonymous BOOLEAN DEFAULT FALSE, -- 익명 여부
show_strategy BOOLEAN DEFAULT FALSE,-- 전략 공개 여부
description TEXT,                   -- 투자전략 설명
share_url VARCHAR(100) UNIQUE,      -- 공유 URL
view_count INTEGER DEFAULT 0,       -- 조회수
like_count INTEGER DEFAULT 0,       -- 좋아요 수
updated_at TIMESTAMP                -- 수정일시
```

### 새로운 테이블

**user_strategy_likes** (좋아요 관리)
```sql
user_id UUID,
session_id VARCHAR(36),
created_at TIMESTAMP,
PRIMARY KEY (user_id, session_id)
```

**strategy_comments** (댓글 - 향후 기능)
```sql
comment_id SERIAL PRIMARY KEY,
session_id VARCHAR(36),
user_id UUID,
content TEXT,
created_at TIMESTAMP
```

---

## 🚀 다음 단계

### Phase 2 기능 추가

1. **댓글 기능**
   - 투자전략에 댓글 달기
   - 대댓글
   - 댓글 좋아요

2. **팔로우 시스템**
   - 우수 투자자 팔로우
   - 팔로우한 사용자의 새 전략 알림

3. **전략 북마크**
   - 관심 전략 저장
   - 나만의 전략 컬렉션

4. **투자전략 복사**
   - 공개된 전략 복제
   - 자신만의 파라미터로 백테스트

5. **실시간 랭킹**
   - Redis를 활용한 실시간 랭킹 캐싱
   - 주간/월간 랭킹

---

## 🐛 트러블슈팅

### 1. 마이그레이션 실패

**에러:** `column "user_id" already exists`
```sql
-- 컬럼 존재 확인
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'simulation_sessions'
AND column_name = 'user_id';

-- 있으면 마이그레이션 스킵
```

### 2. 기존 세션에 user_id 없음

**에러:** `null value in column "user_id" violates not-null constraint`
```sql
-- 임시 유저 생성 후 할당 (위 마이그레이션 섹션 참고)
```

### 3. share_url 중복

**에러:** `duplicate key value violates unique constraint`
```python
# 코드에서 자동 재시도 로직 추가
import secrets

def generate_unique_share_url(session_id):
    max_attempts = 5
    for _ in range(max_attempts):
        url = f"{session_id[:8]}-{secrets.token_urlsafe(8)}"
        # DB에 존재하지 않으면 반환
        if not db.query(SimulationSession).filter_by(share_url=url).first():
            return url
    raise Exception("공유 URL 생성 실패")
```

---

## 📞 문의

기능 추가 요청이나 버그 제보는 이슈로 등록해주세요!
