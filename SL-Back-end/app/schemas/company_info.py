"""
종목 재무 정보 API 스키마
- Request/Response 데이터 구조 정의
- Pydantic 모델을 사용한 데이터 검증
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


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
    momentum_score: Optional[float] = Field(None, serialization_alias="momentumScore")
    fundamental_score: Optional[float] = Field(None, serialization_alias="fundamentalScore")


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
