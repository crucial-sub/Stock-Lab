-- Migration: Add UNIQUE constraint to simulation_daily_values table
-- Purpose: Fix "InvalidColumnReferenceError: there is no unique or exclusion constraint matching the ON CONFLICT specification"
-- Date: 2025-11-20
-- Issue: ON CONFLICT (session_id, date) requires UNIQUE constraint but only has regular index

-- 1. Drop existing regular index (will be replaced by unique constraint)
DROP INDEX IF EXISTS idx_simulation_daily_values_session_date;

-- 2. Add UNIQUE constraint on (session_id, date)
-- This allows ON CONFLICT (session_id, date) DO UPDATE to work correctly
ALTER TABLE simulation_daily_values
ADD CONSTRAINT uq_simulation_daily_values_session_date
UNIQUE (session_id, date);

-- Note: UNIQUE constraint automatically creates an index, so we don't need the regular index anymore
-- This ensures that each session can only have one daily_value record per date

-- Verify the constraint was created
-- SELECT constraint_name, constraint_type
-- FROM information_schema.table_constraints
-- WHERE table_name = 'simulation_daily_values' AND constraint_type = 'UNIQUE';
