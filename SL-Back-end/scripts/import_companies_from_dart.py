"""
OpenDart API를 사용하여 회사 정보를 가져와 companies 테이블에 저장하는 스크립트

OpenDart API 엔드포인트:
- 고유번호 목록: https://opendart.fss.or.kr/api/corpCode.xml
- 회사 개황: https://opendart.fss.or.kr/api/company.json
"""
import sys
import os
import json
import logging
import zipfile
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.company import Company

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# OpenDart API 키
DART_API_KEY = os.getenv("DART_API_KEY")

if not DART_API_KEY:
    logger.error("DART_API_KEY가 .env 파일에 설정되지 않았습니다.")
    logger.error("OpenDart API 키는 https://opendart.fss.or.kr/ 에서 발급받을 수 있습니다.")
    sys.exit(1)

# OpenDart API URL
DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
DART_COMPANY_INFO_URL = "https://opendart.fss.or.kr/api/company.json"

settings = get_settings()

# 동기 엔진 생성
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=False
)


def download_corp_codes() -> List[Dict]:
    """
    OpenDart API에서 고유번호 목록을 다운로드

    Returns:
        List[Dict]: 회사 정보 리스트 (corp_code, corp_name, stock_code, modify_date)
    """
    logger.info("OpenDart API에서 고유번호 목록 다운로드 중...")

    try:
        response = requests.get(
            DART_CORP_CODE_URL,
            params={"crtfc_key": DART_API_KEY},
            timeout=30
        )
        response.raise_for_status()

        # ZIP 파일 압축 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # CORPCODE.xml 파일 읽기
            xml_content = zip_file.read("CORPCODE.xml")

        # XML 파싱
        root = ET.fromstring(xml_content)

        corp_list = []
        for corp in root.findall("list"):
            corp_code = corp.findtext("corp_code", "").strip()
            corp_name = corp.findtext("corp_name", "").strip()
            stock_code = corp.findtext("stock_code", "").strip()
            modify_date = corp.findtext("modify_date", "").strip()

            if corp_code and corp_name:
                corp_list.append({
                    "corp_code": corp_code,
                    "corp_name": corp_name,
                    "stock_code": stock_code if stock_code else None,
                    "modify_date": modify_date
                })

        logger.info(f"총 {len(corp_list)}개 회사 정보를 다운로드했습니다.")
        return corp_list

    except requests.RequestException as e:
        logger.error(f"OpenDart API 요청 실패: {e}")
        raise
    except Exception as e:
        logger.error(f"고유번호 목록 다운로드 실패: {e}")
        raise


def get_company_info(corp_code: str) -> Optional[Dict]:
    """
    특정 회사의 상세 정보를 OpenDart API에서 가져오기

    Args:
        corp_code: 회사 고유번호

    Returns:
        Optional[Dict]: 회사 상세 정보
    """
    try:
        response = requests.get(
            DART_COMPANY_INFO_URL,
            params={
                "crtfc_key": DART_API_KEY,
                "corp_code": corp_code
            },
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        # API 응답 상태 확인
        if data.get("status") != "000":
            logger.debug(f"회사 정보 조회 실패 (corp_code: {corp_code}): {data.get('message')}")
            return None

        return data

    except requests.RequestException as e:
        logger.debug(f"회사 정보 API 요청 실패 (corp_code: {corp_code}): {e}")
        return None
    except Exception as e:
        logger.debug(f"회사 정보 조회 오류 (corp_code: {corp_code}): {e}")
        return None


def parse_market_type(stock_code: str, company_info: Optional[Dict]) -> Optional[str]:
    """
    시장 구분 파싱 (KOSPI/KOSDAQ/KONEX)

    Args:
        stock_code: 종목코드
        company_info: 회사 상세 정보

    Returns:
        Optional[str]: 시장 구분
    """
    if not stock_code:
        return None

    # OpenDart API 응답에서 시장 정보 확인
    if company_info:
        # 'induty_code'나 다른 필드에서 시장 정보를 추출할 수 있음
        # 예: KOSPI: Y, KOSDAQ: K, KONEX: N
        # 실제 API 응답 구조에 따라 조정 필요
        pass

    # 종목코드가 있으면 기본적으로 상장 회사
    # 실제로는 별도 API나 데이터 소스에서 확인 필요
    return None


def parse_listed_date(date_str: str) -> Optional[str]:
    """
    상장일 파싱

    Args:
        date_str: 날짜 문자열 (YYYYMMDD)

    Returns:
        Optional[str]: ISO 형식 날짜 (YYYY-MM-DD)
    """
    if not date_str or len(date_str) != 8:
        return None

    try:
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    except Exception:
        return None


def import_companies(limit: Optional[int] = None, only_listed: bool = True):
    """
    OpenDart API에서 회사 정보를 가져와 DB에 저장

    Args:
        limit: 가져올 회사 수 제한 (None이면 전체)
        only_listed: True이면 상장사만 가져오기
    """
    stats = {
        'total': 0,
        'listed': 0,
        'unlisted': 0,
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }

    # 1. 고유번호 목록 다운로드
    corp_list = download_corp_codes()
    stats['total'] = len(corp_list)

    # 상장사만 필터링
    if only_listed:
        corp_list = [corp for corp in corp_list if corp['stock_code']]
        logger.info(f"상장사만 필터링: {len(corp_list)}개")

    stats['listed'] = len([c for c in corp_list if c['stock_code']])
    stats['unlisted'] = len([c for c in corp_list if not c['stock_code']])

    # 개수 제한
    if limit:
        corp_list = corp_list[:limit]
        logger.info(f"처리할 회사 수를 {limit}개로 제한합니다.")

    # 2. DB에 저장
    with Session(sync_engine) as db:
        for idx, corp in enumerate(corp_list, 1):
            try:
                corp_code = corp['corp_code']
                corp_name = corp['corp_name']
                stock_code = corp['stock_code']

                if idx % 100 == 0:
                    logger.info(f"진행 중... {idx}/{len(corp_list)}")

                # 기존 데이터 확인
                existing = db.execute(
                    select(Company).where(Company.corp_code == corp_code)
                ).scalar_one_or_none()

                # 회사 상세 정보 가져오기 (상장사만)
                company_info = None
                if stock_code:
                    company_info = get_company_info(corp_code)

                # 데이터 준비
                company_data = {
                    'corp_code': corp_code,
                    'stock_code': stock_code,
                    'company_name': corp_name,
                    'is_active': 1 if stock_code else 0,
                }

                # 상세 정보가 있으면 추가
                if company_info:
                    company_data.update({
                        'company_name_eng': company_info.get('corp_name_eng'),
                        'stock_name': company_info.get('stock_name'),
                        'ceo_name': company_info.get('ceo_nm'),
                        'industry': company_info.get('induty_code'),
                    })

                    # 상장일 파싱
                    est_dt = company_info.get('est_dt')
                    if est_dt:
                        listed_date = parse_listed_date(est_dt)
                        if listed_date:
                            company_data['listed_date'] = listed_date

                if existing:
                    # 업데이트
                    for key, value in company_data.items():
                        if value is not None:
                            setattr(existing, key, value)
                    stats['updated'] += 1
                    logger.debug(f"업데이트: {corp_name} ({corp_code})")
                else:
                    # 신규 삽입
                    new_company = Company(**company_data)
                    db.add(new_company)
                    stats['inserted'] += 1
                    logger.debug(f"신규 삽입: {corp_name} ({corp_code})")

                # 100개마다 커밋
                if idx % 100 == 0:
                    db.commit()

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"오류 발생 ({corp['corp_name']}): {e}")
                continue

        # 최종 커밋
        db.commit()
        logger.info("데이터베이스 커밋 완료")

    # 결과 출력
    logger.info("=" * 80)
    logger.info("회사 정보 가져오기 완료!")
    logger.info(f"총 회사 수: {stats['total']}")
    logger.info(f"상장사: {stats['listed']}")
    logger.info(f"비상장사: {stats['unlisted']}")
    logger.info(f"신규 삽입: {stats['inserted']}")
    logger.info(f"업데이트: {stats['updated']}")
    logger.info(f"스킵: {stats['skipped']}")
    logger.info(f"오류: {stats['errors']}")
    logger.info("=" * 80)


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="OpenDart API에서 회사 정보를 가져와 DB에 저장"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="가져올 회사 수 제한 (기본값: 전체)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="비상장사 포함 전체 회사 가져오기 (기본값: 상장사만)"
    )

    args = parser.parse_args()

    logger.info("OpenDart API 회사 정보 가져오기 시작")
    logger.info(f"API 키: {DART_API_KEY[:10]}...")
    logger.info(f"제한: {args.limit if args.limit else '없음'}")
    logger.info(f"대상: {'전체 회사' if args.all else '상장사만'}")
    logger.info("=" * 80)

    import_companies(
        limit=args.limit,
        only_listed=not args.all
    )


if __name__ == "__main__":
    main()
