"""
팩터 계산 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date
from decimal import Decimal


# =====================
# 팩터 계산 요청/응답
# =====================

class FactorCalculationRequest(BaseModel):
    """팩터 계산 요청"""
    stock_codes: Optional[List[str]] = Field(None, description="종목코드 리스트 (없으면 전체)")
    base_date: date = Field(..., description="기준일")
    market_type: Optional[str] = Field(None, description="시장 구분 (KOSPI/KOSDAQ/ALL)")


class FactorValue(BaseModel):
    """팩터 값"""
    stock_code: str
    company_name: str
    value: Optional[float] = None
    rank: Optional[int] = None


class FactorCalculationResponse(BaseModel):
    """팩터 계산 응답"""
    factor_id: str
    factor_name: str
    base_date: date
    data: List[FactorValue]
    total_count: int
    calculation_time_ms: float


# =====================
# 개별 팩터 스키마
# =====================

# 가치 팩터
class PERResponse(BaseModel):
    """PER (주가수익비율) 응답"""
    stock_code: str
    company_name: str
    close_price: int
    eps: Optional[Decimal] = None  # 주당순이익
    per: Optional[float] = None
    rank: Optional[int] = None


class PBRResponse(BaseModel):
    """PBR (주가순자산비율) 응답"""
    stock_code: str
    company_name: str
    close_price: int
    bps: Optional[Decimal] = None  # 주당순자산가치
    pbr: Optional[float] = None
    rank: Optional[int] = None


class PSRResponse(BaseModel):
    """PSR (주가매출비율) 응답"""
    stock_code: str
    company_name: str
    market_cap: Optional[int] = None
    revenue: Optional[Decimal] = None
    psr: Optional[float] = None
    rank: Optional[int] = None


class PCRResponse(BaseModel):
    """PCR (주가현금흐름비율) 응답"""
    stock_code: str
    company_name: str
    market_cap: Optional[int] = None
    operating_cashflow: Optional[Decimal] = None
    pcr: Optional[float] = None
    rank: Optional[int] = None


class DividendYieldResponse(BaseModel):
    """배당수익률 응답"""
    stock_code: str
    company_name: str
    close_price: int
    dividend_per_share: Optional[Decimal] = None
    dividend_yield: Optional[float] = None
    rank: Optional[int] = None


# 퀄리티 팩터
class ROEResponse(BaseModel):
    """ROE (자기자본이익률) 응답"""
    stock_code: str
    company_name: str
    net_income: Optional[Decimal] = None
    equity: Optional[Decimal] = None
    roe: Optional[float] = None
    rank: Optional[int] = None


class ROAResponse(BaseModel):
    """ROA (총자산이익률) 응답"""
    stock_code: str
    company_name: str
    net_income: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    roa: Optional[float] = None
    rank: Optional[int] = None


class GrossProfitMarginResponse(BaseModel):
    """매출총이익률 응답"""
    stock_code: str
    company_name: str
    revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    gross_profit_margin: Optional[float] = None
    rank: Optional[int] = None


class DebtRatioResponse(BaseModel):
    """부채비율 응답"""
    stock_code: str
    company_name: str
    total_liabilities: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None
    debt_ratio: Optional[float] = None
    rank: Optional[int] = None


class CurrentRatioResponse(BaseModel):
    """유동비율 응답"""
    stock_code: str
    company_name: str
    current_assets: Optional[Decimal] = None
    current_liabilities: Optional[Decimal] = None
    current_ratio: Optional[float] = None
    rank: Optional[int] = None


# 성장 팩터
class RevenueGrowthResponse(BaseModel):
    """매출액증가율 응답"""
    stock_code: str
    company_name: str
    current_revenue: Optional[Decimal] = None
    previous_revenue: Optional[Decimal] = None
    revenue_growth: Optional[float] = None
    rank: Optional[int] = None


class OperatingProfitGrowthResponse(BaseModel):
    """영업이익증가율 응답"""
    stock_code: str
    company_name: str
    current_operating_profit: Optional[Decimal] = None
    previous_operating_profit: Optional[Decimal] = None
    operating_profit_growth: Optional[float] = None
    rank: Optional[int] = None


class EPSGrowthResponse(BaseModel):
    """EPS증가율 응답"""
    stock_code: str
    company_name: str
    current_eps: Optional[Decimal] = None
    previous_eps: Optional[Decimal] = None
    eps_growth: Optional[float] = None
    rank: Optional[int] = None


class AssetGrowthResponse(BaseModel):
    """자산증가율 응답"""
    stock_code: str
    company_name: str
    current_assets: Optional[Decimal] = None
    previous_assets: Optional[Decimal] = None
    asset_growth: Optional[float] = None
    rank: Optional[int] = None


# 모멘텀 팩터
class MomentumResponse(BaseModel):
    """모멘텀 (수익률) 응답"""
    stock_code: str
    company_name: str
    current_price: int
    past_price: Optional[int] = None
    return_pct: Optional[float] = None
    rank: Optional[int] = None


class VolumeResponse(BaseModel):
    """거래량 응답"""
    stock_code: str
    company_name: str
    avg_volume: Optional[float] = None
    rank: Optional[int] = None


class TradingValueResponse(BaseModel):
    """거래대금 응답"""
    stock_code: str
    company_name: str
    avg_trading_value: Optional[float] = None
    rank: Optional[int] = None


class HighPriceRatioResponse(BaseModel):
    """52주 최고가 대비 응답"""
    stock_code: str
    company_name: str
    current_price: int
    high_52w: Optional[int] = None
    high_price_ratio: Optional[float] = None
    rank: Optional[int] = None


# 규모 팩터
class MarketCapResponse(BaseModel):
    """시가총액 응답"""
    stock_code: str
    company_name: str
    market_cap: Optional[int] = None
    rank: Optional[int] = None


class RevenueResponse(BaseModel):
    """매출액 응답"""
    stock_code: str
    company_name: str
    revenue: Optional[Decimal] = None
    rank: Optional[int] = None


class TotalAssetsResponse(BaseModel):
    """총자산 응답"""
    stock_code: str
    company_name: str
    total_assets: Optional[Decimal] = None
    rank: Optional[int] = None


# =====================
# 멀티 팩터 조합
# =====================

class MultiFactorRequest(BaseModel):
    """멀티 팩터 요청"""
    factor_ids: List[str] = Field(..., description="팩터 ID 리스트")
    weights: Optional[Dict[str, float]] = Field(None, description="팩터별 가중치 (합=1)")
    stock_codes: Optional[List[str]] = None
    base_date: date
    market_type: Optional[str] = None


class MultiFactorScore(BaseModel):
    """멀티 팩터 스코어"""
    stock_code: str
    company_name: str
    individual_scores: Dict[str, float]  # 팩터별 개별 점수
    total_score: float  # 가중 합산 점수
    rank: int


class MultiFactorResponse(BaseModel):
    """멀티 팩터 응답"""
    base_date: date
    factors: List[str]
    weights: Dict[str, float]
    data: List[MultiFactorScore]
    total_count: int
