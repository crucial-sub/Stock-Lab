"""
종목 정보 조회 서비스
- 비즈니스 로직을 라우터에서 분리
- 재무 지표 계산 로직 모듈화
- 테스트 가능하고 재사용 가능한 구조
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, and_, or_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.models.income_statement import IncomeStatement
from app.models.balance_sheet import BalanceSheet
from app.models.user_favorite_stock import UserFavoriteStock

logger = logging.getLogger(__name__)


class CompanyInfoService:
    """종목 정보 조회 및 재무 지표 계산 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_company_info(self, stock_code: str, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        종목의 전체 재무 정보 조회

        Args:
            stock_code: 종목 코드 (6자리)
            user_id: 사용자 ID (선택, 관심종목 판단용)

        Returns:
            종목 기본정보, 투자지표, 수익지표, 재무비율, 분기별실적, 재무제표, 차트 데이터
        """
        # 1. 기업 정보 조회
        company = await self._get_company(stock_code)
        if not company:
            return None

        # 1-1. 관심종목 여부 확인
        is_favorite = False
        if user_id:
            is_favorite = await self._check_is_favorite(user_id, company.company_id)

        # 2. 최신 주가 정보
        latest_price = await self._get_latest_price(company.company_id)

        # 3. 기간별 변동률 계산
        change_rates = await self._calculate_period_change_rates(
            company.company_id, latest_price
        )

        # 4. 5년 차트 데이터
        price_history = await self._get_price_history(company.company_id)

        # 5. 최근 8분기 재무제표
        financial_statements = await self._get_financial_statements(company.company_id, limit=8)

        # 6. 재무제표 파싱 및 지표 계산
        (
            quarterly_performance,
            income_statements,
            balance_sheets,
            latest_financial_data
        ) = await self._process_financial_statements(financial_statements)

        # 7. 투자지표 계산
        investment_indicators = self._calculate_investment_indicators(
            latest_price, latest_financial_data
        )

        # 8. 수익지표 계산
        profitability_indicators = self._calculate_profitability_indicators(
            latest_price, latest_financial_data
        )

        # 9. 재무비율 계산
        financial_ratios = self._calculate_financial_ratios(latest_financial_data)

        # 10. 전일 종가 계산
        previous_close = self._calculate_previous_close(latest_price)

        # 11. 응답 데이터 조합
        return {
            "basic_info": {
                "company_name": company.company_name,
                "stock_code": company.stock_code,
                "stock_name": company.stock_name,
                "market_type": company.market_type,
                # 주가 정보
                "current_price": latest_price.close_price if latest_price else None,
                "previous_close": previous_close,
                "fluctuation_rate": latest_price.fluctuation_rate if latest_price else None,
                "trade_date": latest_price.trade_date.isoformat() if latest_price and latest_price.trade_date else None,
                "change_vs_1d": change_rates.get("1d_change"),
                "change_vs_1w": change_rates.get("1w_change"),
                "change_vs_1m": change_rates.get("1m_change"),
                "change_vs_2m": change_rates.get("2m_change"),
                # 기간별 변동률
                "change_rate_1d": change_rates.get("1d_rate"),
                "change_rate_1w": change_rates.get("1w_rate"),
                "change_rate_1m": change_rates.get("1m_rate"),
                "change_rate_2m": change_rates.get("2m_rate"),
                # 시가총액 정보
                "market_cap": latest_price.market_cap if latest_price else None,
                "listed_shares": latest_price.listed_shares if latest_price else None,
                # 기업 정보
                "ceo_name": company.ceo_name,
                "listed_date": company.est_dt,
                "industry": company.industry,
                # # 점수
                # "momentum_score": company.momentum_score,
                # "fundamental_score": company.fundamental_score,
                # 관심종목 여부
                "is_favorite": is_favorite
            },
            "investment_indicators": investment_indicators,
            "profitability_indicators": profitability_indicators,
            "financial_ratios": financial_ratios,
            "quarterly_performance": quarterly_performance,
            "income_statements": income_statements,
            "balance_sheets": balance_sheets,
            "price_history": [
                {
                    "date": price.trade_date.isoformat(),
                    "open": price.open_price,
                    "high": price.high_price,
                    "low": price.low_price,
                    "close": price.close_price,
                    "volume": price.volume
                }
                for price in price_history
            ]
        }

    async def search_companies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        종목 검색 (종목명 또는 종목코드)

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            검색된 종목 목록
        """
        search_query = (
            select(Company)
            .where(
                or_(
                    Company.company_name.like(f"%{query}%"),
                    Company.stock_name.like(f"%{query}%"),
                    Company.stock_code.like(f"%{query}%")
                )
            )
            .limit(limit)
        )

        result = await self.db.execute(search_query)
        companies = result.scalars().all()

        return [
            {
                "companyName": company.company_name,
                "stockCode": company.stock_code,
                "stockName": company.stock_name,
                "marketType": company.market_type
            }
            for company in companies
        ]

    # ==================== Private Methods ====================

    async def _get_company(self, stock_code: str) -> Optional[Company]:
        """기업 정보 조회"""
        query = select(Company).where(Company.stock_code == stock_code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_latest_price(self, company_id: int) -> Optional[StockPrice]:
        """최신 주가 정보 조회"""
        query = (
            select(StockPrice)
            .where(StockPrice.company_id == company_id)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_price_history(
        self,
        company_id: int,
        years: int = 5
    ) -> List[StockPrice]:
        """일별 차트 데이터 조회"""
        start_date = datetime.now().date() - timedelta(days=365 * years)
        query = (
            select(StockPrice)
            .where(
                and_(
                    StockPrice.company_id == company_id,
                    StockPrice.trade_date >= start_date
                )
            )
            .order_by(StockPrice.trade_date)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_financial_statements(
        self,
        company_id: int,
        limit: int = 8
    ) -> List[FinancialStatement]:
        """재무제표 조회 (최근 N개 분기)"""
        quarter_priority = case(
            (FinancialStatement.reprt_code == "11011", 1),  # Q4 (사업보고서)
            (FinancialStatement.reprt_code == "11014", 2),  # Q3
            (FinancialStatement.reprt_code == "11012", 3),  # Q2
            (FinancialStatement.reprt_code == "11013", 4),  # Q1
            else_=5
        )
        query = (
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company_id)
            .order_by(
                desc(FinancialStatement.bsns_year),
                quarter_priority
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _process_financial_statements(
        self,
        financial_statements: List[FinancialStatement]
    ) -> Tuple[List[Dict], List[Dict], List[Dict], Dict]:
        """
        재무제표 처리 및 분기별 데이터 생성

        Returns:
            (분기별실적, 손익계산서, 재무상태표, 최신재무데이터)
        """
        quarterly_performance = []
        income_statements = []
        balance_sheets = []
        latest_financial_data = {}

        quarter_map = {
            "11013": "Q1",
            "11012": "Q2",
            "11014": "Q3",
            "11011": "Q4"
        }

        for idx, fs in enumerate(financial_statements):
            quarter = quarter_map.get(fs.reprt_code, "")
            period = f"{fs.bsns_year}{quarter}"

            # 손익계산서 파싱
            income_data = await self._parse_income_statement(fs.stmt_id)

            # 재무상태표 파싱
            balance_data = await self._parse_balance_sheet(fs.stmt_id)

            # 최신 재무 데이터 저장 (지표 계산용)
            if idx == 0:
                latest_financial_data = {**income_data, **balance_data}

            # 분기별 실적 계산
            performance = self._calculate_quarterly_performance(
                period, income_data, balance_data
            )

            # 전분기 대비 성장률 계산
            if idx < len(financial_statements) - 1:
                prev_fs = financial_statements[idx + 1]
                prev_income_data = await self._parse_income_statement(prev_fs.stmt_id)
                growth_rates = self._calculate_growth_rates(income_data, prev_income_data)
                performance.update(growth_rates)

            quarterly_performance.append(performance)

            # 손익계산서 데이터
            income_statements.append({
                "period": period,
                "revenue": income_data.get("revenue"),
                "cost_of_sales": income_data.get("cost_of_sales"),
                "gross_profit": income_data.get("gross_profit"),
                "operating_income": income_data.get("operating_income"),
                "net_income": income_data.get("net_income")
            })

            # 재무상태표 데이터
            balance_sheets.append({
                "period": period,
                "total_assets": balance_data.get("total_assets"),
                "total_liabilities": balance_data.get("total_liabilities"),
                "total_equity": balance_data.get("total_equity")
            })

        return quarterly_performance, income_statements, balance_sheets, latest_financial_data

    async def _parse_income_statement(self, stmt_id: int) -> Dict[str, Optional[int]]:
        """손익계산서 항목 파싱"""
        query = select(IncomeStatement).where(IncomeStatement.stmt_id == stmt_id)
        result = await self.db.execute(query)
        items = result.scalars().all()

        data = {
            "revenue": None,
            "cost_of_sales": None,
            "gross_profit": None,
            "operating_income": None,
            "net_income": None
        }

        for item in items:
            account_nm = item.account_nm.strip()
            amount = item.thstrm_amount

            if "매출액" in account_nm and "매출원가" not in account_nm and "매출총" not in account_nm:
                data["revenue"] = amount
            elif "매출원가" in account_nm:
                data["cost_of_sales"] = amount
            elif "매출총이익" in account_nm or "매출총손실" in account_nm:
                data["gross_profit"] = amount
            elif "영업이익" in account_nm or "영업손실" in account_nm:
                data["operating_income"] = amount
            elif ("당기순이익" in account_nm or "당기순손실" in account_nm) and "지배" not in account_nm:
                data["net_income"] = amount

        return data

    async def _parse_balance_sheet(self, stmt_id: int) -> Dict[str, Optional[int]]:
        """재무상태표 항목 파싱"""
        query = select(BalanceSheet).where(BalanceSheet.stmt_id == stmt_id)
        result = await self.db.execute(query)
        items = result.scalars().all()

        data = {
            "total_assets": None,
            "total_liabilities": None,
            "total_equity": None,
            "current_assets": None,
            "current_liabilities": None
        }

        for item in items:
            account_nm = item.account_nm.strip()
            amount = item.thstrm_amount

            if "자산총계" in account_nm:
                data["total_assets"] = amount
            elif "부채총계" in account_nm:
                data["total_liabilities"] = amount
            elif "자본총계" in account_nm:
                data["total_equity"] = amount
            elif "유동자산" in account_nm:
                data["current_assets"] = amount
            elif "유동부채" in account_nm:
                data["current_liabilities"] = amount

        return data

    def _calculate_quarterly_performance(
        self,
        period: str,
        income_data: Dict,
        balance_data: Dict
    ) -> Dict[str, Any]:
        """분기별 실적 계산"""
        revenue = income_data.get("revenue")
        operating_income = income_data.get("operating_income")
        net_income = income_data.get("net_income")

        net_profit_margin = None
        operating_margin = None

        if revenue and revenue != 0:
            if net_income is not None:
                net_profit_margin = round((net_income / revenue) * 100, 2)
            if operating_income is not None:
                operating_margin = round((operating_income / revenue) * 100, 2)

        return {
            "period": period,
            "revenue": revenue,
            "operating_income": operating_income,
            "net_income": net_income,
            "net_profit_margin": net_profit_margin,
            "operating_margin": operating_margin
        }

    def _calculate_growth_rates(
        self,
        current_data: Dict,
        previous_data: Dict
    ) -> Dict[str, Optional[float]]:
        """전분기 대비 성장률 계산"""
        net_income = current_data.get("net_income")
        prev_net_income = previous_data.get("net_income")
        operating_income = current_data.get("operating_income")
        prev_operating_income = previous_data.get("operating_income")

        net_income_growth = None
        operating_income_growth = None

        if prev_net_income and prev_net_income != 0 and net_income is not None:
            net_income_growth = round(
                ((net_income - prev_net_income) / prev_net_income) * 100, 2
            )

        if prev_operating_income and prev_operating_income != 0 and operating_income is not None:
            operating_income_growth = round(
                ((operating_income - prev_operating_income) / prev_operating_income) * 100, 2
            )

        return {
            "net_income_growth": net_income_growth,
            "operating_income_growth": operating_income_growth
        }

    def _calculate_investment_indicators(
        self,
        latest_price: Optional[StockPrice],
        financial_data: Dict
    ) -> Dict[str, Optional[float]]:
        """투자지표 계산 (PER, PSR, PBR, PCR)"""
        per = None
        psr = None
        pbr = None
        pcr = None

        if latest_price and latest_price.market_cap:
            market_cap = latest_price.market_cap
            net_income = financial_data.get("net_income")
            revenue = financial_data.get("revenue")
            total_equity = financial_data.get("total_equity")

            # PER = 시가총액 / 순이익
            if net_income and net_income != 0:
                per = round(market_cap / net_income, 2)

            # PSR = 시가총액 / 매출액
            if revenue and revenue != 0:
                psr = round(market_cap / revenue, 2)

            # PBR = 시가총액 / 자본총계
            if total_equity and total_equity != 0:
                pbr = round(market_cap / total_equity, 2)

            # PCR = 시가총액 / 영업현금흐름 (데이터 없음)
            # if operating_cf and operating_cf != 0:
            #     pcr = round(market_cap / operating_cf, 2)

        return {
            "per": per,
            "psr": psr,
            "pbr": pbr,
            "pcr": pcr
        }

    def _calculate_profitability_indicators(
        self,
        latest_price: Optional[StockPrice],
        financial_data: Dict
    ) -> Dict[str, Optional[float]]:
        """수익지표 계산 (EPS, BPS, ROE, ROA)"""
        eps = None
        bps = None
        roe = None
        roa = None

        net_income = financial_data.get("net_income")
        total_equity = financial_data.get("total_equity")
        total_assets = financial_data.get("total_assets")

        if latest_price and latest_price.listed_shares and latest_price.listed_shares != 0:
            listed_shares = latest_price.listed_shares

            # EPS = 당기순이익 / 발행주식수
            if net_income:
                eps = round(net_income / listed_shares, 2)

            # BPS = 자본총계 / 발행주식수
            if total_equity:
                bps = round(total_equity / listed_shares, 2)

        # ROE = 당기순이익 / 자본총계 × 100
        if net_income and total_equity and total_equity != 0:
            roe = round((net_income / total_equity) * 100, 2)

        # ROA = 당기순이익 / 자산총계 × 100
        if net_income and total_assets and total_assets != 0:
            roa = round((net_income / total_assets) * 100, 2)

        return {
            "eps": eps,
            "bps": bps,
            "roe": roe,
            "roa": roa
        }

    def _calculate_financial_ratios(
        self,
        financial_data: Dict
    ) -> Dict[str, Optional[float]]:
        """재무비율 계산 (부채비율, 유동비율)"""
        debt_ratio = None
        current_ratio = None

        total_liabilities = financial_data.get("total_liabilities")
        total_equity = financial_data.get("total_equity")
        current_assets = financial_data.get("current_assets")
        current_liabilities = financial_data.get("current_liabilities")

        # 부채비율 = 부채총계 / 자본총계 × 100
        if total_liabilities and total_equity and total_equity != 0:
            debt_ratio = round((total_liabilities / total_equity) * 100, 2)

        # 유동비율 = 유동자산 / 유동부채 × 100
        if current_assets and current_liabilities and current_liabilities != 0:
            current_ratio = round((current_assets / current_liabilities) * 100, 2)

        return {
            "debt_ratio": debt_ratio,
            "current_ratio": current_ratio
        }

    async def _calculate_period_change_rates(
        self,
        company_id: int,
        latest_price: Optional[StockPrice]
    ) -> Dict[str, Optional[float]]:
        """
        기간별 변동률 계산

        Args:
            company_id: 회사 ID
            latest_price: 최신 주가 정보

        Returns:
            기간별 변동률 딕셔너리 (1d, 1w, 1m, 2m)
        """
        if not latest_price or not latest_price.close_price:
            return {
                "1d_change": None,
                "1w_change": None,
                "1m_change": None,
                "2m_change": None,
                "1d_rate": None,
                "1w_rate": None,
                "1m_rate": None,
                "2m_rate": None
            }

        current_price = latest_price.close_price

        # 각 기간별 가격 조회 (거래일 기준)
        price_1d = await self._get_price_n_trading_days_ago(company_id, 1)
        price_1w = await self._get_price_n_trading_days_ago(company_id, 5)  # 5 거래일 = 1주
        price_1m = await self._get_price_n_trading_days_ago(company_id, 22)  # 22 거래일 ≈ 1개월
        price_2m = await self._get_price_n_trading_days_ago(company_id, 44)  # 44 거래일 ≈ 2개월

        # 변동량 계산
        change_vs_1d = self._calculate_change_amount(current_price, price_1d)
        change_vs_1w = self._calculate_change_amount(current_price, price_1w)
        change_vs_1m = self._calculate_change_amount(current_price, price_1m)
        change_vs_2m = self._calculate_change_amount(current_price, price_2m)

        # 변동률 계산
        change_rate_1d = self._calculate_change_rate(current_price, price_1d.close_price if price_1d else None)
        change_rate_1w = self._calculate_change_rate(current_price, price_1w.close_price if price_1w else None)
        change_rate_1m = self._calculate_change_rate(current_price, price_1m.close_price if price_1m else None)
        change_rate_2m = self._calculate_change_rate(current_price, price_2m.close_price if price_2m else None)

        return {
            "1d_change": change_vs_1d,
            "1w_change": change_vs_1w,
            "1m_change": change_vs_1m,
            "2m_change": change_vs_2m,
            "1d_rate": change_rate_1d,
            "1w_rate": change_rate_1w,
            "1m_rate": change_rate_1m,
            "2m_rate": change_rate_2m
        }

    async def _get_price_n_trading_days_ago(
        self,
        company_id: int,
        trading_days: int
    ) -> Optional[StockPrice]:
        """
        N 거래일 전 주가 조회

        Args:
            company_id: 회사 ID
            trading_days: 거래일 수

        Returns:
            N 거래일 전 주가 정보
        """
        query = (
            select(StockPrice)
            .where(StockPrice.company_id == company_id)
            .order_by(desc(StockPrice.trade_date))
            .offset(trading_days)  # N번째 건너뛰기
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _calculate_change_rate(
        self,
        current_price: Optional[int],
        past_price: Optional[int]
    ) -> Optional[float]:
        """
        변동률 계산

        Args:
            current_price: 현재 가격
            past_price: 과거 가격

        Returns:
            변동률 (%)
        """
        if not current_price or not past_price or past_price == 0:
            return None

        change_rate = ((current_price - past_price) / past_price) * 100
        return round(change_rate, 2)

    def _calculate_previous_close(
        self,
        latest_price: Optional[StockPrice]
    ) -> Optional[int]:
        """전일 종가 계산"""
        if not latest_price or latest_price.close_price is None:
            return None
        if latest_price.change_vs_1d is None:
            return None
        return latest_price.close_price - latest_price.change_vs_1d

    def _calculate_change_amount(
        self,
        current_price: Optional[int],
        past_price: Optional[StockPrice]
    ) -> Optional[int]:
        """변동량 계산 (과거 데이터 없으면 None)"""
        if current_price is None or past_price is None or past_price.close_price is None:
            return None
        return current_price - past_price.close_price

    async def _check_is_favorite(self, user_id: UUID, company_id: int) -> bool:
        """
        관심종목 여부 확인

        Args:
            user_id: 사용자 ID
            company_id: 회사 ID

        Returns:
            관심종목 여부
        """
        query = select(UserFavoriteStock).where(
            and_(
                UserFavoriteStock.user_id == user_id,
                UserFavoriteStock.company_id == company_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
