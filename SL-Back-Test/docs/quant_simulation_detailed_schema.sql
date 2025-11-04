-- =====================================================
-- 퀀트 투자 시뮬레이션 시스템 테이블 구조
-- GenPort 스타일의 백테스팅 플랫폼
-- =====================================================

-- =====================================================
-- PART 1: 팩터 및 조건식 관리
-- =====================================================

-- 팩터 카테고리 마스터
CREATE TABLE factor_categories (
    category_id VARCHAR(20) PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    category_name_en VARCHAR(50),
    description TEXT,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_display_order (display_order)
);

-- 팩터 마스터 테이블
CREATE TABLE factors (
    factor_id VARCHAR(30) PRIMARY KEY,
    category_id VARCHAR(20) NOT NULL,
    factor_name VARCHAR(100) NOT NULL,
    factor_name_en VARCHAR(100),
    description TEXT,
    
    -- 팩터 계산 정보
    calculation_type VARCHAR(20),       -- FUNDAMENTAL, TECHNICAL, ALTERNATIVE
    formula TEXT,                       -- 계산 공식
    data_source VARCHAR(30),           -- 데이터 소스
    update_frequency VARCHAR(20),       -- DAILY, MONTHLY, QUARTERLY
    
    -- 표시 정보
    unit VARCHAR(20),                  -- %, 원, 배수 등
    decimal_places INT DEFAULT 2,
    display_format VARCHAR(20),        -- NUMBER, PERCENTAGE, CURRENCY
    display_order INT DEFAULT 0,
    
    -- 정규화 정보
    normalization_method VARCHAR(20),   -- Z_SCORE, MIN_MAX, PERCENTILE
    outlier_treatment VARCHAR(20),      -- WINSORIZE, TRIM, NONE
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES factor_categories(category_id),
    INDEX idx_category (category_id),
    INDEX idx_active (is_active)
);

-- 조건식 템플릿 (사용자가 저장한 조건식)
CREATE TABLE condition_templates (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_type VARCHAR(20),          -- SCREENING, RANKING, SCORING
    description TEXT,
    
    -- 조건식 내용
    conditions JSON,                    -- 조건식 상세 (JSON 형태로 저장)
    /* JSON 구조 예시:
    {
        "operator": "AND",
        "conditions": [
            {
                "factor_id": "PER",
                "operator": "LESS_THAN",
                "value": 10,
                "weight": 1.0
            },
            {
                "factor_id": "ROE",
                "operator": "GREATER_THAN",
                "value": 15,
                "weight": 1.0
            }
        ]
    }
    */
    
    -- 메타 정보
    created_by VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,    -- 공개 템플릿 여부
    usage_count INT DEFAULT 0,          -- 사용 횟수
    avg_performance DECIMAL(8,4),       -- 평균 수익률
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_template_type (template_type),
    INDEX idx_public (is_public)
);

-- =====================================================
-- PART 2: 포트폴리오 전략 설정
-- =====================================================

-- 포트폴리오 전략 마스터
CREATE TABLE portfolio_strategies (
    strategy_id VARCHAR(36) PRIMARY KEY,   -- UUID
    strategy_name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(30),             -- FACTOR, MOMENTUM, VALUE, GROWTH, QUALITY, LOW_VOL
    description TEXT,
    
    -- 생성자 정보
    user_id VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,     -- 시스템 제공 템플릿
    
    -- 백테스트 설정
    backtest_start_date DATE,
    backtest_end_date DATE,
    initial_capital DECIMAL(15,0) DEFAULT 100000000,  -- 1억원
    
    -- 유니버스 설정
    universe_type VARCHAR(30),             -- KOSPI, KOSDAQ, KOSPI200, CUSTOM
    market_cap_filter VARCHAR(20),         -- LARGE, MID, SMALL, ALL
    min_market_cap BIGINT,                 -- 최소 시가총액
    max_market_cap BIGINT,                 -- 최대 시가총액
    
    -- 섹터/업종 필터
    sector_filter JSON,                    -- 포함/제외 섹터 리스트
    exclude_stocks JSON,                   -- 제외 종목 리스트
    
    -- 유동성 필터
    min_trading_volume BIGINT,             -- 최소 거래량
    min_trading_value DECIMAL(15,0),       -- 최소 거래대금
    liquidity_days INT DEFAULT 20,         -- 유동성 체크 기간
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id),
    INDEX idx_public (is_public),
    INDEX idx_strategy_type (strategy_type)
);

-- 전략별 팩터 설정
CREATE TABLE strategy_factors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_id VARCHAR(36) NOT NULL,
    factor_id VARCHAR(30) NOT NULL,
    
    -- 팩터 사용 방법
    usage_type VARCHAR(20),                -- SCREENING, RANKING, SCORING, WEIGHTING
    
    -- 스크리닝 조건
    operator VARCHAR(20),                  -- GT, GTE, LT, LTE, EQ, BETWEEN, TOP_N, BOTTOM_N
    threshold_value DECIMAL(20,4),
    threshold_value2 DECIMAL(20,4),        -- BETWEEN 연산자용
    percentile_rank INT,                   -- 상위/하위 N%
    
    -- 스코어링/가중치
    weight DECIMAL(6,4) DEFAULT 1.0,       -- 팩터 가중치
    direction VARCHAR(10),                 -- POSITIVE, NEGATIVE (높을수록 좋은지/나쁜지)
    
    -- 정규화
    use_normalization BOOLEAN DEFAULT TRUE,
    normalization_period INT DEFAULT 12,   -- 정규화 기간(월)
    
    apply_order INT DEFAULT 0,             -- 적용 순서
    
    FOREIGN KEY (strategy_id) REFERENCES portfolio_strategies(strategy_id) ON DELETE CASCADE,
    FOREIGN KEY (factor_id) REFERENCES factors(factor_id),
    UNIQUE KEY uk_strategy_factor (strategy_id, factor_id, usage_type),
    INDEX idx_factor (factor_id)
);

-- 매매 규칙 설정
CREATE TABLE trading_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_id VARCHAR(36) NOT NULL,
    rule_type VARCHAR(20) NOT NULL,        -- BUY, SELL, REBALANCE, STOP_LOSS, TAKE_PROFIT
    rule_name VARCHAR(100),
    
    -- 리밸런싱 설정
    rebalance_frequency VARCHAR(20),       -- DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
    rebalance_day INT,                     -- 매월 N일, 매주 N요일
    
    -- 포트폴리오 구성
    position_sizing VARCHAR(30),           -- EQUAL_WEIGHT, MARKET_CAP, RISK_PARITY, FACTOR_WEIGHT
    max_positions INT DEFAULT 20,          -- 최대 보유 종목 수
    min_positions INT DEFAULT 5,           -- 최소 보유 종목 수
    max_position_weight DECIMAL(5,2),      -- 최대 종목 비중 (%)
    min_position_weight DECIMAL(5,2),      -- 최소 종목 비중 (%)
    
    -- 매수 조건
    buy_condition JSON,                    -- 매수 조건 상세
    /* JSON 예시:
    {
        "signal_type": "CROSS_ABOVE",
        "indicator1": "PRICE",
        "indicator2": "MA_20",
        "confirmation_days": 1
    }
    */
    
    -- 매도 조건
    sell_condition JSON,                   -- 매도 조건 상세
    /* JSON 예시:
    {
        "conditions": [
            {
                "type": "STOP_LOSS",
                "value": -10,
                "unit": "PERCENTAGE"
            },
            {
                "type": "TRAILING_STOP",
                "value": -5,
                "unit": "PERCENTAGE"
            },
            {
                "type": "HOLDING_PERIOD",
                "value": 60,
                "unit": "DAYS"
            }
        ]
    }
    */
    
    -- 리스크 관리
    stop_loss_pct DECIMAL(5,2),           -- 손절 비율
    take_profit_pct DECIMAL(5,2),         -- 익절 비율
    trailing_stop_pct DECIMAL(5,2),       -- 트레일링 스탑
    max_holding_period INT,                -- 최대 보유 기간(일)
    
    -- 거래 비용
    commission_type VARCHAR(20),           -- PERCENTAGE, FIXED
    commission_rate DECIMAL(6,4),          -- 수수료율
    tax_rate DECIMAL(6,4),                -- 세금율
    slippage DECIMAL(6,4),                -- 슬리피지
    
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (strategy_id) REFERENCES portfolio_strategies(strategy_id) ON DELETE CASCADE,
    INDEX idx_rule_type (rule_type)
);

-- =====================================================
-- PART 3: 시뮬레이션 실행 및 결과
-- =====================================================

-- 시뮬레이션 실행 세션
CREATE TABLE simulation_sessions (
    session_id VARCHAR(36) PRIMARY KEY,    -- UUID
    strategy_id VARCHAR(36) NOT NULL,
    session_name VARCHAR(200),
    
    -- 실행 기간
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    
    -- 초기 설정
    initial_capital DECIMAL(15,0),
    benchmark VARCHAR(30),                 -- KOSPI, KOSDAQ, 또는 특정 종목
    
    -- 실행 상태
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    progress INT DEFAULT 0,                -- 진행률 (0-100)
    
    -- 실행 시간
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    execution_time_seconds INT,
    
    -- 에러 정보
    error_message TEXT,
    warning_messages JSON,                 -- 경고 메시지 리스트
    
    -- 실행 환경
    execution_mode VARCHAR(20),            -- BACKTEST, PAPER, LIVE
    server_id VARCHAR(50),
    version VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (strategy_id) REFERENCES portfolio_strategies(strategy_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 시뮬레이션 통계 결과
CREATE TABLE simulation_statistics (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- 기본 정보
    total_trading_days INT,
    total_holding_days INT,
    
    -- 수익률 지표
    total_return DECIMAL(10,4),           -- 총 수익률 (%)
    annualized_return DECIMAL(10,4),      -- 연환산 수익률 (CAGR) (%)
    benchmark_return DECIMAL(10,4),       -- 벤치마크 수익률 (%)
    excess_return DECIMAL(10,4),          -- 초과 수익률 (%)
    
    -- 월별/연도별 수익률
    monthly_returns JSON,                  -- 월별 수익률 배열
    yearly_returns JSON,                   -- 연도별 수익률 배열
    
    -- 리스크 지표
    volatility DECIMAL(10,4),             -- 변동성 (연환산) (%)
    benchmark_volatility DECIMAL(10,4),    -- 벤치마크 변동성 (%)
    downside_volatility DECIMAL(10,4),     -- 하방 변동성 (%)
    
    -- 리스크 조정 수익률
    sharpe_ratio DECIMAL(8,4),            -- 샤프 비율
    sortino_ratio DECIMAL(8,4),           -- 소르티노 비율
    information_ratio DECIMAL(8,4),        -- 정보 비율
    calmar_ratio DECIMAL(8,4),            -- 칼마 비율
    
    -- 손실 지표
    max_drawdown DECIMAL(8,4),            -- 최대 낙폭 (MDD) (%)
    max_drawdown_days INT,                 -- MDD 지속 기간
    average_drawdown DECIMAL(8,4),         -- 평균 낙폭 (%)
    recovery_factor DECIMAL(8,4),          -- 회복 계수
    
    -- 거래 통계
    total_trades INT,                      -- 총 거래 횟수
    winning_trades INT,                    -- 수익 거래 횟수
    losing_trades INT,                     -- 손실 거래 횟수
    win_rate DECIMAL(5,2),                -- 승률 (%)
    
    -- 손익 통계
    avg_profit DECIMAL(10,2),             -- 평균 수익금액
    avg_loss DECIMAL(10,2),               -- 평균 손실금액
    avg_profit_pct DECIMAL(8,4),          -- 평균 수익률 (%)
    avg_loss_pct DECIMAL(8,4),            -- 평균 손실률 (%)
    profit_loss_ratio DECIMAL(8,4),       -- 손익비
    profit_factor DECIMAL(8,4),           -- Profit Factor
    
    -- 보유 통계
    avg_holding_period DECIMAL(8,2),      -- 평균 보유기간 (일)
    max_holding_period INT,                -- 최대 보유기간
    min_holding_period INT,                -- 최소 보유기간
    
    -- 회전율
    turnover_rate DECIMAL(8,4),           -- 연간 회전율 (%)
    avg_positions DECIMAL(6,2),           -- 평균 보유 종목 수
    
    -- 최대/최소값
    best_trade_return DECIMAL(10,4),      -- 최고 수익 거래 (%)
    worst_trade_return DECIMAL(10,4),     -- 최대 손실 거래 (%)
    best_day_return DECIMAL(8,4),         -- 최고 일 수익률 (%)
    worst_day_return DECIMAL(8,4),        -- 최대 일 손실률 (%)
    best_month_return DECIMAL(8,4),       -- 최고 월 수익률 (%)
    worst_month_return DECIMAL(8,4),      -- 최대 월 손실률 (%)
    
    -- 기타 지표
    alpha DECIMAL(10,4),                  -- 알파
    beta DECIMAL(6,4),                    -- 베타
    correlation DECIMAL(6,4),             -- 벤치마크와의 상관계수
    tracking_error DECIMAL(8,4),          -- 추적 오차
    
    -- 최종 자산
    final_capital DECIMAL(15,0),          -- 최종 자산
    peak_capital DECIMAL(15,0),           -- 최대 자산
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE
);

-- 일별 포트폴리오 가치
CREATE TABLE simulation_daily_values (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    
    -- 포트폴리오 가치
    portfolio_value DECIMAL(15,0),        -- 포트폴리오 총 가치
    cash_balance DECIMAL(15,0),           -- 현금 잔고
    invested_value DECIMAL(15,0),         -- 투자 금액
    
    -- 수익률
    daily_return DECIMAL(8,6),            -- 일 수익률
    cumulative_return DECIMAL(10,6),      -- 누적 수익률
    
    -- 벤치마크
    benchmark_value DECIMAL(15,0),        -- 벤치마크 가치
    benchmark_daily_return DECIMAL(8,6),   -- 벤치마크 일 수익률
    benchmark_cum_return DECIMAL(10,6),    -- 벤치마크 누적 수익률
    
    -- 포지션 정보
    position_count INT,                   -- 보유 종목 수
    long_value DECIMAL(15,0),             -- 매수 포지션 가치
    short_value DECIMAL(15,0) DEFAULT 0,  -- 매도 포지션 가치
    
    -- 리스크 지표
    daily_drawdown DECIMAL(8,6),          -- 일별 낙폭
    portfolio_beta DECIMAL(6,4),          -- 포트폴리오 베타
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    UNIQUE KEY uk_session_date (session_id, date),
    INDEX idx_date (date)
);

-- 거래 내역
CREATE TABLE simulation_trades (
    trade_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    
    -- 거래 정보
    trade_date DATE NOT NULL,
    trade_time TIME,
    stock_code VARCHAR(6) NOT NULL,
    stock_name VARCHAR(100),
    
    -- 거래 상세
    trade_type VARCHAR(10),               -- BUY, SELL, SHORT, COVER
    quantity INT NOT NULL,
    price DECIMAL(10,0) NOT NULL,         -- 거래 가격
    amount DECIMAL(15,0) NOT NULL,        -- 거래 금액
    
    -- 비용
    commission DECIMAL(10,0),             -- 수수료
    tax DECIMAL(10,0),                    -- 세금
    slippage_cost DECIMAL(10,0),          -- 슬리피지 비용
    total_cost DECIMAL(10,0),             -- 총 비용
    
    -- 거래 이유
    signal_type VARCHAR(50),              -- 시그널 타입
    signal_strength DECIMAL(5,2),         -- 시그널 강도
    factor_scores JSON,                   -- 팩터별 점수
    
    -- 포지션 정보 (매도 시)
    entry_price DECIMAL(10,0),            -- 진입 가격
    entry_date DATE,                      -- 진입 날짜
    holding_period INT,                   -- 보유 기간 (일)
    
    -- 손익 (매도 시)
    realized_pnl DECIMAL(15,0),           -- 실현 손익
    realized_pnl_pct DECIMAL(8,4),        -- 실현 수익률 (%)
    
    -- 포트폴리오 정보
    position_weight_before DECIMAL(6,4),   -- 거래 전 비중
    position_weight_after DECIMAL(6,4),    -- 거래 후 비중
    cash_balance_after DECIMAL(15,0),      -- 거래 후 현금 잔고
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_code (stock_code),
    INDEX idx_trade_type (trade_type)
);

-- 보유 포지션 스냅샷
CREATE TABLE simulation_positions (
    position_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    stock_code VARCHAR(6) NOT NULL,
    stock_name VARCHAR(100),
    
    -- 포지션 정보
    quantity INT NOT NULL,
    avg_price DECIMAL(10,0),              -- 평균 매수가
    current_price DECIMAL(10,0),          -- 현재가
    market_value DECIMAL(15,0),           -- 평가 금액
    
    -- 손익
    unrealized_pnl DECIMAL(15,0),         -- 미실현 손익
    unrealized_pnl_pct DECIMAL(8,4),      -- 미실현 수익률 (%)
    
    -- 비중
    weight DECIMAL(6,4),                  -- 포트폴리오 내 비중 (%)
    target_weight DECIMAL(6,4),           -- 목표 비중 (%)
    weight_diff DECIMAL(6,4),             -- 비중 차이
    
    -- 팩터 정보
    factor_values JSON,                   -- 현재 팩터 값들
    factor_scores JSON,                   -- 팩터 스코어
    composite_score DECIMAL(8,4),         -- 종합 스코어
    
    -- 보유 기간
    entry_date DATE,                      -- 진입일
    holding_days INT,                     -- 보유 기간
    
    -- 리스크
    position_beta DECIMAL(6,4),           -- 개별 종목 베타
    contribution_var DECIMAL(10,4),       -- VaR 기여도
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    UNIQUE KEY uk_session_date_stock (session_id, date, stock_code),
    INDEX idx_date (date),
    INDEX idx_stock_code (stock_code)
);

-- 섹터/업종별 분석
CREATE TABLE simulation_sector_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    sector_code VARCHAR(20) NOT NULL,
    sector_name VARCHAR(100),
    
    -- 비중 정보
    weight DECIMAL(6,4),                  -- 섹터 비중 (%)
    stock_count INT,                      -- 보유 종목 수
    
    -- 성과
    sector_return DECIMAL(8,4),           -- 섹터 수익률
    contribution DECIMAL(8,4),            -- 포트폴리오 기여도
    
    -- 벤치마크 대비
    benchmark_weight DECIMAL(6,4),        -- 벤치마크 내 비중
    active_weight DECIMAL(6,4),           -- 액티브 비중
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    UNIQUE KEY uk_session_date_sector (session_id, date, sector_code),
    INDEX idx_date (date)
);

-- 리스크 분석
CREATE TABLE simulation_risk_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    
    -- VaR (Value at Risk)
    var_95 DECIMAL(12,0),                 -- 95% VaR
    var_99 DECIMAL(12,0),                 -- 99% VaR
    cvar_95 DECIMAL(12,0),                -- 95% CVaR (Expected Shortfall)
    
    -- 변동성
    realized_volatility DECIMAL(8,4),     -- 실현 변동성
    implied_volatility DECIMAL(8,4),      -- 내재 변동성
    
    -- 상관관계
    correlation_matrix JSON,              -- 종목 간 상관관계 매트릭스
    
    -- 스트레스 테스트
    stress_test_results JSON,             -- 스트레스 테스트 결과
    
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id) ON DELETE CASCADE,
    UNIQUE KEY uk_session_date (session_id, date),
    INDEX idx_date (date)
);

-- =====================================================
-- PART 4: 사용자 관리 및 즐겨찾기
-- =====================================================

-- 사용자 즐겨찾기 전략
CREATE TABLE user_favorite_strategies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    strategy_id VARCHAR(36) NOT NULL,
    memo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (strategy_id) REFERENCES portfolio_strategies(strategy_id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_strategy (user_id, strategy_id),
    INDEX idx_user (user_id)
);

-- 시뮬레이션 비교 그룹
CREATE TABLE simulation_comparison_groups (
    group_id VARCHAR(36) PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- 비교할 세션들
    session_ids JSON,                     -- 세션 ID 리스트
    
    -- 비교 기준
    comparison_metrics JSON,               -- 비교할 지표 리스트
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user (user_id)
);

-- =====================================================
-- PART 5: 실시간 모니터링 및 알림
-- =====================================================

-- 실시간 모니터링 설정
CREATE TABLE monitoring_configs (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    
    -- 모니터링 항목
    monitor_drawdown BOOLEAN DEFAULT TRUE,
    drawdown_threshold DECIMAL(5,2),      -- MDD 임계값 (%)
    
    monitor_volatility BOOLEAN DEFAULT TRUE,
    volatility_threshold DECIMAL(5,2),    -- 변동성 임계값 (%)
    
    monitor_sharpe BOOLEAN DEFAULT TRUE,
    sharpe_threshold DECIMAL(5,2),        -- 샤프비율 임계값
    
    -- 알림 설정
    alert_email VARCHAR(100),
    alert_sms VARCHAR(20),
    alert_webhook_url VARCHAR(500),
    
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (strategy_id) REFERENCES portfolio_strategies(strategy_id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_active (is_active)
);

-- 알림 이력
CREATE TABLE alert_history (
    alert_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_id INT NOT NULL,
    session_id VARCHAR(36),
    
    alert_type VARCHAR(30),               -- DRAWDOWN, VOLATILITY, SHARPE, ERROR
    alert_level VARCHAR(10),              -- INFO, WARNING, CRITICAL
    
    metric_name VARCHAR(50),
    metric_value DECIMAL(20,4),
    threshold_value DECIMAL(20,4),
    
    message TEXT,
    
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_to VARCHAR(100),                 -- 수신자
    sent_method VARCHAR(20),              -- EMAIL, SMS, WEBHOOK
    
    FOREIGN KEY (config_id) REFERENCES monitoring_configs(config_id) ON DELETE CASCADE,
    INDEX idx_sent_at (sent_at),
    INDEX idx_alert_type (alert_type)
);

-- =====================================================
-- 뷰 (Views) - 자주 사용되는 조회
-- =====================================================

-- 전략 성과 순위
CREATE VIEW v_strategy_performance_ranking AS
SELECT 
    ps.strategy_id,
    ps.strategy_name,
    ps.strategy_type,
    ps.user_id,
    COUNT(DISTINCT ss.session_id) as simulation_count,
    AVG(st.annualized_return) as avg_cagr,
    AVG(st.sharpe_ratio) as avg_sharpe,
    AVG(st.max_drawdown) as avg_mdd,
    AVG(st.win_rate) as avg_win_rate,
    MAX(st.annualized_return) as best_cagr,
    MIN(st.max_drawdown) as best_mdd
FROM portfolio_strategies ps
LEFT JOIN simulation_sessions ss ON ps.strategy_id = ss.strategy_id
LEFT JOIN simulation_statistics st ON ss.session_id = st.session_id
WHERE ss.status = 'COMPLETED'
GROUP BY ps.strategy_id;

-- 최근 시뮬레이션 결과
CREATE VIEW v_recent_simulations AS
SELECT 
    ss.session_id,
    ss.strategy_id,
    ps.strategy_name,
    ss.start_date,
    ss.end_date,
    ss.status,
    st.annualized_return as cagr,
    st.sharpe_ratio,
    st.max_drawdown as mdd,
    st.total_trades,
    st.win_rate,
    ss.created_at
FROM simulation_sessions ss
JOIN portfolio_strategies ps ON ss.strategy_id = ps.strategy_id
LEFT JOIN simulation_statistics st ON ss.session_id = st.session_id
ORDER BY ss.created_at DESC;

-- =====================================================
-- 인덱스 추가 (성능 최적화)
-- =====================================================

-- 복합 인덱스 추가
CREATE INDEX idx_trades_session_date ON simulation_trades(session_id, trade_date);
CREATE INDEX idx_positions_session_date ON simulation_positions(session_id, date);
CREATE INDEX idx_daily_values_session_date ON simulation_daily_values(session_id, date);

-- 파티셔닝 (대용량 데이터 처리)
ALTER TABLE simulation_daily_values
PARTITION BY RANGE (YEAR(date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026)
);

ALTER TABLE simulation_trades
PARTITION BY RANGE (YEAR(trade_date)) (
    PARTITION p2020 VALUES LESS THAN (2021),
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026)
);