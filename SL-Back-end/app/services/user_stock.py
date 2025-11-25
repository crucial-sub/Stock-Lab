"""
사용자 관심종목/최근 본 주식 서비스
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user_favorite_stock import UserFavoriteStock
from app.models.user_recent_stock import UserRecentStock
from app.models.company import Company
from app.models.stock_price import StockPrice

logger = logging.getLogger(__name__)


class UserStockService:
    """사용자 관심종목/최근 본 주식 관리 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== 관심종목 ====================

    async def add_favorite(self, user_id: UUID, stock_code: str) -> Dict[str, Any]:
        """
        관심종목 추가

        Args:
            user_id: 사용자 ID
            stock_code: 종목 코드

        Returns:
            추가된 관심종목 정보
        """
        # 1. 회사 정보 조회
        company = await self._get_company_by_code(stock_code)
        if not company:
            raise ValueError(f"종목 코드 {stock_code}를 찾을 수 없습니다")

        # 2. 이미 존재하는지 확인 (중복 방지)
        existing = await self._check_favorite_exists(user_id, company.company_id)
        if existing:
            raise ValueError("이미 관심종목에 등록되어 있습니다")

        # 3. 관심종목 추가
        favorite = UserFavoriteStock(
            user_id=user_id,
            company_id=company.company_id,
            stock_code=company.stock_code,
            stock_name=company.stock_name
        )

        self.db.add(favorite)
        try:
            await self.db.commit()
            await self.db.refresh(favorite)
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("이미 관심종목에 등록되어 있습니다")

    async def remove_favorite(self, user_id: UUID, stock_code: str) -> Dict[str, str]:
        """
        관심종목 삭제

        Args:
            user_id: 사용자 ID
            stock_code: 종목 코드

        Returns:
            삭제 결과 메시지
        """
        # 회사 정보 조회
        company = await self._get_company_by_code(stock_code)
        if not company:
            raise ValueError(f"종목 코드 {stock_code}를 찾을 수 없습니다")

        # 삭제
        stmt = delete(UserFavoriteStock).where(
            and_(
                UserFavoriteStock.user_id == user_id,
                UserFavoriteStock.company_id == company.company_id
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        if result.rowcount == 0:
            raise ValueError("관심종목에 등록되어 있지 않습니다")

        return {"message": "관심종목이 삭제되었습니다"}

    async def get_favorites(self, user_id: UUID) -> Dict[str, Any]:
        """
        사용자의 관심종목 리스트 조회

        Args:
            user_id: 사용자 ID

        Returns:
            관심종목 리스트
        """
        # 최신 거래일 찾기
        latest_trade_date = await self._get_latest_trade_date()
        logger.info(f"🔍 [get_favorites] Latest trade date: {latest_trade_date}")
        
        if not latest_trade_date:
            return {"items": [], "total": 0}

        # 전일 거래일 찾기
        from sqlalchemy import select as sql_select
        prev_trade_date_query = (
            sql_select(StockPrice.trade_date)
            .where(StockPrice.trade_date < latest_trade_date)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        prev_date_result = await self.db.execute(prev_trade_date_query)
        prev_trade_date = prev_date_result.scalar_one_or_none()
        logger.info(f"🔍 [get_favorites] Previous trade date: {prev_trade_date}")

        # 전일 주가 서브쿼리 (별칭: prev)
        PrevStockPrice = StockPrice.__table__.alias("prev_stock_price")

        # 관심종목 조회 (현재가 + 전일 종가)
        query = (
            select(
                UserFavoriteStock.stock_code,
                UserFavoriteStock.stock_name,
                UserFavoriteStock.company_id,
                Company.industry,
                UserFavoriteStock.created_at,
                StockPrice.close_price,
                StockPrice.change_vs_1d,
                StockPrice.fluctuation_rate,
                StockPrice.volume,
                StockPrice.trading_value,
                StockPrice.market_cap,
                PrevStockPrice.c.close_price.label("prev_close_price")
            )
            .join(Company, Company.company_id == UserFavoriteStock.company_id)
            .outerjoin(
                StockPrice,
                and_(
                    UserFavoriteStock.company_id == StockPrice.company_id,
                    StockPrice.trade_date == latest_trade_date
                )
            )
            .outerjoin(
                PrevStockPrice,
                and_(
                    PrevStockPrice.c.company_id == UserFavoriteStock.company_id,
                    PrevStockPrice.c.trade_date == prev_trade_date
                )
            )
            .where(UserFavoriteStock.user_id == user_id)
            .order_by(desc(UserFavoriteStock.favorite_id))
        )

        result = await self.db.execute(query)
        rows = result.all()
        logger.info(f"🔍 [get_favorites] Found {len(rows)} favorite stocks")

        items = []
        for row in rows:
            # 등락률 계산
            fluctuation_rate = row.fluctuation_rate
            close_price = row.close_price
            change_vs_1d = row.change_vs_1d
            prev_close_price = row.prev_close_price
            
            logger.info(f"🔍 [get_favorites] {row.stock_name} ({row.stock_code}): rate={fluctuation_rate}, price={close_price}, change={change_vs_1d}, prev={prev_close_price}")

            # DB에 등락률이 없으면 전일 종가로 계산
            if fluctuation_rate is None and close_price and prev_close_price and prev_close_price != 0:
                fluctuation_rate = ((close_price - prev_close_price) / prev_close_price) * 100
                logger.info(f"✅ [get_favorites] Calculated rate for {row.stock_name}: {fluctuation_rate:.2f}%")
                # 등락금액도 계산
                if change_vs_1d is None:
                    change_vs_1d = close_price - prev_close_price

            items.append({
                "stock_code": row.stock_code,
                "stock_name": row.stock_name,
                "theme": row.industry,
                "current_price": close_price,
                "change_rate": fluctuation_rate,
                "previous_close": prev_close_price,
                "volume": row.volume,
                "trading_value": row.trading_value,
                "market_cap": row.market_cap,
                "created_at": row.created_at
            })

        return {"items": items, "total": len(items)}

    async def check_favorite(self, user_id: UUID, stock_code: str) -> bool:
        """
        특정 종목이 관심종목인지 확인

        Args:
            user_id: 사용자 ID
            stock_code: 종목 코드

        Returns:
            관심종목 여부
        """
        company = await self._get_company_by_code(stock_code)
        if not company:
            return False

        return await self._check_favorite_exists(user_id, company.company_id)

    # ==================== 최근 본 주식 ====================

    async def add_recent_view(self, user_id: UUID, stock_code: str) -> None:
        """
        최근 본 주식 기록 (UPSERT)

        Args:
            user_id: 사용자 ID
            stock_code: 종목 코드
        """
        # 회사 정보 조회
        company = await self._get_company_by_code(stock_code)
        if not company:
            logger.warning(f"종목 코드 {stock_code}를 찾을 수 없습니다")
            return

        # 기존 기록 확인
        existing_query = select(UserRecentStock).where(
            and_(
                UserRecentStock.user_id == user_id,
                UserRecentStock.company_id == company.company_id
            )
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()

        if existing:
            # 이미 있으면 viewed_at 업데이트 (onupdate로 자동 업데이트)
            existing.viewed_at = datetime.now()
        else:
            # 없으면 새로 추가
            recent = UserRecentStock(
                user_id=user_id,
                company_id=company.company_id,
                stock_code=company.stock_code,
                stock_name=company.stock_name
            )
            self.db.add(recent)

        try:
            await self.db.commit()

            # 10개 초과 시 가장 오래된 항목 삭제
            await self._enforce_recent_view_limit(user_id, limit=10)
        except IntegrityError:
            await self.db.rollback()
            logger.warning(f"최근 본 주식 기록 실패: {stock_code}")

    async def get_recent_views(self, user_id: UUID, limit: int = 10) -> Dict[str, Any]:
        """
        사용자의 최근 본 주식 리스트 조회

        Args:
            user_id: 사용자 ID
            limit: 최대 개수

        Returns:
            최근 본 주식 리스트
        """
        # 최신 거래일 찾기
        latest_trade_date = await self._get_latest_trade_date()

        price_columns = []
        join_condition = None
        if latest_trade_date:
            price_columns = [
                StockPrice.close_price,
                StockPrice.change_vs_1d,
                StockPrice.fluctuation_rate,
                StockPrice.volume,
                StockPrice.trading_value,
                StockPrice.market_cap
            ]
            join_condition = and_(
                UserRecentStock.company_id == StockPrice.company_id,
                StockPrice.trade_date == latest_trade_date
            )

        query = (
            select(
                UserRecentStock.stock_code,
                UserRecentStock.stock_name,
                UserRecentStock.viewed_at,
                *price_columns
            )
            .where(UserRecentStock.user_id == user_id)
            .order_by(desc(UserRecentStock.viewed_at))
            .limit(limit)
        )

        if join_condition is not None:
            query = query.outerjoin(StockPrice, join_condition)

        result = await self.db.execute(query)
        rows = result.all()

        items = [
            {
                "stock_code": row.stock_code,
                "stock_name": row.stock_name,
                "current_price": getattr(row, "close_price", None),
                "change_rate": getattr(row, "fluctuation_rate", None),
                "previous_close": self._calculate_previous_close_value(
                    getattr(row, "close_price", None),
                    getattr(row, "change_vs_1d", None)
                ),
                "volume": getattr(row, "volume", None),
                "trading_value": getattr(row, "trading_value", None),
                "market_cap": getattr(row, "market_cap", None),
                "viewed_at": row.viewed_at
            }
            for row in rows
        ]

        return {"items": items, "total": len(items)}

    async def remove_recent_view(self, user_id: UUID, stock_code: str) -> None:
        """
        최근 본 주식 수동 삭제

        Args:
            user_id: 사용자 ID
            stock_code: 종목 코드
        """
        # 회사 정보 조회
        company = await self._get_company_by_code(stock_code)
        if not company:
            raise ValueError(f"종목 코드 {stock_code}를 찾을 수 없습니다")

        # 삭제
        stmt = delete(UserRecentStock).where(
            and_(
                UserRecentStock.user_id == user_id,
                UserRecentStock.company_id == company.company_id
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        if result.rowcount == 0:
            raise ValueError("최근 본 종목에 없습니다")

    # ==================== Private Methods ====================

    async def _get_company_by_code(self, stock_code: str) -> Optional[Company]:
        """종목 코드로 회사 정보 조회"""
        query = select(Company).where(Company.stock_code == stock_code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _check_favorite_exists(self, user_id: UUID, company_id: int) -> bool:
        """관심종목 존재 여부 확인"""
        query = select(UserFavoriteStock).where(
            and_(
                UserFavoriteStock.user_id == user_id,
                UserFavoriteStock.company_id == company_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _get_latest_trade_date(self) -> Optional[datetime.date]:
        """최신 거래일 조회"""
        query = (
            select(StockPrice.trade_date)
            .order_by(desc(StockPrice.trade_date))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _enforce_recent_view_limit(self, user_id: UUID, limit: int = 10) -> None:
        """
        최근 본 주식 개수 제한 (10개 초과 시 가장 오래된 항목 삭제)

        Args:
            user_id: 사용자 ID
            limit: 최대 개수 (기본 10개)
        """
        # 현재 개수 확인
        count_query = select(UserRecentStock).where(UserRecentStock.user_id == user_id)
        count_result = await self.db.execute(count_query)
        count = len(count_result.all())

        if count > limit:
            # 가장 오래된 항목들 조회 (개수 초과분만큼)
            delete_count = count - limit
            old_items_query = (
                select(UserRecentStock.recent_id)
                .where(UserRecentStock.user_id == user_id)
                .order_by(UserRecentStock.viewed_at)  # 오래된 순
                .limit(delete_count)
            )
            old_items_result = await self.db.execute(old_items_query)
            old_item_ids = [row.recent_id for row in old_items_result.all()]

            # 오래된 항목 삭제
            if old_item_ids:
                delete_stmt = delete(UserRecentStock).where(
                    UserRecentStock.recent_id.in_(old_item_ids)
                )
                await self.db.execute(delete_stmt)
                await self.db.commit()

    @staticmethod
    def _calculate_previous_close_value(
        close_price: Optional[int],
        change_vs_1d: Optional[int]
    ) -> Optional[int]:
        """전일 종가 계산"""
        if close_price is None or change_vs_1d is None:
            return None
        return close_price - change_vs_1d
