"""
데이터베이스 마이그레이션 실행 스크립트
investment_strategies 테이블 생성

실행 방법:
    cd SL-Back-end
    python -m scripts.run_migration
"""
import asyncio
import sys
import re
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal


def parse_sql_statements(sql_content: str) -> list[str]:
    """
    SQL 파일을 개별 문장으로 파싱
    간단한 접근: 라인별로 읽고 세미콜론이 나올 때까지 누적
    """
    statements = []
    current_statement = []
    in_dollar_block = False  # $$ ... $$ 블록 내부인지 추적

    for line in sql_content.split('\n'):
        stripped = line.strip()

        # 빈 줄이나 주석만 있는 줄은 건너뛰기
        if not stripped or stripped.startswith('--'):
            # 하지만 문장 내부에 있으면 추가
            if current_statement:
                current_statement.append(line)
            continue

        # $$ 토글 확인
        if '$$' in line:
            # $$ 개수가 홀수면 토글
            dollar_count = line.count('$$')
            if dollar_count % 2 == 1:
                in_dollar_block = not in_dollar_block

        current_statement.append(line)

        # 세미콜론으로 문장 종료 확인 (단, $$ 블록 내부가 아닐 때만)
        if not in_dollar_block and stripped.endswith(';'):
            # 현재 누적된 문장을 완성
            full_statement = '\n'.join(current_statement).strip()
            if full_statement and not full_statement.startswith('--'):
                statements.append(full_statement)
            current_statement = []

    # 마지막 문장 처리 (세미콜론 없이 끝나는 경우)
    if current_statement:
        full_statement = '\n'.join(current_statement).strip()
        if full_statement and not full_statement.startswith('--'):
            statements.append(full_statement)

    return statements


async def run_migration():
    """마이그레이션 SQL 실행"""

    # SQL 파일 경로
    sql_path = project_root / "migrations" / "add_investment_strategies.sql"

    if not sql_path.exists():
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_path}")
        return

    # SQL 파일 읽기
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"📄 마이그레이션 SQL 로드 완료")

    # SQL 문장 파싱 (함수 블록 고려)
    statements = parse_sql_statements(sql_content)

    # SQL 문장 순서 정렬 (CREATE TABLE → CREATE FUNCTION → CREATE INDEX → CREATE TRIGGER → COMMENT)
    def get_statement_priority(stmt: str) -> int:
        stmt_upper = stmt.upper().strip()
        if stmt_upper.startswith('CREATE TABLE'):
            return 0
        elif stmt_upper.startswith('CREATE') and 'FUNCTION' in stmt_upper:
            return 1
        elif stmt_upper.startswith('CREATE INDEX'):
            return 2
        elif stmt_upper.startswith('DROP TRIGGER'):
            return 3
        elif stmt_upper.startswith('CREATE TRIGGER'):
            return 4
        elif stmt_upper.startswith('COMMENT'):
            return 5
        else:
            return 6

    statements.sort(key=get_statement_priority)
    print(f"📝 총 {len(statements)}개의 SQL 문장 파싱 완료\n")

    # 파싱 결과 미리보기 (디버깅용)
    print("파싱된 문장 목록:")
    for idx, statement in enumerate(statements, 1):
        preview = statement[:80].replace('\n', ' ')
        if len(statement) > 80:
            preview += "..."
        print(f"  {idx}. {preview}")
    print()

    # 데이터베이스 세션
    async with AsyncSessionLocal() as db:
        try:
            # 파싱된 문장들을 개별적으로 실행
            for idx, statement in enumerate(statements, 1):
                await db.execute(text(statement))
                print(f"✅ [{idx}/{len(statements)}] 실행 완료")

            await db.commit()

            print(f"\n{'='*60}")
            print(f"✅ 마이그레이션 완료")
            print(f"   - 테이블: investment_strategies")
            print(f"   - 인덱스: tags, is_active, popularity_score")
            print(f"   - 트리거: updated_at 자동 갱신")
            print(f"{'='*60}")

        except Exception as e:
            print(f"\n❌ 마이그레이션 실패: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("🚀 데이터베이스 마이그레이션 시작...\n")
    asyncio.run(run_migration())
