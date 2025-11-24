"""
시세 조회 서비스
- 전체 종목 시세 리스트 조회
- 정렬 기능 (거래량, 등락률, 거래대금, 시가총액)
- 페이지네이션
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.user_favorite_stock import UserFavoriteStock
from app.schemas.market_quote import SortBy, SortOrder

logger = logging.getLogger(__name__)


class MarketQuoteService:
    """시세 조회 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_market_quotes(
        self,
        sort_by: SortBy = SortBy.MARKET_CAP,
        sort_order: SortOrder = SortOrder.DESC,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[UUID] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 종목 시세 조회

        Args:
            sort_by: 정렬 기준
            sort_order: 정렬 순서
            page: 페이지 번호
            page_size: 페이지 크기
            user_id: 사용자 ID (관심종목 판단용, 선택)
            search: 검색어 (종목명 또는 종목코드, 부분 일치)

        Returns:
            시세 리스트 및 페이지네이션 정보
        """
        # 1. 최신 거래일 찾기
        latest_trade_date = await self._get_latest_trade_date()
        if not latest_trade_date:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "has_next": False
            }

        # 1-1. 전일 거래일 찾기
        prev_trade_date_query = (
            select(StockPrice.trade_date)
            .where(StockPrice.trade_date < latest_trade_date)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        prev_date_result = await self.db.execute(prev_trade_date_query)
        prev_trade_date = prev_date_result.scalar_one_or_none()

        # 2. 정렬 컬럼 매핑
        sort_column = self._get_sort_column(sort_by)
        order_func = desc if sort_order == SortOrder.DESC else asc

        # 3. 시세 데이터 조회 (전일 데이터와 JOIN하여 등락률 계산)
        offset = (page - 1) * page_size

        # 전일 주가 서브쿼리 (별칭: prev)
        PrevStockPrice = StockPrice.__table__.alias("prev_stock_price")

        # WHERE 조건 구성
        where_conditions = [StockPrice.trade_date == latest_trade_date]

        # 검색어가 있으면 종목명 또는 종목코드로 필터링
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            where_conditions.append(
                (Company.stock_name.ilike(search_term)) |
                (Company.stock_code.ilike(search_term))
            )

        query = (
            select(
                Company.stock_code,
                Company.stock_name,
                Company.industry,
                Company.company_id,
                StockPrice.close_price,
                StockPrice.change_vs_1d,
                StockPrice.fluctuation_rate,
                StockPrice.volume,
                StockPrice.trading_value,
                StockPrice.market_cap,
                StockPrice.trade_date,
                PrevStockPrice.c.close_price.label("prev_close_price")
            )
            .join(StockPrice, Company.company_id == StockPrice.company_id)
            .outerjoin(
                PrevStockPrice,
                and_(
                    PrevStockPrice.c.company_id == Company.company_id,
                    PrevStockPrice.c.trade_date == prev_trade_date
                )
            )
            .where(and_(*where_conditions))
            .order_by(order_func(sort_column))
            .offset(offset)
            .limit(page_size + 1)  # has_next 판단을 위해 1개 더 조회
        )

        result = await self.db.execute(query)
        rows = result.all()

        # 4. has_next 판단
        has_next = len(rows) > page_size
        if has_next:
            rows = rows[:page_size]

        # 5. 전체 개수 조회 (검색 조건 포함)
        count_query = (
            select(func.count())
            .select_from(Company)
            .join(StockPrice, Company.company_id == StockPrice.company_id)
            .where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 6. 관심종목 목록 조회 (user_id가 있는 경우)
        favorite_stock_codes = set()
        if user_id:
            favorite_query = select(UserFavoriteStock.stock_code).where(
                UserFavoriteStock.user_id == user_id
            )
            favorite_result = await self.db.execute(favorite_query)
            favorite_stock_codes = {row[0] for row in favorite_result.all()}

        # 7. 응답 데이터 생성 (rank 추가)
        offset = (page - 1) * page_size
        items = []
        for idx, row in enumerate(rows):
            # fluctuation_rate 계산: DB값 우선, 없으면 전일 종가로 계산
            fluctuation_rate = row.fluctuation_rate
            change_amount = row.change_vs_1d

            if fluctuation_rate is None and row.prev_close_price and row.prev_close_price != 0:
                # 등락률 = ((현재가 - 전일종가) / 전일종가) * 100
                fluctuation_rate = ((row.close_price - row.prev_close_price) / row.prev_close_price) * 100
                # 등락 금액도 계산
                if change_amount is None:
                    change_amount = row.close_price - row.prev_close_price
            elif fluctuation_rate is None:
                fluctuation_rate = 0.0

            items.append({
                "rank": offset + idx + 1,  # 페이지 기준 순위 계산
                "name": row.stock_name,
                "code": row.stock_code,
                "theme": row.industry,
                "price": row.close_price or 0,
                "change_amount": change_amount or 0,
                "change_rate": fluctuation_rate,
                "trend": self._get_trend(fluctuation_rate),
                "volume": row.volume or 0,
                "trading_value": row.trading_value or 0,
                "market_cap": row.market_cap,
                "is_favorite": row.stock_code in favorite_stock_codes
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": has_next
        }

    async def _get_latest_trade_date(self) -> Optional[datetime.date]:
        """최신 거래일 조회"""
        query = (
            select(StockPrice.trade_date)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        result = await self.db.execute(query)
        row = result.scalar_one_or_none()
        return row

    def _get_sort_column(self, sort_by: SortBy):
        """정렬 컬럼 매핑"""
        sort_map = {
            SortBy.VOLUME: StockPrice.volume,
            SortBy.CHANGE_RATE: StockPrice.fluctuation_rate,
            SortBy.TRADING_VALUE: StockPrice.trading_value,
            SortBy.MARKET_CAP: StockPrice.market_cap,
            SortBy.NAME: Company.stock_name
        }
        return sort_map.get(sort_by, StockPrice.market_cap)

    @staticmethod
    def _get_trend(change_rate: Optional[float]) -> str:
        """등락 추세 판단"""
        if change_rate is None or change_rate == 0:
            return "flat"
        return "up" if change_rate > 0 else "down"
