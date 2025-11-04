"""
업종명 업데이트 확인 스크립트
companies 테이블의 industry 컬럼 데이터 확인
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.company import Company

settings = get_settings()

# 동기 엔진 생성
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=False
)


def check_industries():
    """업종 데이터 확인"""

    with Session(sync_engine) as db:
        # 전체 활성 회사 수
        total_active = db.execute(
            select(func.count(Company.company_id)).where(Company.is_active == 1)
        ).scalar()

        print(f"총 활성 회사 수: {total_active}")
        print("=" * 80)

        # industry가 NULL인 회사 수
        null_industry = db.execute(
            select(func.count(Company.company_id)).where(
                Company.is_active == 1,
                Company.industry.is_(None)
            )
        ).scalar()

        print(f"업종이 NULL인 회사: {null_industry}")

        # industry가 있는 회사 수
        has_industry = db.execute(
            select(func.count(Company.company_id)).where(
                Company.is_active == 1,
                Company.industry.isnot(None)
            )
        ).scalar()

        print(f"업종이 등록된 회사: {has_industry}")
        print("=" * 80)

        # 업종별 통계
        print("\n업종별 회사 수:")
        industry_stats = db.execute(
            select(Company.industry, func.count(Company.company_id).label('count'))
            .where(Company.is_active == 1, Company.industry.isnot(None))
            .group_by(Company.industry)
            .order_by(func.count(Company.company_id).desc())
        ).all()

        for industry, count in industry_stats[:20]:  # 상위 20개만
            print(f"  {industry}: {count}개")

        print("=" * 80)

        # 샘플 데이터 (업종이 있는 회사 10개)
        print("\n샘플 데이터 (업종이 등록된 회사 10개):")
        sample_companies = db.execute(
            select(Company)
            .where(Company.is_active == 1, Company.industry.isnot(None))
            .limit(10)
        ).scalars().all()

        for company in sample_companies:
            print(f"  [{company.stock_code}] {company.company_name} - {company.industry}")

        print("=" * 80)

        # 특정 종목 확인 (060310 - 3S)
        print("\n특정 종목 확인:")
        test_codes = ['060310', '054620', '095570', '006840', '027410']
        for code in test_codes:
            company = db.execute(
                select(Company).where(Company.stock_code == code)
            ).scalar_one_or_none()

            if company:
                print(f"  [{company.stock_code}] {company.company_name} - {company.industry}")
            else:
                print(f"  [{code}] - 찾을 수 없음")


if __name__ == "__main__":
    check_industries()
