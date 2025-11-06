-- Migration: Add portfolio sharing and user ownership fields
-- Date: 2025-01-06
-- Description: Adds user_id, is_public, is_anonymous, hide_strategy_details columns to portfolio_strategies table

BEGIN;

-- Add user_id column
ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);

-- Add public sharing settings
ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE portfolio_strategies
ADD COLUMN IF NOT EXISTS hide_strategy_details BOOLEAN NOT NULL DEFAULT FALSE;

-- Add comments
COMMENT ON COLUMN portfolio_strategies.user_id IS '전략 생성자 ID (UUID)';
COMMENT ON COLUMN portfolio_strategies.is_public IS '공개 여부 (랭킹 집계)';
COMMENT ON COLUMN portfolio_strategies.is_anonymous IS '익명 여부';
COMMENT ON COLUMN portfolio_strategies.hide_strategy_details IS '전략 내용 숨김 여부';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_portfolio_strategies_user ON portfolio_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_strategies_public ON portfolio_strategies(is_public, user_id);

COMMIT;
