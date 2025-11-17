"""채팅 테이블 생성 마이그레이션"""
import sys
import os
import psycopg

# 환경변수에서 DATABASE_SYNC_URL 가져오기
DATABASE_URL = os.getenv("DATABASE_SYNC_URL")

if not DATABASE_URL:
    print("❌ DATABASE_SYNC_URL 환경변수가 설정되지 않았습니다")
    sys.exit(1)

print(f"데이터베이스 연결 중: {DATABASE_URL.split('@')[1]}")

try:
    with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
        print("✅ 데이터베이스 연결 성공")

        with conn.cursor() as cur:
            # 1. chat_sessions 테이블 생성
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    mode VARCHAR(50) NOT NULL DEFAULT 'chat',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ chat_sessions 테이블 생성 완료")

            # 2. chat_messages 테이블 생성
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    intent VARCHAR(100),
                    backtest_conditions JSONB,
                    ui_language JSONB,
                    message_order INTEGER NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ chat_messages 테이블 생성 완료")

            # 3. 인덱스 생성
            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)")
            print("✅ 인덱스: chat_sessions.user_id")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC)")
            print("✅ 인덱스: chat_sessions.created_at")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)")
            print("✅ 인덱스: chat_messages.session_id")

            cur.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at)")
            print("✅ 인덱스: chat_messages.created_at")

            # 4. updated_at 자동 업데이트 트리거 함수
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_chat_sessions_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
            """)
            print("✅ 트리거 함수 생성")

            # 5. 트리거 생성
            cur.execute("DROP TRIGGER IF EXISTS trigger_update_chat_sessions_updated_at ON chat_sessions")
            cur.execute("""
                CREATE TRIGGER trigger_update_chat_sessions_updated_at
                    BEFORE UPDATE ON chat_sessions
                    FOR EACH ROW
                    EXECUTE FUNCTION update_chat_sessions_updated_at()
            """)
            print("✅ 트리거 생성")

        conn.commit()
        print("\n✅ 채팅 테이블 마이그레이션 완료!")

except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
