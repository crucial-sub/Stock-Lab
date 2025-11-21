"""
companies.industry 컬럼 값을 theme_name_kor과 일치시키는 마이그레이션 스크립트

실행 방법:
    cd SL-Back-end
    python -m scripts.fix_industry_names
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


# 업데이트할 industry 이름 매핑
INDUSTRY_NAME_UPDATES = [
    ("전기·가스·수도", "전기 / 가스 / 수도"),
    ("농업, 임업 및 어업", "농업 / 임업 / 어업"),
    ("전기·전자", "전기 / 전자"),
    ("IT 서비스", "IT서비스"),
    ("기계·장비", "기계 / 장비"),
    ("섬유·의류", "섬유 / 의류"),
    ("오락·문화", "오락 / 문화"),
    ("운송·창고", "운송 / 창고"),
    ("종이·목재", "종이 / 목재"),
    ("의료·정밀기기", "의료 / 정밀기기"),
    ("출판·매체복제", "출판 / 매체 복제"),
    ("음식료·담배", "음식료 / 담배"),
    ("기타금융", "기타 금융"),
    ("기타제조", "기타 제조"),
    ("운송장비·부품", "운송장비 / 부품"),
    ("일반서비스", "일반 서비스"),
]


async def fix_industry_names():
    """companies.industry 값을 theme_name_kor 형식으로 수정"""

    async with AsyncSessionLocal() as db:
        print("🔧 companies.industry 값 업데이트 시작...\n")

        total_updated = 0

        for old_name, new_name in INDUSTRY_NAME_UPDATES:
            # 업데이트할 레코드 수 확인
            count_query = text(
                "SELECT COUNT(*) FROM companies WHERE industry = :old_name"
            )
            result = await db.execute(count_query, {"old_name": old_name})
            count = result.scalar()

            if count > 0:
                # 업데이트 실행
                update_query = text(
                    "UPDATE companies SET industry = :new_name WHERE industry = :old_name"
                )
                await db.execute(update_query, {"old_name": old_name, "new_name": new_name})

                print(f"✅ '{old_name}' → '{new_name}' ({count}개 레코드 업데이트)")
                total_updated += count
            else:
                print(f"⏭️  '{old_name}' 레코드 없음 (스킵)")

        # 커밋
        await db.commit()

        print(f"\n{'='*60}")
        print(f"✅ 마이그레이션 완료")
        print(f"   - 총 업데이트: {total_updated}개 레코드")
        print(f"   - 업데이트 항목: {len(INDUSTRY_NAME_UPDATES)}개")
        print(f"{'='*60}\n")

        # 최종 확인 쿼리
        print("📊 업데이트 후 industry 분포:\n")
        check_query = text("""
            SELECT industry, COUNT(*) as count
            FROM companies
            WHERE industry IS NOT NULL
            GROUP BY industry
            ORDER BY industry
        """)
        result = await db.execute(check_query)
        rows = result.fetchall()

        for row in rows:
            print(f"   - {row[0]}: {row[1]}개")


if __name__ == "__main__":
    print("🚀 companies.industry 업데이트 마이그레이션 시작...\n")
    asyncio.run(fix_industry_names())
