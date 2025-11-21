"""
재무 데이터 장기 캐싱 서비스
- 재무제표는 분기별로만 변경 → 장기 캐싱 가능
- TTL: 3개월 (다음 분기까지)
"""

import json
import hashlib
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.cache import cache
from app.models import BalanceSheet, IncomeStatement, CashflowStatement, FinancialStatement, Company
import logging

logger = logging.getLogger(__name__)


class FinancialDataCache:
    """재무 데이터 캐싱 관리자"""

    # TTL: 3개월 (7776000초)
    FINANCIAL_CACHE_TTL = 7776000

    @staticmethod
    def _get_cache_key(stock_code: str, fiscal_year: str, report_code: str, statement_type: str) -> str:
        """캐시 키 생성"""
        return f"financial:{statement_type}:{stock_code}:{fiscal_year}:{report_code}"

    @staticmethod
    def _get_bulk_cache_key(stock_codes: List[str], year: str, report_code: str) -> str:
        """벌크 조회용 캐시 키"""
        codes_hash = hashlib.md5(",".join(sorted(stock_codes)).encode()).hexdigest()[:8]
        return f"financial:bulk:{codes_hash}:{year}:{report_code}"

    async def get_financial_statements_cached(
        self,
        db: AsyncSession,
        stock_codes: List[str],
        fiscal_year: str,
        report_code: str = "11011"
    ) -> Dict[str, Dict[str, Dict]]:
        """
        재무제표 데이터 조회 (캐시 우선)

        Args:
            db: DB 세션
            stock_codes: 종목 코드 리스트
            fiscal_year: 회계연도 (YYYY)
            report_code: 보고서 코드 (11011:사업보고서, 11012:반기, 11013:1분기, 11014:3분기)

        Returns:
            {
                'stock_code': {
                    'balance_sheet': {...},
                    'income_statement': {...},
                    'cashflow_statement': {...}
                }
            }
        """
        # 벌크 캐시 체크
        bulk_key = self._get_bulk_cache_key(stock_codes, fiscal_year, report_code)
        cached_data = await cache.get(bulk_key)

        if cached_data:
            logger.debug(f"✅ 재무 데이터 캐시 적중: {fiscal_year}년 {report_code}, {len(stock_codes)}종목")
            return cached_data

        logger.info(f"⚠️ 재무 데이터 캐시 미스 - DB 조회: {fiscal_year}년 {report_code}, {len(stock_codes)}종목")

        # DB에서 조회
        result = {}

        # 1. 먼저 FinancialStatement를 통해 stmt_id를 가져옴
        # stock_code를 company_id로 변환하기 위해 Company 테이블 조인
        stmt_query = (
            select(FinancialStatement, Company.stock_code)
            .join(Company, FinancialStatement.company_id == Company.company_id)
            .where(
                and_(
                    Company.stock_code.in_(stock_codes),
                    FinancialStatement.bsns_year == fiscal_year,
                    FinancialStatement.reprt_code == report_code
                )
            )
        )

        stmt_result = await db.execute(stmt_query)
        stmt_rows = stmt_result.all()

        # stmt_id -> stock_code 매핑
        stmt_id_to_stock_code = {}
        stmt_ids = []
        for stmt, stock_code in stmt_rows:
            stmt_id_to_stock_code[stmt.stmt_id] = stock_code
            stmt_ids.append(stmt.stmt_id)

            # 결과 딕셔너리 초기화
            if stock_code not in result:
                result[stock_code] = {
                    'balance_sheet': {},
                    'income_statement': {},
                    'cashflow_statement': {}
                }

        if not stmt_ids:
            logger.warning(f"재무제표 데이터 없음: {fiscal_year}년 {report_code}")
            # 빈 결과도 캐싱 (단, TTL은 짧게)
            await cache.set(bulk_key, result, ttl=3600)
            return result

        # 2. Balance Sheets 조회
        bs_query = select(BalanceSheet).where(BalanceSheet.stmt_id.in_(stmt_ids))
        bs_result = await db.execute(bs_query)
        bs_data = bs_result.scalars().all()

        # 3. Income Statements 조회
        is_query = select(IncomeStatement).where(IncomeStatement.stmt_id.in_(stmt_ids))
        is_result = await db.execute(is_query)
        is_data = is_result.scalars().all()

        # 4. Cashflow Statements 조회
        cf_query = select(CashflowStatement).where(CashflowStatement.stmt_id.in_(stmt_ids))
        cf_result = await db.execute(cf_query)
        cf_data = cf_result.scalars().all()

        # 5. 결과 조합
        for bs in bs_data:
            stock_code = stmt_id_to_stock_code.get(bs.stmt_id)
            if stock_code and stock_code in result:
                account_nm = bs.account_nm
                if account_nm not in result[stock_code]['balance_sheet']:
                    result[stock_code]['balance_sheet'][account_nm] = {
                        'account_detail': bs.account_detail,
                        'thstrm_amount': bs.thstrm_amount,
                        'frmtrm_amount': bs.frmtrm_amount,
                        'bfefrmtrm_amount': bs.bfefrmtrm_amount,
                    }

        for is_item in is_data:
            stock_code = stmt_id_to_stock_code.get(is_item.stmt_id)
            if stock_code and stock_code in result:
                account_nm = is_item.account_nm
                if account_nm not in result[stock_code]['income_statement']:
                    result[stock_code]['income_statement'][account_nm] = {
                        'thstrm_amount': is_item.thstrm_amount,
                        'thstrm_add_amount': is_item.thstrm_add_amount,
                        'frmtrm_amount': is_item.frmtrm_amount,
                        'frmtrm_add_amount': is_item.frmtrm_add_amount,
                    }

        for cf in cf_data:
            stock_code = stmt_id_to_stock_code.get(cf.stmt_id)
            if stock_code and stock_code in result:
                account_nm = cf.account_nm
                if account_nm not in result[stock_code]['cashflow_statement']:
                    result[stock_code]['cashflow_statement'][account_nm] = {
                        'thstrm_amount': cf.thstrm_amount,
                        'frmtrm_amount': cf.frmtrm_amount,
                        'bfefrmtrm_amount': cf.bfefrmtrm_amount,
                    }

        # Redis에 캐싱 (3개월)
        await cache.set(bulk_key, result, ttl=self.FINANCIAL_CACHE_TTL)
        logger.info(f"✅ 재무 데이터 캐싱 완료: {fiscal_year}년 {report_code}, {len(result)}종목")

        return result

    async def get_multi_year_financial_data(
        self,
        db: AsyncSession,
        stock_codes: List[str],
        years: List[str],
        report_code: str = "11011"
    ) -> Dict[str, List[Dict]]:
        """
        여러 연도의 재무 데이터 조회 (성장률 계산용)

        Args:
            db: DB 세션
            stock_codes: 종목 코드 리스트
            years: 연도 리스트 (예: ['2023', '2022', '2021'])
            report_code: 보고서 코드

        Returns:
            {
                'stock_code': [
                    {'year': '2023', 'data': {...}},
                    {'year': '2022', 'data': {...}},
                    ...
                ]
            }
        """
        result = {code: [] for code in stock_codes}

        # 각 연도별로 캐시에서 조회
        for year in years:
            year_data = await self.get_financial_statements_cached(
                db, stock_codes, year, report_code
            )

            for stock_code, data in year_data.items():
                if stock_code in result:
                    result[stock_code].append({
                        'year': year,
                        'data': data
                    })

        return result

    async def invalidate_financial_cache(
        self,
        stock_code: Optional[str] = None,
        fiscal_year: Optional[str] = None
    ):
        """
        재무 데이터 캐시 무효화

        Args:
            stock_code: 특정 종목만 무효화 (None이면 전체)
            fiscal_year: 특정 연도만 무효화 (None이면 전체)
        """
        if stock_code and fiscal_year:
            # 특정 종목, 특정 연도 무효화
            patterns = [
                f"financial:*:{stock_code}:{fiscal_year}:*"
            ]
        elif stock_code:
            # 특정 종목의 모든 연도 무효화
            patterns = [f"financial:*:{stock_code}:*"]
        elif fiscal_year:
            # 모든 종목의 특정 연도 무효화
            patterns = [f"financial:*:*:{fiscal_year}:*"]
        else:
            # 전체 무효화
            patterns = ["financial:*"]

        total_deleted = 0
        for pattern in patterns:
            deleted = await cache.delete(pattern)
            total_deleted += deleted

        logger.info(f"재무 캐시 무효화 완료: {total_deleted}개 키 삭제")
        return total_deleted


# 싱글톤 인스턴스
financial_cache = FinancialDataCache()
