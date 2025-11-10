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
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        전체 종목 시세 조회

        Args:
            sort_by: 정렬 기준
            sort_order: 정렬 순서
            page: 페이지 번호
            page_size: 페이지 크기
            user_id: 사용자 ID (관심종목 판단용, 선택)

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

        # 2. 정렬 컬럼 매핑
        sort_column = self._get_sort_column(sort_by)
        order_func = desc if sort_order == SortOrder.DESC else asc

        # 3. 시세 데이터 조회 (JOIN으로 한번에 가져오기)
        offset = (page - 1) * page_size

        query = (
            select(
                Company.stock_code,
                Company.stock_name,
                StockPrice.close_price,
                StockPrice.vs_previous,
                StockPrice.fluctuation_rate,
                StockPrice.volume,
                StockPrice.trading_value,
                StockPrice.market_cap,
                StockPrice.trade_date
            )
            .join(StockPrice, Company.company_id == StockPrice.company_id)
            .where(StockPrice.trade_date == latest_trade_date)
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

        # 5. 전체 개수 조회
        count_query = (
            select(func.count())
            .select_from(Company)
            .join(StockPrice, Company.company_id == StockPrice.company_id)
            .where(StockPrice.trade_date == latest_trade_date)
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

        # 7. 응답 데이터 생성
        items = [
            {
                "stock_code": row.stock_code,
                "stock_name": row.stock_name,
                "current_price": row.close_price,
                "previous_close": self._calculate_previous_close(row.close_price, row.vs_previous),
                "vs_previous": row.vs_previous or 0,
                "change_rate": row.fluctuation_rate or 0.0,
                "volume": row.volume or 0,
                "trading_value": row.trading_value or 0,
                "market_cap": row.market_cap,
                "trade_date": row.trade_date.isoformat(),
                "is_favorite": row.stock_code in favorite_stock_codes
            }
            for row in rows
        ]

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
    def _calculate_previous_close(
        close_price: Optional[int],
        vs_previous: Optional[int]
    ) -> Optional[int]:
        """전일 종가 계산"""
        if close_price is None or vs_previous is None:
            return None
        return close_price - vs_previous
