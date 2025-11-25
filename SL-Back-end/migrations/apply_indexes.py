"""
DB 인덱스 적용 스크립트
Phase 1 백테스트 최적화 인덱스 생성
"""
import psycopg
from pathlib import Path


def apply_indexes():
    """인덱스 마이그레이션 실행"""
    # DB 연결
    conn = psycopg.connect(
        host='localhost',
        port=15432,
        user='stocklabadmin',
        password='nmmteam05',
        dbname='stock_lab_investment_db'
    )

    try:
        cursor = conn.cursor()

        # SQL 파일 읽기
        sql_file = Path(__file__).parent / 'add_backtest_indexes_phase1.sql'
        sql_content = sql_file.read_text(encoding='utf-8')

        # SQL을 개별 명령문으로 분리 (주석과 빈 줄 제거)
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # 주석 라인 스킵
            if line.strip().startswith('--') or not line.strip():
                continue

            current_statement.append(line)

            # 세미콜론으로 끝나면 명령문 완료
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement and not statement.startswith('/*'):
                    statements.append(statement)
                current_statement = []

        print(f"📋 총 {len(statements)}개의 SQL 명령문 실행 예정\n")

        # 각 명령문 실행
        created_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                # CREATE INDEX 명령만 실행
                if 'CREATE' in statement.upper() and 'INDEX' in statement.upper():
                    # 인덱스 이름 추출
                    if 'IF NOT EXISTS' in statement:
                        index_name = statement.split('IF NOT EXISTS')[1].split('ON')[0].strip()
                    else:
                        index_name = statement.split('INDEX')[1].split('ON')[0].strip()

                    print(f"[{i}/{len(statements)}] Creating index: {index_name}...", end=' ')
                    cursor.execute(statement)
                    conn.commit()
                    print("✅")
                    created_count += 1
                elif 'SELECT' in statement.upper():
                    # SELECT 쿼리 실행 및 결과 출력
                    print(f"\n[{i}/{len(statements)}] 실행 중: 통계 조회...")
                    cursor.execute(statement)
                    results = cursor.fetchall()
                    if results:
                        print(f"  결과: {len(results)}개 레코드")
                        for row in results[:5]:  # 처음 5개만 출력
                            print(f"  {row}")
                        if len(results) > 5:
                            print(f"  ... 외 {len(results) - 5}개")
                else:
                    print(f"[{i}/{len(statements)}] 실행: {statement[:50]}...")
                    cursor.execute(statement)
                    conn.commit()

            except Exception as e:
                if 'already exists' in str(e):
                    print(f"⚠️  (이미 존재)")
                    conn.rollback()
                else:
                    print(f"❌ 에러: {e}")
                    conn.rollback()

        print(f"\n✅ 인덱스 적용 완료!")
        print(f"📊 생성된 인덱스: {created_count}개")

        # 생성된 인덱스 목록 확인
        print("\n📋 생성된 백테스트 관련 인덱스 목록:")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexrelname as indexname,
                pg_size_pretty(pg_relation_size(indexrelid::regclass)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
              AND (
                indexrelname LIKE 'idx_backtest_%'
                OR indexrelname LIKE 'idx_simulation_%'
              )
            ORDER BY tablename, indexrelname
        """)

        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  {idx[1]:30} | {idx[2]:40} | {idx[3]}")

        print(f"\n총 {len(indexes)}개의 백테스트 관련 인덱스 확인됨")

        cursor.close()

    finally:
        conn.close()


if __name__ == '__main__':
    apply_indexes()
