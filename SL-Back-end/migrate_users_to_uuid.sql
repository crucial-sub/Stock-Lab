-- ======================================================
-- Users 테이블 UUID 마이그레이션 스크립트
-- ======================================================
-- 기존 Integer ID를 UUID로 변경합니다.
-- 주의: 기존 데이터는 모두 삭제됩니다!
-- ======================================================

-- 1. 기존 테이블 백업 (옵션)
-- DROP TABLE IF EXISTS users_backup;
-- CREATE TABLE users_backup AS SELECT * FROM users;

-- 2. 기존 users 테이블 삭제
DROP TABLE IF EXISTS users CASCADE;

-- 3. UUID 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 4. UUID 기반 users 테이블 생성
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 5. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);

-- 6. 업데이트 시각 자동 갱신 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. 업데이트 시각 트리거 생성
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8. 확인
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'Users 테이블이 UUID로 성공적으로 마이그레이션되었습니다!';
END $$;
