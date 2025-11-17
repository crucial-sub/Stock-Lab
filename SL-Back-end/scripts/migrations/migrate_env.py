"""환경변수의 DATABASE_SYNC_URL을 사용한 마이그레이션"""
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
            # 컬럼 추가 (current_date는 PostgreSQL 예약어이므로 큰따옴표로 감싸기)
            cur.execute('ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS "current_date" DATE')
            print("✅ current_date 추가")

            cur.execute("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS buy_count INTEGER DEFAULT 0")
            print("✅ buy_count 추가")

            cur.execute("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS sell_count INTEGER DEFAULT 0")
            print("✅ sell_count 추가")

            cur.execute("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_return DECIMAL(10, 4)")
            print("✅ current_return 추가")

            cur.execute("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_capital DECIMAL(15, 2)")
            print("✅ current_capital 추가")

        conn.commit()
        print("\n✅ 모든 컬럼 추가 완료!")

except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
