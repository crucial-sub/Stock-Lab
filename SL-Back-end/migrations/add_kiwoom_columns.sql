-- 키움증권 API 연동을 위한 컬럼 추가
ALTER TABLE users
ADD COLUMN IF NOT EXISTS kiwoom_app_key VARCHAR(255),
ADD COLUMN IF NOT EXISTS kiwoom_app_secret VARCHAR(255),
ADD COLUMN IF NOT EXISTS kiwoom_access_token VARCHAR(512),
ADD COLUMN IF NOT EXISTS kiwoom_token_expires_at TIMESTAMP WITH TIME ZONE;

-- 인덱스 추가 (선택적)
CREATE INDEX IF NOT EXISTS idx_users_kiwoom_access_token ON users(kiwoom_access_token);

-- 확인
\d users
