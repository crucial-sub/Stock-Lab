"""
종목 재무 정보 API 라우터
- 종목 기본 정보
- 투자지표 (PER, PSR, PBR, PCR)
- 수익지표 (EPS, BPS, ROE, ROA)
- 재무비율 (부채비율, 유동비율)
- 분기별 실적 (매출, 순이익 등)
- 재무제표 (손익계산서, 재무상태표)
- 5년 일별 차트 데이터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from app.core.database import get_db
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.models.income_statement import IncomeStatement
from app.models.balance_sheet import BalanceSheet
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class CompanyBasicInfo(BaseModel):
    """종목 기본 정보"""
    model_config = ConfigDict(populate_by_name=True)

    company_name: str = Field(..., serialization_alias="companyName")
    stock_code: str = Field(..., serialization_alias="stockCode")
    stock_name: Optional[str] = Field(None, serialization_alias="stockName")
    market_type: Optional[str] = Field(None, serialization_alias="marketType")
    market_cap: Optional[int] = Field(None, serialization_alias="marketCap")
    ceo_name: Optional[str] = Field(None, serialization_alias="ceoName")
    listed_shares: Optional[int] = Field(None, serialization_alias="listedShares")
    listed_date: Optional[str] = Field(None, serialization_alias="listedDate")
    industry: Optional[str] = None


class InvestmentIndicators(BaseModel):
    """투자지표 (가치평가)"""
    model_config = ConfigDict(populate_by_name=True)

    per: Optional[float] = Field(None, description="주가수익비율")
    psr: Optional[float] = Field(None, description="주가매출비율")
    pbr: Optional[float] = Field(None, description="주가순자산비율")
    pcr: Optional[float] = Field(None, description="주가현금흐름비율")


class ProfitabilityIndicators(BaseModel):
    """수익지표"""
    model_config = ConfigDict(populate_by_name=True)

    eps: Optional[float] = Field(None, description="주당순이익")
    bps: Optional[float] = Field(None, description="주당순자산")
    roe: Optional[float] = Field(None, description="자기자본이익률")
    roa: Optional[float] = Field(None, description="총자산이익률")


class FinancialRatios(BaseModel):
    """재무비율"""
    model_config = ConfigDict(populate_by_name=True)

    debt_ratio: Optional[float] = Field(None, serialization_alias="debtRatio", description="부채비율")
    current_ratio: Optional[float] = Field(None, serialization_alias="currentRatio", description="유동비율")


class QuarterlyPerformance(BaseModel):
    """분기별 실적"""
    model_config = ConfigDict(populate_by_name=True)

    period: str = Field(..., description="분기 (예: 2024Q1)")
    revenue: Optional[int] = Field(None, description="매출액")
    operating_income: Optional[int] = Field(None, serialization_alias="operatingIncome", description="영업이익")
    net_income: Optional[int] = Field(None, serialization_alias="netIncome", description="당기순이익")
    net_profit_margin: Optional[float] = Field(None, serialization_alias="netProfitMargin", description="순이익률 (%)")
    net_income_growth: Optional[float] = Field(None, serialization_alias="netIncomeGrowth", description="순이익 성장률 (%)")
    operating_margin: Optional[float] = Field(None, serialization_alias="operatingMargin", description="영업이익률 (%)")
    operating_income_growth: Optional[float] = Field(None, serialization_alias="operatingIncomeGrowth", description="영업이익 증가율 (%)")


class IncomeStatementData(BaseModel):
    """손익계산서 데이터"""
    model_config = ConfigDict(populate_by_name=True)

    period: str = Field(..., description="분기")
    revenue: Optional[int] = Field(None, description="매출액")
    cost_of_sales: Optional[int] = Field(None, serialization_alias="costOfSales", description="매출원가")
    gross_profit: Optional[int] = Field(None, serialization_alias="grossProfit", description="매출총이익")
    operating_income: Optional[int] = Field(None, serialization_alias="operatingIncome", description="영업이익")
    net_income: Optional[int] = Field(None, serialization_alias="netIncome", description="당기순이익")


class BalanceSheetData(BaseModel):
    """재무상태표 데이터"""
    model_config = ConfigDict(populate_by_name=True)

    period: str = Field(..., description="분기")
    total_assets: Optional[int] = Field(None, serialization_alias="totalAssets", description="자산총계")
    total_liabilities: Optional[int] = Field(None, serialization_alias="totalLiabilities", description="부채총계")
    total_equity: Optional[int] = Field(None, serialization_alias="totalEquity", description="자본총계")


class PriceHistoryPoint(BaseModel):
    """일별 차트 데이터 포인트"""
    model_config = ConfigDict(populate_by_name=True)

    date: str = Field(..., description="거래일자")
    open: Optional[int] = Field(None, description="시가")
    high: Optional[int] = Field(None, description="고가")
    low: Optional[int] = Field(None, description="저가")
    close: Optional[int] = Field(None, description="종가")
    volume: Optional[int] = Field(None, description="거래량")


class CompanyInfoResponse(BaseModel):
    """종목 재무 정보 통합 응답"""
    model_config = ConfigDict(populate_by_name=True)

    basic_info: CompanyBasicInfo = Field(..., serialization_alias="basicInfo")
    investment_indicators: InvestmentIndicators = Field(..., serialization_alias="investmentIndicators")
    profitability_indicators: ProfitabilityIndicators = Field(..., serialization_alias="profitabilityIndicators")
    financial_ratios: FinancialRatios = Field(..., serialization_alias="financialRatios")
    quarterly_performance: List[QuarterlyPerformance] = Field(..., serialization_alias="quarterlyPerformance")
    income_statements: List[IncomeStatementData] = Field(..., serialization_alias="incomeStatements")
    balance_sheets: List[BalanceSheetData] = Field(..., serialization_alias="balanceSheets")
    price_history: List[PriceHistoryPoint] = Field(..., serialization_alias="priceHistory")


@router.get("/company/{stock_code}/info", response_model=CompanyInfoResponse)
async def get_company_info(
    stock_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    종목의 모든 재무 정보를 반환

    Args:
        stock_code: 종목 코드 (6자리, 예: 005930)
        db: 데이터베이스 세션

    Returns:
        CompanyInfoResponse: 종목의 모든 재무 정보
    """
    try:
        # 1. 기업 정보 조회
        company_query = select(Company).where(Company.stock_code == stock_code)
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"종목 코드 {stock_code}를 찾을 수 없습니다")

        # 2. 최신 주가 정보 조회 (시가총액, 발행주식수)
        latest_price_query = (
            select(StockPrice)
            .where(StockPrice.company_id == company.company_id)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        latest_price_result = await db.execute(latest_price_query)
        latest_price = latest_price_result.scalar_one_or_none()

        # 3. 최근 5년 일별 차트 데이터
        five_years_ago = datetime.now().date() - timedelta(days=365 * 5)
        price_history_query = (
            select(StockPrice)
            .where(
                and_(
                    StockPrice.company_id == company.company_id,
                    StockPrice.trade_date >= five_years_ago
                )
            )
            .order_by(StockPrice.trade_date)
        )
        price_history_result = await db.execute(price_history_query)
        price_history = price_history_result.scalars().all()

        # 4. 최근 재무제표 조회 (최근 8분기)
        financial_statements_query = (
            select(FinancialStatement)
            .where(FinancialStatement.company_id == company.company_id)
            .order_by(
                desc(FinancialStatement.bsns_year),
                desc(FinancialStatement.reprt_code)
            )
            .limit(8)
        )
        financial_statements_result = await db.execute(financial_statements_query)
        financial_statements = financial_statements_result.scalars().all()

        # 5. 각 재무제표별로 손익계산서 및 재무상태표 조회
        quarterly_performance_list = []
        income_statements_list = []
        balance_sheets_list = []

        # 최신 재무제표에서 투자지표 및 수익지표 계산에 필요한 데이터 추출
        latest_net_income = None
        latest_revenue = None
        latest_total_assets = None
        latest_total_equity = None
        latest_total_liabilities = None
        latest_current_assets = None
        latest_current_liabilities = None
        latest_operating_cf = None

        for idx, fs in enumerate(financial_statements):
            # 분기 표시 (예: 2024Q1)
            quarter_map = {
                "11013": "Q1",  # 1분기
                "11012": "Q2",  # 반기 (2분기)
                "11014": "Q3",  # 3분기
                "11011": "Q4"   # 사업보고서 (연간)
            }
            quarter = quarter_map.get(fs.reprt_code, "")
            period = f"{fs.bsns_year}{quarter}"

            # 손익계산서 조회
            income_query = (
                select(IncomeStatement)
                .where(IncomeStatement.stmt_id == fs.stmt_id)
            )
            income_result = await db.execute(income_query)
            income_items = income_result.scalars().all()

            # 재무상태표 조회
            balance_query = (
                select(BalanceSheet)
                .where(BalanceSheet.stmt_id == fs.stmt_id)
            )
            balance_result = await db.execute(balance_query)
            balance_items = balance_result.scalars().all()

            # 손익계산서 항목 파싱
            revenue = None
            cost_of_sales = None
            gross_profit = None
            operating_income = None
            net_income = None

            for item in income_items:
                account_nm = item.account_nm.strip()
                amount = item.thstrm_amount  # 당기 금액

                if "매출액" in account_nm and "매출원가" not in account_nm and "매출총" not in account_nm:
                    revenue = amount
                elif "매출원가" in account_nm:
                    cost_of_sales = amount
                elif "매출총이익" in account_nm or "매출총손실" in account_nm:
                    gross_profit = amount
                elif "영업이익" in account_nm or "영업손실" in account_nm:
                    operating_income = amount
                elif ("당기순이익" in account_nm or "당기순손실" in account_nm) and "지배" not in account_nm:
                    net_income = amount

            # 재무상태표 항목 파싱
            total_assets = None
            total_liabilities = None
            total_equity = None
            current_assets = None
            current_liabilities = None

            for item in balance_items:
                account_nm = item.account_nm.strip()
                amount = item.thstrm_amount

                if "자산총계" in account_nm:
                    total_assets = amount
                elif "부채총계" in account_nm:
                    total_liabilities = amount
                elif "자본총계" in account_nm:
                    total_equity = amount
                elif "유동자산" in account_nm:
                    current_assets = amount
                elif "유동부채" in account_nm:
                    current_liabilities = amount

            # 최신 재무제표 데이터 저장 (지표 계산용)
            if idx == 0:
                latest_net_income = net_income
                latest_revenue = revenue
                latest_total_assets = total_assets
                latest_total_equity = total_equity
                latest_total_liabilities = total_liabilities
                latest_current_assets = current_assets
                latest_current_liabilities = current_liabilities

            # 분기별 실적 계산
            net_profit_margin = None
            operating_margin = None
            if revenue and revenue != 0:
                if net_income is not None:
                    net_profit_margin = round((net_income / revenue) * 100, 2)
                if operating_income is not None:
                    operating_margin = round((operating_income / revenue) * 100, 2)

            # 전분기 대비 성장률 계산 (다음 분기와 비교)
            net_income_growth = None
            operating_income_growth = None
            if idx < len(financial_statements) - 1:
                prev_fs = financial_statements[idx + 1]

                # 전분기 손익계산서 조회
                prev_income_query = (
                    select(IncomeStatement)
                    .where(IncomeStatement.stmt_id == prev_fs.stmt_id)
                )
                prev_income_result = await db.execute(prev_income_query)
                prev_income_items = prev_income_result.scalars().all()

                prev_net_income = None
                prev_operating_income = None

                for item in prev_income_items:
                    account_nm = item.account_nm.strip()
                    amount = item.thstrm_amount

                    if ("당기순이익" in account_nm or "당기순손실" in account_nm) and "지배" not in account_nm:
                        prev_net_income = amount
                    elif "영업이익" in account_nm or "영업손실" in account_nm:
                        prev_operating_income = amount

                # 성장률 계산
                if prev_net_income and prev_net_income != 0 and net_income is not None:
                    net_income_growth = round(((net_income - prev_net_income) / prev_net_income) * 100, 2)

                if prev_operating_income and prev_operating_income != 0 and operating_income is not None:
                    operating_income_growth = round(((operating_income - prev_operating_income) / prev_operating_income) * 100, 2)

            # 분기별 실적 추가
            quarterly_performance_list.append(QuarterlyPerformance(
                period=period,
                revenue=revenue,
                operating_income=operating_income,
                net_income=net_income,
                net_profit_margin=net_profit_margin,
                net_income_growth=net_income_growth,
                operating_margin=operating_margin,
                operating_income_growth=operating_income_growth
            ))

            # 손익계산서 데이터 추가
            income_statements_list.append(IncomeStatementData(
                period=period,
                revenue=revenue,
                cost_of_sales=cost_of_sales,
                gross_profit=gross_profit,
                operating_income=operating_income,
                net_income=net_income
            ))

            # 재무상태표 데이터 추가
            balance_sheets_list.append(BalanceSheetData(
                period=period,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                total_equity=total_equity
            ))

        # 6. 투자지표 계산
        per = None
        psr = None
        pbr = None
        pcr = None

        if latest_price and latest_price.market_cap:
            market_cap = latest_price.market_cap

            # PER = 시가총액 / 순이익
            if latest_net_income and latest_net_income != 0:
                per = round(market_cap / latest_net_income, 2)

            # PSR = 시가총액 / 매출액
            if latest_revenue and latest_revenue != 0:
                psr = round(market_cap / latest_revenue, 2)

            # PBR = 시가총액 / 자본총계
            if latest_total_equity and latest_total_equity != 0:
                pbr = round(market_cap / latest_total_equity, 2)

            # PCR = 시가총액 / 영업현금흐름 (현재 데이터 없음)
            if latest_operating_cf and latest_operating_cf != 0:
                pcr = round(market_cap / latest_operating_cf, 2)

        # 7. 수익지표 계산
        eps = None
        bps = None
        roe = None
        roa = None

        if latest_price and latest_price.listed_shares and latest_price.listed_shares != 0:
            listed_shares = latest_price.listed_shares

            # EPS = 당기순이익 / 발행주식수
            if latest_net_income:
                eps = round(latest_net_income / listed_shares, 2)

            # BPS = 자본총계 / 발행주식수
            if latest_total_equity:
                bps = round(latest_total_equity / listed_shares, 2)

        # ROE = 당기순이익 / 자본총계 × 100
        if latest_net_income and latest_total_equity and latest_total_equity != 0:
            roe = round((latest_net_income / latest_total_equity) * 100, 2)

        # ROA = 당기순이익 / 자산총계 × 100
        if latest_net_income and latest_total_assets and latest_total_assets != 0:
            roa = round((latest_net_income / latest_total_assets) * 100, 2)

        # 8. 재무비율 계산
        debt_ratio = None
        current_ratio = None

        # 부채비율 = 부채총계 / 자본총계 × 100
        if latest_total_liabilities and latest_total_equity and latest_total_equity != 0:
            debt_ratio = round((latest_total_liabilities / latest_total_equity) * 100, 2)

        # 유동비율 = 유동자산 / 유동부채 × 100
        if latest_current_assets and latest_current_liabilities and latest_current_liabilities != 0:
            current_ratio = round((latest_current_assets / latest_current_liabilities) * 100, 2)

        # 9. 응답 생성
        return CompanyInfoResponse(
            basic_info=CompanyBasicInfo(
                company_name=company.company_name,
                stock_code=company.stock_code,
                stock_name=company.stock_name,
                market_type=company.market_type,
                market_cap=latest_price.market_cap if latest_price else None,
                ceo_name=company.ceo_name,
                listed_shares=latest_price.listed_shares if latest_price else None,
                listed_date=company.listed_date.isoformat() if company.listed_date else None,
                industry=company.industry
            ),
            investment_indicators=InvestmentIndicators(
                per=per,
                psr=psr,
                pbr=pbr,
                pcr=pcr
            ),
            profitability_indicators=ProfitabilityIndicators(
                eps=eps,
                bps=bps,
                roe=roe,
                roa=roa
            ),
            financial_ratios=FinancialRatios(
                debt_ratio=debt_ratio,
                current_ratio=current_ratio
            ),
            quarterly_performance=quarterly_performance_list,
            income_statements=income_statements_list,
            balance_sheets=balance_sheets_list,
            price_history=[
                PriceHistoryPoint(
                    date=price.trade_date.isoformat(),
                    open=price.open_price,
                    high=price.high_price,
                    low=price.low_price,
                    close=price.close_price,
                    volume=price.volume
                )
                for price in price_history
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 정보 조회 실패 ({stock_code}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"종목 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/company/search")
async def search_companies(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    종목 검색 (종목명 또는 종목 코드로 검색)

    Args:
        query: 검색어 (종목명 또는 종목 코드)
        limit: 최대 결과 수
        db: 데이터베이스 세션

    Returns:
        검색된 종목 목록
    """
    try:
        search_query = (
            select(Company)
            .where(
                and_(
                    Company.is_active == 1,
                    or_(
                        Company.company_name.like(f"%{query}%"),
                        Company.stock_name.like(f"%{query}%"),
                        Company.stock_code.like(f"%{query}%")
                    )
                )
            )
            .limit(limit)
        )

        result = await db.execute(search_query)
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

    except Exception as e:
        logger.error(f"종목 검색 실패 ({query}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"종목 검색 중 오류가 발생했습니다: {str(e)}")
