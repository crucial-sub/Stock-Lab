-- =====================================================
-- 투자 전략 관리 테이블 생성
-- =====================================================
-- 목적: AI 어시스턴트 전략 추천 및 백테스트 실행을 위한 전략 데이터 저장
-- 작성일: 2025-01-20
-- =====================================================

-- 전략 테이블 생성
CREATE TABLE IF NOT EXISTS investment_strategies (
    -- 기본 식별자
    id VARCHAR(50) PRIMARY KEY,

    -- 전략 메타데이터
    name VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    description TEXT,
    tags TEXT[] NOT NULL,  -- 추천 매칭용 태그: ['long_term', 'style_value', 'risk_low']

    -- 백테스트 실행 설정
    -- BacktestRunRequest 형식 (user_id, start_date, end_date, initial_investment 제외)
    backtest_config JSONB NOT NULL,

    -- UI 표시용 조건 설명
    display_conditions JSONB NOT NULL,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    popularity_score INTEGER DEFAULT 0,  -- 사용 횟수 추적

    -- 제약 조건
    CONSTRAINT valid_tags CHECK (array_length(tags, 1) > 0),
    CONSTRAINT valid_backtest_config CHECK (jsonb_typeof(backtest_config) = 'object'),
    CONSTRAINT valid_display_conditions CHECK (jsonb_typeof(display_conditions) = 'array')
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_strategies_tags ON investment_strategies USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON investment_strategies (is_active);
CREATE INDEX IF NOT EXISTS idx_strategies_popularity ON investment_strategies (popularity_score DESC);

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_investment_strategy_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 업데이트 트리거 생성
DROP TRIGGER IF EXISTS trigger_update_investment_strategy_timestamp ON investment_strategies;
CREATE TRIGGER trigger_update_investment_strategy_timestamp
    BEFORE UPDATE ON investment_strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_investment_strategy_timestamp();

-- 코멘트 추가
COMMENT ON TABLE investment_strategies IS 'AI 어시스턴트 전략 추천 및 백테스트 실행을 위한 투자 전략 마스터 테이블';
COMMENT ON COLUMN investment_strategies.id IS '전략 고유 식별자 (예: warren_buffett)';
COMMENT ON COLUMN investment_strategies.name IS '전략 표시명 (예: 워렌버핏의 전략)';
COMMENT ON COLUMN investment_strategies.summary IS '전략 요약 설명';
COMMENT ON COLUMN investment_strategies.tags IS '추천 매칭용 태그 배열';
COMMENT ON COLUMN investment_strategies.backtest_config IS '백테스트 실행에 필요한 전체 설정 (JSONB)';
COMMENT ON COLUMN investment_strategies.display_conditions IS 'UI에 표시할 조건 설명 배열 (JSONB)';
COMMENT ON COLUMN investment_strategies.popularity_score IS '전략 사용 횟수 (조회 시 자동 증가)';
