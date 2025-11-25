-- Phase 1: 백테스트 성능 최적화 - DB 인덱스 추가 (테이블명 복수형 반영)
-- 작성일: 2025-02-06
-- 대상: prod RDS (백테스트/시뮬레이션 결과 조회 성능 향상)

-- ==================== BacktestSessions ====================
-- 상태 + 생성일 복합 인덱스 (목록 정렬/필터)
CREATE INDEX IF NOT EXISTS idx_backtest_sessions_status_created
ON backtest_sessions(status, created_at DESC);

-- ==================== BacktestConditions ====================
-- 백테스트별 조건 타입 필터
CREATE INDEX IF NOT EXISTS idx_backtest_conditions_type
ON backtest_conditions(backtest_id, condition_type);

-- ==================== BacktestStatistics ====================
-- 수익률 정렬/랭킹 조회
CREATE INDEX IF NOT EXISTS idx_backtest_statistics_total_return_desc
ON backtest_statistics(total_return DESC);

-- ==================== BacktestTrades ====================
-- 백테스트 + 거래타입 + 날짜(최근 우선)
CREATE INDEX IF NOT EXISTS idx_backtest_trades_type_date
ON backtest_trades(backtest_id, trade_type, trade_date DESC);

-- 수익률 정렬 (NULL 제외)
CREATE INDEX IF NOT EXISTS idx_backtest_trades_profit_rate_desc
ON backtest_trades(profit_rate DESC)
WHERE profit_rate IS NOT NULL;

-- ==================== SimulationStatistics ====================
-- 수익률 정렬/랭킹 조회
CREATE INDEX IF NOT EXISTS idx_simulation_statistics_total_return_desc
ON simulation_statistics(total_return DESC);

-- ==================== SimulationTrades ====================
-- 세션 + 거래타입 + 날짜(최근 우선)
CREATE INDEX IF NOT EXISTS idx_simulation_trades_type_date
ON simulation_trades(session_id, trade_type, trade_date DESC);

-- 수익률 정렬 (NULL 제외)
CREATE INDEX IF NOT EXISTS idx_simulation_trades_return_pct_desc
ON simulation_trades(return_pct DESC)
WHERE return_pct IS NOT NULL;

-- ==================== 인덱스 목록 확인 ====================
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid::regclass)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND (
    indexrelname LIKE 'idx_backtest_%'
    OR indexrelname LIKE 'idx_simulation_%'
  )
ORDER BY tablename, indexname;
