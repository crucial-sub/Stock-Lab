-- 백테스트 전략 설정 테이블
-- AI 어시스턴트 및 포트폴리오 페이지에서 생성한 전략의 상세 설정 저장
CREATE TABLE IF NOT EXISTS strategy_configurations (
    config_id SERIAL PRIMARY KEY,
    strategy_id VARCHAR(36) NOT NULL REFERENCES portfolio_strategies(strategy_id) ON DELETE CASCADE,

    -- 기본 설정
    is_day_or_month VARCHAR(10) DEFAULT 'daily',  -- 'daily' or 'monthly'
    commission_rate DECIMAL(5, 3) DEFAULT 0.015,  -- 수수료율 (%)
    slippage DECIMAL(5, 3) DEFAULT 0.1,           -- 슬리피지 (%)

    -- 매수 조건 (JSONB)
    buy_conditions JSONB DEFAULT '[]'::jsonb,
    buy_logic VARCHAR(10) DEFAULT 'AND',          -- 'AND' or 'OR'
    priority_factor VARCHAR(50),                   -- 우선순위 팩터 (예: {PER}, {PBR})
    priority_order VARCHAR(10) DEFAULT 'desc',     -- 'desc' or 'asc'

    -- 매수 설정
    per_stock_ratio DECIMAL(5, 2) DEFAULT 5.0,    -- 종목당 투자 비율 (%)
    max_holdings INTEGER DEFAULT 20,               -- 최대 보유 종목 수
    max_buy_value DECIMAL(15, 2),                  -- 최대 매수 금액 제한
    max_daily_stock INTEGER,                       -- 일일 최대 매수 종목 수
    buy_price_basis VARCHAR(20) DEFAULT '전일 종가',  -- 매수 가격 기준
    buy_price_offset DECIMAL(5, 2) DEFAULT 0,      -- 매수 가격 offset (%)

    -- 매도 조건: 목표가/손절가
    target_and_loss JSONB,                         -- {"target_gain": 10, "stop_loss": 10}

    -- 매도 조건: 보유 기간
    hold_days JSONB,                               -- {"min_hold_days": 2, "max_hold_days": 5, "sell_price_basis": "전일 종가", "sell_price_offset": 10}

    -- 매도 조건: 조건 매도
    condition_sell JSONB,                          -- {"sell_conditions": [...], "sell_logic": "AND", "sell_price_basis": "전일 종가", "sell_price_offset": 0}

    -- 매매 대상 (JSONB)
    trade_targets JSONB DEFAULT '{}'::jsonb,       -- {"use_all_stocks": false, "selected_universes": [], "selected_themes": [], "selected_stocks": []}

    -- 리밸런싱 주기
    rebalance_frequency VARCHAR(20) DEFAULT 'monthly',  -- 'daily' or 'monthly'

    -- 타임스탬프
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 유니크 제약: 한 전략에 하나의 설정만
    UNIQUE(strategy_id)
);

-- 인덱스 추가 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_strategy_configurations_strategy_id ON strategy_configurations(strategy_id);

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_strategy_configurations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_strategy_configurations_updated_at
BEFORE UPDATE ON strategy_configurations
FOR EACH ROW
EXECUTE FUNCTION update_strategy_configurations_updated_at();

-- 코멘트 추가
COMMENT ON TABLE strategy_configurations IS 'AI 어시스턴트 및 포트폴리오 페이지에서 생성한 백테스트 전략의 상세 설정';
COMMENT ON COLUMN strategy_configurations.buy_conditions IS '매수 조건 배열 (JSON): [{"name": "A", "exp_left_side": "기본값({dividend_yield})", "inequality": ">", "exp_right_side": 50}]';
COMMENT ON COLUMN strategy_configurations.target_and_loss IS '목표가/손절가 (JSON): {"target_gain": 10, "stop_loss": 10}';
COMMENT ON COLUMN strategy_configurations.hold_days IS '보유 기간 제한 (JSON): {"min_hold_days": 2, "max_hold_days": 5, "sell_price_basis": "전일 종가", "sell_price_offset": 10}';
COMMENT ON COLUMN strategy_configurations.condition_sell IS '조건 매도 (JSON): {"sell_conditions": [...], "sell_logic": "AND", "sell_price_basis": "전일 종가", "sell_price_offset": 0}';
COMMENT ON COLUMN strategy_configurations.trade_targets IS '매매 대상 (JSON): {"use_all_stocks": false, "selected_universes": [], "selected_themes": ["부동산", "증권"], "selected_stocks": []}';
