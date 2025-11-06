-- 투자전략 공유 기능 추가 마이그레이션
-- 작성일: 2025-01-06
-- 설명: user_id FK, 공유 설정 필드, 커뮤니티 기능 추가

-- 1. simulation_sessions 테이블에 user_id 컬럼 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(user_id);

-- 기존 데이터가 있을 경우 임시 user 생성 (선택)
-- INSERT INTO users (user_id, name, email, phone_number, hashed_password)
-- VALUES (
--     '00000000-0000-0000-0000-000000000000',
--     'System',
--     'system@example.com',
--     '00000000000',
--     'hashed_password_placeholder'
-- )
-- ON CONFLICT DO NOTHING;

-- 기존 데이터에 user_id 설정 (선택)
-- UPDATE simulation_sessions
-- SET user_id = '00000000-0000-0000-0000-000000000000'
-- WHERE user_id IS NULL;

-- user_id를 NOT NULL로 변경 (기존 데이터 처리 후)
-- ALTER TABLE simulation_sessions
-- ALTER COLUMN user_id SET NOT NULL;

-- 2. 공유 설정 컬럼 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN DEFAULT FALSE;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS show_strategy BOOLEAN DEFAULT FALSE;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS share_url VARCHAR(100) UNIQUE;

-- 3. 커뮤니티 기능 컬럼 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS like_count INTEGER DEFAULT 0;

-- 4. updated_at 컬럼 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 5. 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_simulation_sessions_user_id
ON simulation_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_simulation_sessions_user_created
ON simulation_sessions(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_simulation_sessions_public_created
ON simulation_sessions(is_public, created_at);

CREATE INDEX IF NOT EXISTS idx_simulation_sessions_share_url
ON simulation_sessions(share_url);

-- 6. 성능 최적화를 위한 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_simulation_sessions_public_status_created
ON simulation_sessions(is_public, status, created_at)
WHERE status = 'COMPLETED';

-- 7. 좋아요 관리 테이블 생성 (선택 - 중복 좋아요 방지)
CREATE TABLE IF NOT EXISTS user_strategy_likes (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(36) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, session_id)
);

CREATE INDEX IF NOT EXISTS idx_user_strategy_likes_session
ON user_strategy_likes(session_id);

-- 8. 댓글 테이블 생성 (선택 - 향후 커뮤니티 기능)
CREATE TABLE IF NOT EXISTS strategy_comments (
    comment_id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_strategy_comments_session
ON strategy_comments(session_id, created_at);

-- 9. 통계 테이블에 랭킹용 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_simulation_statistics_total_return
ON simulation_statistics(total_return DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_simulation_statistics_sharpe_ratio
ON simulation_statistics(sharpe_ratio DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_simulation_statistics_annualized_return
ON simulation_statistics(annualized_return DESC NULLS LAST);

-- 10. 업데이트 트리거 생성 (updated_at 자동 갱신)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_simulation_sessions_updated_at ON simulation_sessions;

CREATE TRIGGER update_simulation_sessions_updated_at
BEFORE UPDATE ON simulation_sessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '투자전략 공유 기능 마이그레이션이 완료되었습니다.';
    RAISE NOTICE '추가된 기능:';
    RAISE NOTICE '  - user_id FK (사용자 연결)';
    RAISE NOTICE '  - 공유 설정 (is_public, is_anonymous, show_strategy)';
    RAISE NOTICE '  - 커뮤니티 기능 (view_count, like_count)';
    RAISE NOTICE '  - 좋아요 관리 테이블 (user_strategy_likes)';
    RAISE NOTICE '  - 댓글 기능 (strategy_comments)';
END $$;
