"""psycopg3를 사용한 마이그레이션"""
import sys
import psycopg

DATABASE_URL = "postgresql://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db"

try:
    with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
        print("✅ 데이터베이스 연결 성공")

        with conn.cursor() as cur:
            # 컬럼 추가
            cur.execute("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_date DATE")
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
    sys.exit(1)
