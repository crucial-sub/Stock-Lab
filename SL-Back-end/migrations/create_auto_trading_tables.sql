-- 자동매매 전략 설정 테이블
CREATE TABLE IF NOT EXISTS auto_trading_strategies (
    strategy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    simulation_session_id VARCHAR NOT NULL REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,

    -- 활성화 상태
    is_active BOOLEAN DEFAULT FALSE,

    -- 매매 설정
    initial_capital DECIMAL(20, 2) DEFAULT 50000000,  -- 초기 자본금 (모의투자)
    current_capital DECIMAL(20, 2) DEFAULT 50000000,  -- 현재 총 자산
    cash_balance DECIMAL(20, 2) DEFAULT 50000000,     -- 현금 잔액

    per_stock_ratio DECIMAL(5, 2) DEFAULT 5.0,        -- 종목당 투자 비율 (%)
    max_positions INTEGER DEFAULT 20,                  -- 최대 보유 종목 수

    -- 리밸런싱 주기
    rebalance_frequency VARCHAR(20) DEFAULT 'DAILY',   -- DAILY, MONTHLY

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP,
    last_executed_at TIMESTAMP  -- 마지막 실행 시간
);

-- 실시간 보유 종목 (포지션)
CREATE TABLE IF NOT EXISTS live_positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),

    quantity INTEGER NOT NULL,
    avg_buy_price DECIMAL(20, 2) NOT NULL,
    current_price DECIMAL(20, 2),

    buy_date DATE NOT NULL,
    hold_days INTEGER DEFAULT 0,

    -- 평가 손익
    unrealized_profit DECIMAL(20, 2),
    unrealized_profit_pct DECIMAL(10, 4),

    -- 메타 정보 (매수 근거)
    buy_factors JSONB,
    selection_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_position_per_strategy UNIQUE (strategy_id, stock_code)
);

-- 실시간 매매 내역
CREATE TABLE IF NOT EXISTS live_trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    trade_date DATE NOT NULL,
    trade_time TIME DEFAULT CURRENT_TIME,
    trade_type VARCHAR(10) NOT NULL,  -- BUY, SELL

    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),

    quantity INTEGER NOT NULL,
    price DECIMAL(20, 2) NOT NULL,
    amount DECIMAL(20, 2) NOT NULL,

    -- 비용
    commission DECIMAL(20, 2) DEFAULT 0,
    tax DECIMAL(20, 2) DEFAULT 0,

    -- 매도 시에만 (실현 손익)
    profit DECIMAL(20, 2),
    profit_rate DECIMAL(10, 4),
    hold_days INTEGER,

    -- 매매 근거
    selection_reason TEXT,
    factors JSONB,

    -- 키움 API 주문 정보
    order_number VARCHAR(50),
    order_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, FILLED, CANCELLED, FAILED

    created_at TIMESTAMP DEFAULT NOW()
);

-- 자동매매 일일 성과
CREATE TABLE IF NOT EXISTS live_daily_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    date DATE NOT NULL,

    -- 자산 현황
    cash_balance DECIMAL(20, 2) NOT NULL,
    stock_value DECIMAL(20, 2) NOT NULL,
    total_value DECIMAL(20, 2) NOT NULL,

    -- 수익률
    daily_return DECIMAL(10, 4),
    cumulative_return DECIMAL(10, 4),

    -- 거래 통계
    buy_count INTEGER DEFAULT 0,
    sell_count INTEGER DEFAULT 0,
    trade_count INTEGER DEFAULT 0,

    -- 보유 종목 수
    position_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_strategy_date UNIQUE (strategy_id, date)
);

-- 자동매매 이벤트 로그 (디버깅 및 감사용)
CREATE TABLE IF NOT EXISTS auto_trading_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    event_type VARCHAR(50) NOT NULL,  -- ACTIVATED, DEACTIVATED, STOCK_SELECTED, ORDER_PLACED, ORDER_FILLED, ERROR
    event_level VARCHAR(20) DEFAULT 'INFO',  -- INFO, WARNING, ERROR

    message TEXT,
    details JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_auto_trading_strategies_user ON auto_trading_strategies(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_auto_trading_strategies_active ON auto_trading_strategies(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_live_positions_strategy ON live_positions(strategy_id);
CREATE INDEX IF NOT EXISTS idx_live_trades_strategy_date ON live_trades(strategy_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_live_trades_stock ON live_trades(stock_code, trade_date);
CREATE INDEX IF NOT EXISTS idx_live_performance_strategy ON live_daily_performance(strategy_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_auto_trading_logs_strategy ON auto_trading_logs(strategy_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_auto_trading_logs_type ON auto_trading_logs(event_type, created_at DESC);

-- 코멘트 추가
COMMENT ON TABLE auto_trading_strategies IS '자동매매 전략 설정 (모의투자 전용)';
COMMENT ON TABLE live_positions IS '실시간 보유 종목 (자동매매)';
COMMENT ON TABLE live_trades IS '실시간 매매 내역 (자동매매)';
COMMENT ON TABLE live_daily_performance IS '자동매매 일일 성과';
COMMENT ON TABLE auto_trading_logs IS '자동매매 이벤트 로그';
