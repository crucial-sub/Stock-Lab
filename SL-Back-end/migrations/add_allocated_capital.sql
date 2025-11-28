-- Migration: Add allocated_capital column to auto_trading_strategies table
-- Purpose: Allow users to allocate specific capital amounts to each trading strategy
-- Example: Total account balance 500M won can be split: Strategy A: 100M, Strategy B: 200M, Strategy C: 50M

-- Add allocated_capital column (nullable first for existing rows)
ALTER TABLE auto_trading_strategies
ADD COLUMN IF NOT EXISTS allocated_capital DECIMAL(20, 2);

-- Set default value to initial_capital for existing strategies
UPDATE auto_trading_strategies
SET allocated_capital = initial_capital
WHERE allocated_capital IS NULL;

-- Make column NOT NULL after data is populated
ALTER TABLE auto_trading_strategies
ALTER COLUMN allocated_capital SET NOT NULL;

-- Add comment to explain the field
COMMENT ON COLUMN auto_trading_strategies.allocated_capital IS '전략에 할당된 자본금 (원). 여러 전략에 계좌 잔액을 나누어 배분 가능.';
