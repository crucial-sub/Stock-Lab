-- 백테스트 성능 최적화를 위한 인덱스 추가

-- 1. stock_prices 테이블 복합 인덱스 (백테스트 핵심 쿼리 최적화)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stock_prices_backtest
ON stock_prices(trade_date, company_id, close_price, volume);

-- 2. stock_prices 날짜 범위 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stock_prices_date_range
ON stock_prices(company_id, trade_date DESC);

-- 3. companies 테이블 industry 인덱스 (이미 있을 수 있음)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_companies_industry_stock
ON companies(industry, stock_code) WHERE stock_code IS NOT NULL;

-- 4. financial_statements 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_statements_company_year
ON financial_statements(company_id, bsns_year DESC, reprt_code DESC);

-- 5. balance_sheets 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_balance_sheets_stmt_account
ON balance_sheets(stmt_id, account_nm);

-- 6. income_statements 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_income_statements_stmt_account
ON income_statements(stmt_id, account_nm);

-- 7. cashflow_statements 조회 최적화
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cashflow_statements_stmt_account
ON cashflow_statements(stmt_id, account_nm);

-- 인덱스 생성 확인
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND (
    indexname LIKE 'idx_stock_prices_%' OR
    indexname LIKE 'idx_companies_%' OR
    indexname LIKE 'idx_financial_%' OR
    indexname LIKE 'idx_balance_%' OR
    indexname LIKE 'idx_income_%' OR
    indexname LIKE 'idx_cashflow_%'
)
ORDER BY tablename, indexname;
