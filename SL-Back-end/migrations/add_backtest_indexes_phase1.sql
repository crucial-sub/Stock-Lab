-- Phase 1: 백테스트 성능 최적화 - DB 인덱스 추가
-- 작성일: 2025-01-24
-- 목적: 백테스트 결과 조회 성능 향상 (50% 이상 속도 개선 목표)

-- ==================== BacktestSession 테이블 인덱스 ====================

-- 1. 사용자별 백테스트 목록 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_session_user_created
ON backtest_session(user_id, created_at DESC)
WHERE user_id IS NOT NULL;

-- 2. 상태별 백테스트 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_session_status_created
ON backtest_session(status, created_at DESC);

-- 3. 백테스트 ID 기반 조회 최적화 (UNIQUE 인덱스)
CREATE UNIQUE INDEX IF NOT EXISTS idx_backtest_session_backtest_id
ON backtest_session(backtest_id);

-- ==================== BacktestCondition 테이블 인덱스 ====================

-- 4. 백테스트 ID로 조건 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_condition_backtest_id
ON backtest_condition(backtest_id);

-- 5. 조건 타입별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_condition_type
ON backtest_condition(backtest_id, condition_type);

-- ==================== BacktestStatistics 테이블 인덱스 ====================

-- 6. 백테스트 ID로 통계 조회 최적화 (UNIQUE 인덱스)
CREATE UNIQUE INDEX IF NOT EXISTS idx_backtest_statistics_backtest_id
ON backtest_statistics(backtest_id);

-- 7. 수익률 기준 정렬 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_statistics_total_return
ON backtest_statistics(total_return DESC);

-- ==================== BacktestDailySnapshot 테이블 인덱스 ====================

-- 8. 백테스트 ID + 날짜 복합 인덱스 (UNIQUE)
CREATE UNIQUE INDEX IF NOT EXISTS idx_backtest_daily_snapshot_id_date
ON backtest_daily_snapshot(backtest_id, snapshot_date DESC);

-- 9. 날짜 범위 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_daily_snapshot_date
ON backtest_daily_snapshot(snapshot_date DESC);

-- ==================== BacktestTrade 테이블 인덱스 ====================

-- 10. 백테스트 ID로 거래 내역 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_trade_backtest_id
ON backtest_trade(backtest_id, trade_date DESC);

-- 11. 거래 타입별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_trade_type
ON backtest_trade(backtest_id, trade_type, trade_date DESC);

-- 12. 종목별 거래 내역 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_trade_stock
ON backtest_trade(stock_code, trade_date DESC);

-- 13. 수익률 기준 거래 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_trade_profit_rate
ON backtest_trade(backtest_id, profit_rate DESC)
WHERE profit_rate IS NOT NULL;

-- ==================== BacktestHolding 테이블 인덱스 ====================

-- 14. 백테스트 ID로 보유 종목 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_holding_backtest_id
ON backtest_holding(backtest_id);

-- 15. 종목 코드로 보유 내역 조회 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_holding_stock
ON backtest_holding(stock_code);

-- ==================== SimulationStatistics 테이블 인덱스 ====================

-- 16. 세션 ID로 통계 조회 최적화 (UNIQUE 인덱스)
CREATE UNIQUE INDEX IF NOT EXISTS idx_simulation_statistics_session_id
ON simulation_statistics(session_id);

-- 17. 수익률 기준 정렬 조회 최적화
CREATE INDEX IF NOT EXISTS idx_simulation_statistics_total_return
ON simulation_statistics(total_return DESC);

-- ==================== 복합 인덱스 (성능 집중 최적화) ====================

-- 18. 백테스트 목록 조회 최적화 (사용자 + 상태 + 날짜)
CREATE INDEX IF NOT EXISTS idx_backtest_session_user_status_date
ON backtest_session(user_id, status, created_at DESC)
WHERE user_id IS NOT NULL;

-- 19. 거래 내역 페이징 최적화
CREATE INDEX IF NOT EXISTS idx_backtest_trade_pagination
ON backtest_trade(backtest_id, trade_date DESC, id);

-- ==================== 인덱스 생성 완료 ====================

-- 인덱스 생성 통계 조회
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    indexname LIKE 'idx_backtest_%'
    OR indexname LIKE 'idx_simulation_%'
  )
ORDER BY tablename, indexname;

-- 각 테이블의 인덱스 개수 확인
SELECT
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    tablename LIKE 'backtest_%'
    OR tablename = 'simulation_statistics'
  )
GROUP BY tablename
ORDER BY tablename;

-- 인덱스 크기 확인
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid::regclass)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND (
    indexrelname LIKE 'idx_backtest_%'
    OR indexrelname LIKE 'idx_simulation_%'
  )
ORDER BY pg_relation_size(indexrelid::regclass) DESC;

-- ==================== 사용 가이드 ====================

/*
인덱스 적용 방법:
1. PostgreSQL 데이터베이스 접속
   psql -U stocklabadmin -d stock_lab_investment_db

2. 마이그레이션 파일 실행
   \i /path/to/add_backtest_indexes_phase1.sql

3. 인덱스 적용 확인
   - 위의 통계 조회 쿼리가 자동 실행됨
   - 각 테이블에 필요한 인덱스가 모두 생성되었는지 확인

4. 성능 개선 확인
   - EXPLAIN ANALYZE를 사용하여 쿼리 실행 계획 확인
   - 백테스트 목록 조회, 거래 내역 조회 등의 속도 측정

예상 성능 개선:
- 백테스트 목록 조회: 50-70% 속도 향상
- 거래 내역 조회: 60-80% 속도 향상
- 일별 스냅샷 조회: 40-60% 속도 향상
- 통계 조회: 80-90% 속도 향상 (UNIQUE 인덱스)

주의사항:
- 인덱스 생성은 테이블 크기에 따라 시간이 걸릴 수 있음
- CONCURRENT 옵션을 사용하지 않아 생성 중 테이블 락 발생 가능
- 운영 환경에서는 트래픽이 적은 시간대에 실행 권장
*/
