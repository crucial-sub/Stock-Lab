"""
유니버스 API 라우터
- 유니버스별 종목 그룹 정보 제공
- 시가총액 기준 종목 분류 조회
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.universe_service import UniverseService

router = APIRouter()


class UniverseInfo(BaseModel):
    """유니버스 정보"""
    id: str = Field(..., description="유니버스 ID")
    name: str = Field(..., description="유니버스 이름")
    market: str = Field(..., description="시장 구분 (KOSPI/KOSDAQ)")
    stock_count: int = Field(..., description="종목 수", serialization_alias="stockCount")
    min_cap: int = Field(..., description="최소 시가총액", serialization_alias="minCap")
    max_cap: Optional[int] = Field(None, description="최대 시가총액", serialization_alias="maxCap")

    class Config:
        populate_by_name = True


class UniversesSummaryResponse(BaseModel):
    """유니버스 요약 정보 응답"""
    trade_date: Optional[str] = Field(None, description="기준 거래일", serialization_alias="tradeDate")
    universes: List[UniverseInfo] = Field(..., description="유니버스 리스트")

    class Config:
        populate_by_name = True


class StockInfo(BaseModel):
    """종목 정보"""
    stock_code: str = Field(..., description="종목 코드", serialization_alias="stockCode")
    stock_name: str = Field(..., description="종목명", serialization_alias="stockName")
    market_cap: int = Field(..., description="시가총액", serialization_alias="marketCap")

    class Config:
        populate_by_name = True


class UniverseStocksResponse(BaseModel):
    """유니버스 종목 리스트 응답"""
    universe_id: str = Field(..., description="유니버스 ID", serialization_alias="universeId")
    universe_name: str = Field(..., description="유니버스 이름", serialization_alias="universeName")
    stock_count: int = Field(..., description="종목 수", serialization_alias="stockCount")
    stocks: List[StockInfo] = Field(..., description="종목 리스트")

    class Config:
        populate_by_name = True


class UniverseStockCountRequest(BaseModel):
    """선택된 유니버스의 종목 수 조회 요청"""
    universe_ids: List[str] = Field(..., description="조회할 유니버스 ID 리스트", alias="universeIds")
    theme_ids: List[str] = Field(default=[], description="조회할 테마(업종) 리스트", alias="themeIds")

    class Config:
        populate_by_name = True


class UniverseStockCountResponse(BaseModel):
    """선택된 유니버스의 종목 수 응답"""
    stock_count: int = Field(..., description="총 종목 수", serialization_alias="stockCount")
    universe_ids: List[str] = Field(..., description="조회한 유니버스 ID 리스트", serialization_alias="universeIds")

    class Config:
        populate_by_name = True


@router.get(
    "",
    response_model=UniversesSummaryResponse,
    summary="유니버스 요약 정보 조회",
    description="모든 유니버스의 종목 수 요약 정보를 조회합니다."
)
async def get_universes_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    모든 유니버스의 요약 정보 조회

    - 코스피: 초대형, 대형, 중형, 소형
    - 코스닥: 초대형, 대형, 중형, 소형
    - 각 유니버스별 종목 수 포함
    """
    service = UniverseService(db)
    summary = await service.get_universes_summary()

    return UniversesSummaryResponse(
        trade_date=summary["trade_date"],
        universes=[
            UniverseInfo(
                id=u["id"],
                name=u["name"],
                market=u["market"],
                stock_count=u["stock_count"],
                min_cap=u["min_cap"],
                max_cap=u["max_cap"]
            )
            for u in summary["universes"]
        ]
    )


@router.get(
    "/{universe_id}/stocks",
    response_model=UniverseStocksResponse,
    summary="유니버스별 종목 리스트 조회",
    description="특정 유니버스에 속한 종목 리스트를 조회합니다."
)
async def get_universe_stocks(
    universe_id: str,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 유니버스의 종목 리스트 조회

    Parameters:
    - universe_id: 유니버스 ID (KOSPI_MEGA, KOSPI_LARGE, KOSPI_MID, KOSPI_SMALL,
                                  KOSDAQ_MEGA, KOSDAQ_LARGE, KOSDAQ_MID, KOSDAQ_SMALL)
    - limit: 최대 조회 종목 수 (선택)
    """
    service = UniverseService(db)

    # 유니버스 이름 찾기
    universe_name = None
    for market, universes in service.UNIVERSES.items():
        if universe_id in universes:
            universe_name = universes[universe_id]["name"]
            break

    if not universe_name:
        raise HTTPException(status_code=404, detail=f"유니버스를 찾을 수 없습니다: {universe_id}")

    stocks = await service.get_stocks_in_universe(universe_id, limit)

    return UniverseStocksResponse(
        universe_id=universe_id,
        universe_name=universe_name,
        stock_count=len(stocks),
        stocks=[
            StockInfo(
                stock_code=s["stock_code"],
                stock_name=s["stock_name"],
                market_cap=s["market_cap"]
            )
            for s in stocks
        ]
    )


@router.post(
    "/stock-count",
    response_model=UniverseStockCountResponse,
    summary="선택된 유니버스의 종목 수 조회",
    description="선택된 유니버스들의 총 종목 수를 조회합니다 (중복 제거)."
)
async def get_universe_stock_count(
    request: UniverseStockCountRequest = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    선택된 유니버스들의 종목 수 조회 (테마 필터 적용 가능)

    Parameters:
    - universe_ids: 유니버스 ID 리스트
    - theme_ids: 테마(업종) 리스트 (선택)

    Returns:
    - stock_count: 총 종목 수 (중복 제거, 테마 필터 적용 시 교집합)
    - universe_ids: 조회한 유니버스 ID 리스트
    """
    from app.models.company import Company
    from sqlalchemy import select, and_

    # 빈 리스트인 경우 0 반환
    if not request.universe_ids and not request.theme_ids:
        return UniverseStockCountResponse(
            stock_count=0,
            universe_ids=[]
        )

    # 1. 유니버스 필터가 있으면 유니버스 종목 가져오기
    universe_stock_codes = set()
    if request.universe_ids:
        service = UniverseService(db)
        universe_stock_codes = set(await service.get_stock_codes_by_universes(request.universe_ids))

    # 2. 테마(업종) 필터가 있으면 테마 종목 가져오기
    theme_stock_codes = set()
    if request.theme_ids:
        theme_query = select(Company.stock_code).where(
            Company.industry.in_(request.theme_ids)
        )
        theme_result = await db.execute(theme_query)
        theme_stock_codes = set([row[0] for row in theme_result.fetchall()])

    # 3. 교집합 계산
    if request.universe_ids and request.theme_ids:
        # 유니버스와 테마 모두 선택 -> 교집합
        final_stock_codes = universe_stock_codes & theme_stock_codes
    elif request.universe_ids:
        # 유니버스만 선택
        final_stock_codes = universe_stock_codes
    else:
        # 테마만 선택
        final_stock_codes = theme_stock_codes

    return UniverseStockCountResponse(
        stock_count=len(final_stock_codes),
        universe_ids=request.universe_ids
    )
