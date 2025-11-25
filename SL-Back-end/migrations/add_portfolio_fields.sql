-- 포트폴리오 저장 기능을 위한 필드 추가
-- 2025-01-25

-- simulation_sessions 테이블에 포트폴리오 관련 필드 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS is_portfolio BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS portfolio_name VARCHAR(200) DEFAULT NULL;

ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS saved_at TIMESTAMP DEFAULT NULL;

-- 포트폴리오 조회 성능 최적화를 위한 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_simulation_sessions_portfolio
ON simulation_sessions(user_id, is_portfolio, saved_at DESC)
WHERE is_portfolio = TRUE;

-- SimulationSession 테이블에 end_time 필드가 없으면 추가
ALTER TABLE simulation_sessions
ADD COLUMN IF NOT EXISTS end_time TIMESTAMP DEFAULT NULL;

-- 기존 COMPLETED 상태인 세션의 end_time 업데이트 (없는 경우)
UPDATE simulation_sessions
SET end_time = completed_at
WHERE status = 'COMPLETED' AND end_time IS NULL;

-- 필드에 대한 주석 추가 (PostgreSQL 방식)
COMMENT ON COLUMN simulation_sessions.is_portfolio IS '포트폴리오로 저장 여부';
COMMENT ON COLUMN simulation_sessions.portfolio_name IS '포트폴리오 이름';
COMMENT ON COLUMN simulation_sessions.saved_at IS '포트폴리오 저장 시간';
COMMENT ON COLUMN simulation_sessions.end_time IS '백테스트 종료 시간';