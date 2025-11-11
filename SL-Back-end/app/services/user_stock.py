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
            return {"message": "이미 관심종목에 등록되어 있습니다", "exists": True}

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
            return {"message": "이미 관심종목에 등록되어 있습니다", "exists": True}

        return {
            "message": "관심종목이 추가되었습니다",
            "stock_code": stock_code,
            "stock_name": company.stock_name,
            "exists": False
        }

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

        # 관심종목 조회 (최신 거래일이 있으면 가격 정보까지 포함)
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
                UserFavoriteStock.company_id == StockPrice.company_id,
                StockPrice.trade_date == latest_trade_date
            )

        query = select(
            UserFavoriteStock.stock_code,
            UserFavoriteStock.stock_name,
            UserFavoriteStock.created_at,
            *price_columns
        ).where(UserFavoriteStock.user_id == user_id).order_by(desc(UserFavoriteStock.created_at))

        if join_condition:
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
                "created_at": row.created_at
            }
            for row in rows
        ]

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

        if join_condition:
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

    @staticmethod
    def _calculate_previous_close_value(
        close_price: Optional[int],
        change_vs_1d: Optional[int]
    ) -> Optional[int]:
        """전일 종가 계산"""
        if close_price is None or change_vs_1d is None:
            return None
        return close_price - change_vs_1d
