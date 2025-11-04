"""
업종명 업데이트 스크립트
CSV 파일에서 업종 정보를 읽어와 companies 테이블의 industry 컬럼을 업데이트
"""
import sys
import os
import csv
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, update, select, text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.company import Company

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# 동기 엔진 생성
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=False
)


def read_csv_industries(csv_path: str) -> dict:
    """
    CSV 파일에서 종목코드와 업종명 매핑 읽기

    Args:
        csv_path: CSV 파일 경로

    Returns:
        dict: {종목코드: 업종명} 매핑 딕셔너리
    """
    industry_map = {}

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # 헤더 확인
            headers = reader.fieldnames
            logger.info(f"CSV 헤더: {headers}")

            row_count = 0
            for row in reader:
                row_count += 1
                stock_code = row.get('종목코드', '').strip()
                industry_name = row.get('업종명', '').strip()

                # 첫 3개 행 디버깅
                if row_count <= 3:
                    logger.info(f"행 {row_count}: 종목코드='{stock_code}', 업종명='{industry_name}'")

                if stock_code and industry_name:
                    # 종목코드 6자리로 정규화 (앞에 0이 빠진 경우 대비)
                    stock_code = stock_code.zfill(6)
                    industry_map[stock_code] = industry_name

        logger.info(f"CSV에서 {len(industry_map)}개 종목의 업종 정보를 읽었습니다.")

        # 처음 5개 샘플 출력
        sample = list(industry_map.items())[:5]
        logger.info(f"샘플 데이터: {sample}")

        return industry_map

    except Exception as e:
        logger.error(f"CSV 파일 읽기 실패: {e}")
        raise


def update_company_industries(industry_map: dict) -> dict:
    """
    companies 테이블의 industry 컬럼 업데이트

    Args:
        industry_map: {종목코드: 업종명} 매핑 딕셔너리

    Returns:
        dict: 업데이트 결과 통계
    """
    stats = {
        'total_csv': len(industry_map),
        'matched': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    with Session(sync_engine) as db:
        try:
            # 데이터베이스의 모든 활성 회사 조회
            companies = db.execute(
                select(Company).where(Company.is_active == 1)
            ).scalars().all()

            logger.info(f"데이터베이스에서 {len(companies)}개 활성 회사를 조회했습니다.")

            # 처음 3개 회사 정보 출력
            for i, company in enumerate(companies[:3]):
                logger.info(f"DB 회사 {i+1}: stock_code='{company.stock_code}', name='{company.company_name}', current_industry='{company.industry}'")

            for company in companies:
                if not company.stock_code:
                    stats['skipped'] += 1
                    continue

                # CSV에서 해당 종목코드의 업종 찾기
                industry_name = industry_map.get(company.stock_code)

                if industry_name:
                    stats['matched'] += 1

                    # 기존 업종과 다른 경우에만 업데이트
                    if company.industry != industry_name:
                        try:
                            stmt = update(Company).where(
                                Company.company_id == company.company_id
                            ).values(
                                industry=industry_name
                            )
                            db.execute(stmt)
                            stats['updated'] += 1

                            logger.info(
                                f"업데이트: {company.stock_code} ({company.company_name}) "
                                f"- '{company.industry}' → '{industry_name}'"
                            )
                        except Exception as e:
                            stats['errors'] += 1
                            logger.error(
                                f"업데이트 실패: {company.stock_code} ({company.company_name}) - {e}"
                            )
                    else:
                        logger.debug(
                            f"동일: {company.stock_code} ({company.company_name}) - '{industry_name}'"
                        )
                else:
                    logger.debug(
                        f"CSV에 없음: {company.stock_code} ({company.company_name})"
                    )

            # 커밋
            db.commit()
            logger.info("데이터베이스 업데이트 커밋 완료")

        except Exception as e:
            logger.error(f"데이터베이스 업데이트 중 오류: {e}")
            db.rollback()
            raise

    return stats


def main():
    """메인 실행 함수"""
    # 명령행 인자로 CSV 파일 경로 받기
    if len(sys.argv) < 2:
        print("사용법: python update_industries.py <CSV_파일_경로>")
        print("예시: python update_industries.py /path/to/국장_상장_종목.csv")
        csv_path = input("CSV 파일 경로를 입력하세요: ").strip()
    else:
        csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    logger.info(f"CSV 파일: {csv_path}")
    logger.info("=" * 80)

    # CSV에서 업종 정보 읽기
    industry_map = read_csv_industries(csv_path)

    # 데이터베이스 업데이트
    logger.info("=" * 80)
    logger.info("데이터베이스 업데이트 시작...")
    stats = update_company_industries(industry_map)

    # 결과 출력
    logger.info("=" * 80)
    logger.info("업데이트 완료!")
    logger.info(f"CSV 총 종목 수: {stats['total_csv']}")
    logger.info(f"매칭된 종목 수: {stats['matched']}")
    logger.info(f"업데이트된 종목 수: {stats['updated']}")
    logger.info(f"스킵된 종목 수 (종목코드 없음): {stats['skipped']}")
    logger.info(f"오류 발생 수: {stats['errors']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
