-- Migration: 성능 최적화 인덱스 추가
-- Date: 2025-01-24
-- Description: 페이지네이션, N+1 쿼리, 랭킹 조회 최적화를 위한 복합 인덱스 추가

-- ============================================================
-- 1. simulation_sessions 테이블 인덱스 추가
-- ============================================================

-- 페이지네이션 최적화 (내 전략 목록 조회)
-- 쿼리: SELECT * FROM simulation_sessions
--       WHERE user_id = ? AND status = 'COMPLETED'
--       ORDER BY created_at DESC LIMIT 20 OFFSET 0;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_simulation_sessions_user_status_created
ON simulation_sessions(user_id, status, created_at DESC);

COMMENT ON INDEX idx_simulation_sessions_user_status_created IS
'페이지네이션 쿼리 최적화: 사용자별 전략 목록 조회 (상태 필터링 포함)';


-- 랭킹 쿼리 최적화 (공개 전략 순위)
-- 쿼리: SELECT * FROM simulation_sessions
--       WHERE strategy_id = ? AND status = 'COMPLETED'
--       ORDER BY completed_at DESC LIMIT 1;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_simulation_sessions_strategy_status_completed
ON simulation_sessions(strategy_id, status, completed_at DESC);

COMMENT ON INDEX idx_simulation_sessions_strategy_status_completed IS
'랭킹 쿼리 최적화: 전략별 최신 완료 세션 조회';


-- ============================================================
-- 2. live_positions 테이블 인덱스 추가
-- ============================================================

-- N+1 쿼리 해결 후 selectinload 최적화
-- 쿼리: SELECT * FROM live_positions
--       WHERE strategy_id IN (uuid1, uuid2, uuid3, ...);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_live_positions_strategy_stock
ON live_positions(strategy_id, stock_code);

COMMENT ON INDEX idx_live_positions_strategy_stock IS
'Auto Trading 포지션 조회 최적화: strategy_id IN (...) 쿼리 성능 향상';


-- ============================================================
-- 인덱스 생성 확인
-- ============================================================

-- 생성된 인덱스 확인 쿼리
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname IN (
    'idx_simulation_sessions_user_status_created',
    'idx_simulation_sessions_strategy_status_completed',
    'idx_live_positions_strategy_stock'
)
ORDER BY tablename, indexname;


-- ============================================================
-- 인덱스 사이즈 확인
-- ============================================================

SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE indexname IN (
    'idx_simulation_sessions_user_status_created',
    'idx_simulation_sessions_strategy_status_completed',
    'idx_live_positions_strategy_stock'
);


-- ============================================================
-- Rollback (필요 시)
-- ============================================================

-- DROP INDEX CONCURRENTLY IF EXISTS idx_simulation_sessions_user_status_created;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_simulation_sessions_strategy_status_completed;
-- DROP INDEX CONCURRENTLY IF EXISTS idx_live_positions_strategy_stock;


-- ============================================================
-- 성능 테스트 쿼리
-- ============================================================

-- 1. 페이지네이션 쿼리 (EXPLAIN ANALYZE로 실행)
-- EXPLAIN ANALYZE
-- SELECT * FROM simulation_sessions
-- WHERE user_id = 'your-uuid-here' AND status = 'COMPLETED'
-- ORDER BY created_at DESC
-- LIMIT 20 OFFSET 0;

-- 2. N+1 해결 후 selectinload 쿼리
-- EXPLAIN ANALYZE
-- SELECT * FROM live_positions
-- WHERE strategy_id IN ('uuid1', 'uuid2', 'uuid3');

-- 3. 랭킹 쿼리
-- EXPLAIN ANALYZE
-- SELECT * FROM simulation_sessions
-- WHERE strategy_id = 'your-uuid-here' AND status = 'COMPLETED'
-- ORDER BY completed_at DESC
-- LIMIT 1;
