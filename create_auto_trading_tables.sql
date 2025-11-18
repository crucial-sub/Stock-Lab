-- 자동매매 테이블 생성 SQL

-- 1. AutoTradingStrategy 테이블
CREATE TABLE IF NOT EXISTS auto_trading_strategies (
    strategy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    simulation_session_id VARCHAR NOT NULL REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,

    is_active BOOLEAN DEFAULT FALSE,

    initial_capital DECIMAL(20, 2) DEFAULT 50000000,
    current_capital DECIMAL(20, 2) DEFAULT 50000000,
    cash_balance DECIMAL(20, 2) DEFAULT 50000000,

    per_stock_ratio DECIMAL(5, 2) DEFAULT 5.0,
    max_positions INTEGER DEFAULT 20,

    rebalance_frequency VARCHAR(20) DEFAULT 'DAILY',

    buy_conditions JSONB,
    buy_logic VARCHAR(500),
    priority_factor VARCHAR(50),
    priority_order VARCHAR(10) DEFAULT 'desc',
    max_buy_value DECIMAL(20, 2),
    max_daily_stock INTEGER,
    buy_price_basis VARCHAR(20) DEFAULT '전일 종가',
    buy_price_offset DECIMAL(10, 4) DEFAULT 0,

    target_gain DECIMAL(10, 4),
    stop_loss DECIMAL(10, 4),

    min_hold_days INTEGER,
    max_hold_days INTEGER,
    hold_days_sell_price_basis VARCHAR(20),
    hold_days_sell_price_offset DECIMAL(10, 4),

    sell_conditions JSONB,
    sell_logic VARCHAR(500),
    condition_sell_price_basis VARCHAR(20),
    condition_sell_price_offset DECIMAL(10, 4),

    commission_rate DECIMAL(10, 6) DEFAULT 0.00015,
    slippage DECIMAL(10, 6) DEFAULT 0.001,

    trade_targets JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP,
    last_executed_at TIMESTAMP
);

-- 2. LivePosition 테이블
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

    unrealized_profit DECIMAL(20, 2),
    unrealized_profit_pct DECIMAL(10, 4),

    buy_factors JSONB,
    selection_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. LiveTrade 테이블
CREATE TABLE IF NOT EXISTS live_trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    trade_date DATE NOT NULL,
    trade_time TIME DEFAULT CURRENT_TIME,
    trade_type VARCHAR(10) NOT NULL,

    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),

    quantity INTEGER NOT NULL,
    price DECIMAL(20, 2) NOT NULL,
    amount DECIMAL(20, 2) NOT NULL,

    commission DECIMAL(20, 2) DEFAULT 0,
    tax DECIMAL(20, 2) DEFAULT 0,

    profit DECIMAL(20, 2),
    profit_rate DECIMAL(10, 4),
    hold_days INTEGER,

    selection_reason TEXT,
    factors JSONB,

    order_number VARCHAR(50),
    order_status VARCHAR(20) DEFAULT 'PENDING',

    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. LiveDailyPerformance 테이블
CREATE TABLE IF NOT EXISTS live_daily_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    date DATE NOT NULL,

    cash_balance DECIMAL(20, 2) NOT NULL,
    stock_value DECIMAL(20, 2) NOT NULL,
    total_value DECIMAL(20, 2) NOT NULL,

    daily_return DECIMAL(10, 4),
    cumulative_return DECIMAL(10, 4),

    buy_count INTEGER DEFAULT 0,
    sell_count INTEGER DEFAULT 0,
    trade_count INTEGER DEFAULT 0,

    position_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. AutoTradingLog 테이블
CREATE TABLE IF NOT EXISTS auto_trading_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES auto_trading_strategies(strategy_id) ON DELETE CASCADE,

    event_type VARCHAR(50) NOT NULL,
    event_level VARCHAR(20) DEFAULT 'INFO',

    message TEXT,
    details JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_live_positions_strategy ON live_positions(strategy_id);
CREATE INDEX IF NOT EXISTS idx_live_positions_stock ON live_positions(stock_code);

CREATE INDEX IF NOT EXISTS idx_live_trades_strategy ON live_trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_live_trades_date ON live_trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_live_trades_stock ON live_trades(stock_code);

CREATE INDEX IF NOT EXISTS idx_live_daily_perf_strategy ON live_daily_performance(strategy_id);
CREATE INDEX IF NOT EXISTS idx_live_daily_perf_date ON live_daily_performance(date);

CREATE INDEX IF NOT EXISTS idx_auto_trading_logs_strategy ON auto_trading_logs(strategy_id);
CREATE INDEX IF NOT EXISTS idx_auto_trading_logs_event_type ON auto_trading_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_auto_trading_logs_created ON auto_trading_logs(created_at DESC);
