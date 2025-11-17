"""동기 방식으로 실시간 진행 상황 컬럼 추가"""
import psycopg2

# RDS 연결 정보
DATABASE_URL = "postgresql://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db"

def add_realtime_columns():
    conn = None
    try:
        # 연결
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("✅ 데이터베이스 연결 성공")

        # 컬럼 추가
        columns = [
            ("current_date", "DATE", "현재 처리 중인 날짜"),
            ("buy_count", "INTEGER DEFAULT 0", "현재까지 매수 횟수"),
            ("sell_count", "INTEGER DEFAULT 0", "현재까지 매도 횟수"),
            ("current_return", "DECIMAL(10, 4)", "현재 수익률 (%)"),
            ("current_capital", "DECIMAL(15, 2)", "현재 자본금")
        ]

        for col_name, col_type, comment in columns:
            try:
                cur.execute(f"ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                conn.commit()
                print(f"✅ {col_name} 컬럼 추가 완료")
            except Exception as e:
                print(f"⚠️  {col_name} 컬럼 추가 중 오류 (이미 존재할 수 있음): {e}")
                conn.rollback()

        print("\n✅ 모든 실시간 진행 컬럼 추가 작업 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
            print("✅ 데이터베이스 연결 종료")

if __name__ == "__main__":
    add_realtime_columns()
