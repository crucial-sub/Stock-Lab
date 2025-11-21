#!/usr/bin/env python3
"""
simulation_daily_values 테이블에 UNIQUE 제약 조건 추가
"""
import asyncio
import asyncpg
from pathlib import Path

async def run_migration():
    """마이그레이션 실행"""
    conn = await asyncpg.connect(
        host='host.docker.internal',
        port=5433,
        user='stocklabadmin',
        password='nmmteam05',
        database='stock_lab_investment_db'
    )

    try:
        print("🔄 마이그레이션 시작: UNIQUE 제약 조건 추가")
        print("📄 작업: simulation_daily_values 테이블에 UNIQUE(session_id, date) 추가")
        print()

        # 1단계: 중복 데이터 확인
        print("1️⃣ 중복 데이터 확인 중...")
        duplicates = await conn.fetch("""
            SELECT session_id, date, COUNT(*) as count
            FROM simulation_daily_values
            GROUP BY session_id, date
            HAVING COUNT(*) > 1
        """)

        if duplicates:
            print(f"   ⚠️  중복 발견: {len(duplicates)}개의 (session_id, date) 조합")
            for dup in duplicates[:5]:  # 처음 5개만 표시
                print(f"      - session_id={dup['session_id'][:13]}..., date={dup['date']}, count={dup['count']}")
            if len(duplicates) > 5:
                print(f"      ... 외 {len(duplicates) - 5}개")

            # 2단계: 중복 데이터 제거 (각 조합에서 id가 가장 큰 레코드만 남김)
            print("\n2️⃣ 중복 데이터 제거 중...")
            delete_sql = """
                DELETE FROM simulation_daily_values
                WHERE id IN (
                    SELECT id
                    FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (PARTITION BY session_id, date ORDER BY id DESC) as rn
                        FROM simulation_daily_values
                    ) t
                    WHERE rn > 1
                )
            """
            result = await conn.execute(delete_sql)
            print(f"   ✅ 중복 데이터 제거 완료: {result}")
        else:
            print("   ✅ 중복 데이터 없음")

        # 3단계: 기존 인덱스 제거
        print("\n3️⃣ 기존 인덱스 제거 중...")
        await conn.execute("DROP INDEX IF EXISTS idx_simulation_daily_values_session_date")
        print("   ✅ 인덱스 제거 완료")

        # 4단계: UNIQUE 제약 조건 추가
        print("\n4️⃣ UNIQUE 제약 조건 추가 중...")
        await conn.execute("""
            ALTER TABLE simulation_daily_values
            ADD CONSTRAINT uq_simulation_daily_values_session_date
            UNIQUE (session_id, date)
        """)
        print("   ✅ UNIQUE 제약 조건 추가 완료")

        print("✅ 마이그레이션 완료!")
        print()

        # 결과 확인
        constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'simulation_daily_values' AND constraint_type = 'UNIQUE'
        """)

        print("🔒 UNIQUE 제약 조건:")
        for c in constraints:
            print(f"  - {c['constraint_name']}: {c['constraint_type']}")

        # 인덱스 확인
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'simulation_daily_values'
            AND indexname LIKE '%session%date%'
        """)

        print("\n📊 관련 인덱스:")
        for idx in indexes:
            print(f"  - {idx['indexname']}")

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        raise
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run_migration())
