"""간단한 마이그레이션 스크립트"""
import sys
from sqlalchemy import create_engine, text

# 동기 엔진 사용 (asyncpg 대신 psycopg2)
DATABASE_URL = "postgresql://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db"

try:
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"connect_timeout": 10})

    with engine.begin() as conn:
        print("✅ 데이터베이스 연결 성공")

        # 컬럼 추가
        conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_date DATE"))
        print("✅ current_date 추가")

        conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS buy_count INTEGER DEFAULT 0"))
        print("✅ buy_count 추가")

        conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS sell_count INTEGER DEFAULT 0"))
        print("✅ sell_count 추가")

        conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_return DECIMAL(10, 4)"))
        print("✅ current_return 추가")

        conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_capital DECIMAL(15, 2)"))
        print("✅ current_capital 추가")

    print("\n✅ 모든 컬럼 추가 완료!")

except Exception as e:
    print(f"❌ 오류: {e}")
    sys.exit(1)
finally:
    engine.dispose()
