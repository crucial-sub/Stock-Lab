# 커뮤니티 기능 명세서

## 개요
커뮤니티 기능은 크게 3가지로 구성됩니다:
1. **수익률 랭킹** - 공개 전략의 수익률 순위 (상위 3개)
2. **포트폴리오 공유** - 전략 공유 게시글
3. **자유게시판** - 일반 커뮤니티 게시판

---

## 1. 수익률 랭킹

### 기능
- `is_public=True`인 전략만 포함
- `total_return` 기준 상위 3개만 메인 페이지에 표시
- **1시간마다 업데이트** (캐싱)

### 표시 정보
- `strategy_name` (제목)
- `user_nickname` (작성자)
- `total_return` (최종 수익률)
- **복제하기** 버튼

### 동작
1. **제목 클릭** → 백테스트 결과 페이지로 이동 (`/backtest/result/{session_id}`)
2. **복제하기 버튼** → `TradingRule`의 `buy_condition`, `sell_condition` JSON 복사 → 백테스트 창으로 이동 (`/quant/new`)

### 데이터 소스
```sql
SELECT
    ps.strategy_name,
    u.nickname as user_nickname,
    stats.total_return,
    ss.session_id
FROM portfolio_strategies ps
JOIN simulation_sessions ss ON ss.strategy_id = ps.strategy_id
JOIN simulation_statistics stats ON stats.session_id = ss.session_id
JOIN users u ON u.user_id = ps.user_id
WHERE ps.is_public = TRUE
  AND ss.status = 'COMPLETED'
ORDER BY stats.total_return DESC
LIMIT 3;
```

### API 엔드포인트
- `GET /api/community/rankings/top` - 상위 3개 랭킹 조회
- `GET /api/strategies/{strategy_id}/clone-data` - 전략 복제 데이터 조회

---

## 2. 포트폴리오 공유 게시글

### 기능
- 게시글 형태로 전략 공유
- 포트폴리오 추가하기 버튼 클릭 시 → 내 전략 포트폴리오에 복사

### 표시 정보
- `strategy_name` (제목)
- `user_nickname` (작성자)
- `total_return` (최종 수익률)
- `description` (사용자 입력 설명)
- **포트폴리오 추가하기** 버튼

### 동작
1. **포트폴리오 추가하기** → 전략 데이터 전체 복사 (`PortfolioStrategy` + `TradingRule` + `StrategyFactor`)
2. 복사된 전략이 내 전략 포트폴리오 카드에 추가됨

### 데이터 모델
**테이블**: `community_posts`
- `post_type = 'STRATEGY_SHARE'`로 필터링
- `strategy_snapshot`: 전략 정보 JSON
- `session_snapshot`: 백테스트 결과 JSON

### 스냅샷 구조
```json
{
  "strategy_snapshot": {
    "strategy_name": "모멘텀 전략",
    "strategy_type": "MOMENTUM",
    "description": "...",
    "buy_conditions": [...],
    "sell_conditions": {...},
    "trade_targets": {...}
  },
  "session_snapshot": {
    "initial_capital": 50000000,
    "period": {"start": "2024-01-01", "end": "2024-06-30"},
    "statistics": {
      "total_return": 15.5,
      "sharpe_ratio": 1.2,
      "max_drawdown": -8.3
    }
  }
}
```

### API 엔드포인트
- `GET /api/community/posts?type=STRATEGY_SHARE` - 포트폴리오 공유 게시글 목록
- `POST /api/community/posts/share-strategy` - 포트폴리오 공유 게시글 작성
- `POST /api/strategies/clone/{share_id}` - 포트폴리오 복제

---

## 3. 자유게시판

### 목록 페이지 표시 정보
- `tags` (태그)
- `title` (제목)
- `user_nickname` (작성자)
- `created_at` (작성날짜+시간)
- `content` (간략하게 - 한 줄 + `...`)
- `view_count` (조회수)
- `like_count` (좋아요 수)
- `comment_count` (댓글 수)

### 상세 페이지 표시 정보
- `tags` (태그)
- `title` (제목)
- `user_nickname` (작성자)
- `created_at` (작성날짜+시간)
- `view_count` (조회수)
- `like_count` (좋아요 수)
- `comment_count` (댓글 수)
- `content` (전체 내용)
- **좋아요 버튼** (토글: 좋아요 ↔ 좋아요 취소)
- **댓글 작성 칸** + 댓글 작성 버튼
- **대댓글 작성 버튼** → 대댓글 작성 칸

### 댓글 기능
- **댓글 작성**: `parent_comment_id = NULL`
- **대댓글 작성**: `parent_comment_id = {부모 댓글 ID}`
- 댓글에도 좋아요 가능

### 데이터 모델
**테이블**: `community_posts`
- `post_type = 'DISCUSSION'` or `'QUESTION'`

**테이블**: `community_comments`
- `parent_comment_id`: 대댓글인 경우 부모 댓글 ID

**테이블**: `community_likes` (게시글 좋아요)
**테이블**: `community_comment_likes` (댓글 좋아요)

### API 엔드포인트

#### 게시글
- `GET /api/community/posts` - 게시글 목록 조회
- `GET /api/community/posts/{post_id}` - 게시글 상세 조회 (조회수 +1)
- `POST /api/community/posts` - 게시글 작성
- `PUT /api/community/posts/{post_id}` - 게시글 수정
- `DELETE /api/community/posts/{post_id}` - 게시글 삭제

#### 댓글
- `GET /api/community/posts/{post_id}/comments` - 댓글 목록 조회
- `POST /api/community/posts/{post_id}/comments` - 댓글 작성
- `POST /api/community/comments/{comment_id}/replies` - 대댓글 작성
- `PUT /api/community/comments/{comment_id}` - 댓글 수정
- `DELETE /api/community/comments/{comment_id}` - 댓글 삭제

#### 좋아요
- `POST /api/community/posts/{post_id}/like` - 게시글 좋아요 (토글)
- `POST /api/community/comments/{comment_id}/like` - 댓글 좋아요 (토글)

---

## DB 스키마

### 수정된 테이블

#### `users`
```sql
ALTER TABLE users ADD COLUMN nickname VARCHAR(50) UNIQUE;
CREATE INDEX idx_users_nickname ON users(nickname);
```

#### `community_posts`
```sql
ALTER TABLE community_posts ADD COLUMN tags JSON;
```

#### `community_comments`
```sql
ALTER TABLE community_comments ADD COLUMN like_count INTEGER DEFAULT 0;
```

### 새로 추가된 테이블

#### `community_comment_likes`
```sql
CREATE TABLE community_comment_likes (
    like_id SERIAL PRIMARY KEY,
    comment_id VARCHAR(36) NOT NULL REFERENCES community_comments(comment_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_comment_user_like UNIQUE (comment_id, user_id)
);
CREATE INDEX idx_community_comment_likes_comment ON community_comment_likes(comment_id);
CREATE INDEX idx_community_comment_likes_user ON community_comment_likes(user_id, created_at);
```

---

## 마이그레이션 명령어

```bash
# 1. 마이그레이션 생성
alembic revision --autogenerate -m "Add community features: nickname, tags, comment_likes"

# 2. 마이그레이션 적용
alembic upgrade head
```

---

## 구현 우선순위

### Phase 1: 기본 자유게시판
- [ ] 게시글 CRUD API
- [ ] 댓글/대댓글 CRUD API
- [ ] 좋아요 토글 API
- [ ] 조회수 증가 로직

### Phase 2: 수익률 랭킹
- [ ] 랭킹 조회 API (캐싱)
- [ ] 전략 복제 API

### Phase 3: 포트폴리오 공유
- [ ] 포트폴리오 공유 게시글 작성 API
- [ ] 포트폴리오 복제 API
- [ ] 스냅샷 생성 로직

---

## 프론트엔드 라우팅

```
/community                     # 커뮤니티 메인 (랭킹 + 최신 게시글)
/community/rankings            # 수익률 랭킹 전체 목록
/community/share               # 포트폴리오 공유 게시글 목록
/community/board               # 자유게시판 목록
/community/board/new           # 게시글 작성
/community/board/{post_id}     # 게시글 상세
```

---

## 캐싱 전략

### 수익률 랭킹 (Redis)
```python
# 1시간마다 갱신
CACHE_KEY = "community:rankings:top3"
CACHE_TTL = 3600  # 1 hour

async def get_top_rankings():
    cached = await redis.get(CACHE_KEY)
    if cached:
        return json.loads(cached)

    # DB 조회
    rankings = await db.execute(query)

    # 캐시 저장
    await redis.setex(CACHE_KEY, CACHE_TTL, json.dumps(rankings))

    return rankings
```

---

## 보안 고려사항

1. **XSS 방지**: 게시글/댓글 내용 HTML 이스케이프
2. **SQL Injection 방지**: ORM 사용 (SQLAlchemy)
3. **Rate Limiting**: 게시글/댓글 작성 제한 (1분에 5회)
4. **권한 확인**: 본인 게시글/댓글만 수정/삭제 가능
5. **Soft Delete**: 삭제 시 실제 삭제 대신 `is_deleted=True` 플래그

---

## 알림 기능 (추후 확장)

- 내 게시글에 댓글 달림
- 내 댓글에 대댓글 달림
- 내 게시글/댓글에 좋아요 받음
