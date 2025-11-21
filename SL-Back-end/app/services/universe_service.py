"""
유니버스(종목 그룹) 분류 서비스
- 시가총액 기준으로 종목을 유니버스별로 분류
- 코스피: 초대형주, 대형주, 중형주, 소형주
- 코스닥: 초대형주, 대형주, 중형주, 소형주
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.stock_universe_history import StockUniverseHistory

logger = logging.getLogger(__name__)


class UniverseService:
    """유니버스 분류 및 조회 서비스"""

    # 유니버스 정의
    UNIVERSES = {
        "KOSPI": {
            "KOSPI_MEGA": {"name": "코스피 초대형", "min_cap": 10_000_000_000_000, "max_cap": None},  # 10조 이상
            "KOSPI_LARGE": {"name": "코스피 대형", "min_cap": 2_000_000_000_000, "max_cap": 10_000_000_000_000},  # 2조 ~ 10조
            "KOSPI_MID": {"name": "코스피 중형", "min_cap": 500_000_000_000, "max_cap": 2_000_000_000_000},  # 5천억 ~ 2조
            "KOSPI_SMALL": {"name": "코스피 소형", "min_cap": 0, "max_cap": 500_000_000_000},  # 5천억 이하
        },
        "KOSDAQ": {
            "KOSDAQ_MEGA": {"name": "코스닥 초대형", "min_cap": 2_000_000_000_000, "max_cap": None},  # 2조 이상
            "KOSDAQ_LARGE": {"name": "코스닥 대형", "min_cap": 500_000_000_000, "max_cap": 2_000_000_000_000},  # 5천억 ~ 2조
            "KOSDAQ_MID": {"name": "코스닥 중형", "min_cap": 200_000_000_000, "max_cap": 500_000_000_000},  # 2천억 ~ 5천억
            "KOSDAQ_SMALL": {"name": "코스닥 소형", "min_cap": 0, "max_cap": 200_000_000_000},  # 2천억 이하
        }
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_trading_date(self) -> Optional[str]:
        """
        가장 최근 거래일 조회 (완전한 데이터가 있는 날짜)

        Note: 단순히 가장 최근 날짜가 아니라, 충분한 종목 데이터(2000개 이상)가 있는
        가장 최근 날짜를 반환합니다. 이는 불완전한 데이터로 인한 오류를 방지합니다.

        Returns:
            최근 거래일 (YYYYMMDD) 또는 None
        """
        try:
            # 시가총액 데이터가 있는 종목이 2000개 이상인 가장 최근 날짜 조회
            stmt = (
                select(StockPrice.trade_date)
                .where(
                    and_(
                        StockPrice.market_cap.isnot(None),
                        StockPrice.market_cap > 0
                    )
                )
                .group_by(StockPrice.trade_date)
                .having(func.count() >= 2000)
                .order_by(desc(StockPrice.trade_date))
                .limit(1)
            )
            result = await self.db.execute(stmt)
            latest_date = result.scalar_one_or_none()

            if latest_date:
                logger.debug(f"완전한 데이터가 있는 최근 거래일: {latest_date}")
            else:
                logger.warning("2000개 이상의 종목 데이터가 있는 거래일을 찾을 수 없습니다.")

            return latest_date
        except Exception as e:
            logger.error(f"최근 거래일 조회 실패: {e}")
            return None

    async def get_universes_summary(self) -> Dict[str, Any]:
        """
        모든 유니버스의 종목 수 요약 정보 조회

        Returns:
            {
                "trade_date": "20240101",
                "universes": [
                    {
                        "id": "KOSPI_MEGA",
                        "name": "코스피 초대형",
                        "market": "KOSPI",
                        "stock_count": 50,
                        "min_cap": 10000000000000,
                        "max_cap": null
                    },
                    ...
                ]
            }
        """
        try:
            # 최근 거래일 조회
            latest_date = await self.get_latest_trading_date()
            if not latest_date:
                logger.warning("거래일 데이터가 없습니다.")
                return {"trade_date": None, "universes": []}

            universes_info = []

            # 각 유니버스별 종목 수 계산
            for market_type, universes in self.UNIVERSES.items():
                for universe_id, universe_config in universes.items():
                    stock_count = await self._count_stocks_in_universe(
                        latest_date,
                        universe_id
                    )

                    universes_info.append({
                        "id": universe_id,
                        "name": universe_config["name"],
                        "market": market_type,
                        "stock_count": stock_count,
                        "min_cap": universe_config["min_cap"],
                        "max_cap": universe_config["max_cap"]
                    })

            return {
                "trade_date": latest_date.strftime("%Y%m%d") if latest_date else None,
                "universes": universes_info
            }

        except Exception as e:
            logger.error(f"유니버스 요약 정보 조회 실패: {e}", exc_info=True)
            return {"trade_date": None, "universes": []}

    async def _count_stocks_in_universe(
        self,
        trade_date: str,
        universe_id: str
    ) -> int:
        """
        특정 유니버스의 종목 수 계산 (히스토리 테이블 우선, 동적 계산 폴백)

        Args:
            trade_date: 기준 거래일
            universe_id: 유니버스 ID (예: KOSPI_MEGA, KOSDAQ_SMALL)

        Returns:
            종목 수
        """
        try:
            # 1차: 히스토리 테이블에서 조회
            stmt_history = (
                select(func.count(StockUniverseHistory.stock_code))
                .where(
                    and_(
                        StockUniverseHistory.trade_date == trade_date,
                        StockUniverseHistory.universe_id == universe_id
                    )
                )
            )
            result = await self.db.execute(stmt_history)
            count = result.scalar_one_or_none() or 0

            if count > 0:
                logger.debug(f"✅ 히스토리 테이블에서 {universe_id} 종목 수 조회: {count}개")
                return count

            # 2차: 히스토리에 없으면 동적 계산으로 폴백
            logger.info(f"히스토리 테이블에 데이터 없음. 동적 계산 시도: {universe_id}, {trade_date}")

            # 유니버스 설정 찾기
            universe_config = None
            market_type = None

            for market, universes in self.UNIVERSES.items():
                if universe_id in universes:
                    universe_config = universes[universe_id]
                    market_type = market
                    break

            if not universe_config:
                return 0

            # 조건 설정
            conditions = [
                StockPrice.trade_date == trade_date,
                Company.market_type == market_type,
                StockPrice.market_cap.isnot(None),
                StockPrice.market_cap >= universe_config["min_cap"]
            ]

            if universe_config["max_cap"] is not None:
                conditions.append(StockPrice.market_cap < universe_config["max_cap"])

            # 종목 수 계산
            stmt = (
                select(func.count(Company.stock_code))
                .select_from(Company)
                .join(StockPrice, Company.company_id == StockPrice.company_id)
                .where(and_(*conditions))
            )

            result = await self.db.execute(stmt)
            count = result.scalar_one_or_none() or 0
            logger.debug(f"🔄 동적 계산 결과: {count}개")
            return count

        except Exception as e:
            logger.error(f"유니버스 종목 수 계산 실패: {e}")
            return 0

    async def get_stocks_in_universe(
        self,
        universe_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        특정 유니버스에 속한 종목 리스트 조회

        Args:
            universe_id: 유니버스 ID (예: "KOSPI_MEGA")
            limit: 최대 조회 종목 수 (None이면 전체)

        Returns:
            종목 리스트 [{"stock_code": "005930", "stock_name": "삼성전자", "market_cap": 500000000000000}, ...]
        """
        try:
            # 유니버스 설정 찾기
            universe_config = None
            market_type = None

            for market, universes in self.UNIVERSES.items():
                if universe_id in universes:
                    universe_config = universes[universe_id]
                    market_type = market
                    break

            if not universe_config:
                logger.warning(f"유효하지 않은 유니버스 ID: {universe_id}")
                return []

            # 최근 거래일 조회
            latest_date = await self.get_latest_trading_date()
            if not latest_date:
                return []

            # 조건 설정
            conditions = [
                StockPrice.trade_date == latest_date,
                Company.market_type == market_type,
                StockPrice.market_cap.isnot(None),
                StockPrice.market_cap >= universe_config["min_cap"]
            ]

            if universe_config["max_cap"] is not None:
                conditions.append(StockPrice.market_cap < universe_config["max_cap"])

            # 쿼리 실행
            stmt = (
                select(
                    Company.stock_code,
                    Company.stock_name,
                    StockPrice.market_cap
                )
                .select_from(Company)
                .join(StockPrice, Company.company_id == StockPrice.company_id)
                .where(and_(*conditions))
                .order_by(desc(StockPrice.market_cap))
            )

            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            rows = result.all()

            stocks = [
                {
                    "stock_code": row.stock_code,
                    "stock_name": row.stock_name,
                    "market_cap": int(row.market_cap) if row.market_cap else 0
                }
                for row in rows
            ]

            return stocks

        except Exception as e:
            logger.error(f"유니버스 종목 리스트 조회 실패: {e}", exc_info=True)
            return []

    async def get_stock_codes_by_universes(
        self,
        universe_ids: List[str],
        trade_date: Optional[str] = None
    ) -> List[str]:
        """
        여러 유니버스에 속한 종목 코드 리스트 조회 (백테스트용)

        Args:
            universe_ids: 유니버스 ID 리스트 (예: ["KOSPI_MEGA", "KOSDAQ_LARGE"])
            trade_date: 기준 거래일 (None이면 최근 거래일 사용)

        Returns:
            종목 코드 리스트 ["005930", "000660", ...]
        """
        try:
            if not universe_ids:
                return []

            # 거래일 설정
            if not trade_date:
                trade_date = await self.get_latest_trading_date()
                if not trade_date:
                    return []

            # 먼저 히스토리 테이블에서 시도
            stock_codes = await self._get_stock_codes_from_history(universe_ids, trade_date)

            # 히스토리 테이블에 데이터가 없으면 동적 계산으로 폴백
            if not stock_codes:
                logger.info(f"히스토리 테이블에 데이터 없음. 동적 계산으로 폴백: {trade_date}")
                stock_codes = await self._get_stock_codes_dynamic(universe_ids, trade_date)

            return stock_codes

        except Exception as e:
            logger.error(f"유니버스별 종목 코드 조회 실패: {e}", exc_info=True)
            return []

    async def _get_stock_codes_from_history(
        self,
        universe_ids: List[str],
        trade_date: str
    ) -> List[str]:
        """
        히스토리 테이블에서 종목 코드 조회

        Args:
            universe_ids: 유니버스 ID 리스트
            trade_date: 기준 거래일 (YYYYMMDD 문자열 또는 date 객체)

        Returns:
            종목 코드 리스트
        """
        try:
            # 문자열을 date 객체로 변환 (YYYYMMDD -> date)
            if isinstance(trade_date, str):
                if len(trade_date) == 8:  # YYYYMMDD
                    from datetime import datetime
                    trade_date = datetime.strptime(trade_date, '%Y%m%d').date()
                # 이미 datetime이면 date로 변환
                elif hasattr(trade_date, 'date'):
                    trade_date = trade_date.date()

            stmt = (
                select(StockUniverseHistory.stock_code)
                .where(
                    and_(
                        StockUniverseHistory.universe_id.in_(universe_ids),
                        StockUniverseHistory.trade_date == trade_date
                    )
                )
                .distinct()
            )

            result = await self.db.execute(stmt)
            stock_codes = [row.stock_code for row in result.all()]

            logger.info(f"✅ 히스토리 테이블에서 {len(stock_codes)}개 종목 조회 (날짜: {trade_date})")
            return stock_codes

        except Exception as e:
            logger.warning(f"히스토리 테이블 조회 실패 (폴백 예정): {e}")
            return []

    async def _get_stock_codes_dynamic(
        self,
        universe_ids: List[str],
        trade_date: str
    ) -> List[str]:
        """
        동적 계산으로 종목 코드 조회 (폴백용)

        Args:
            universe_ids: 유니버스 ID 리스트
            trade_date: 기준 거래일

        Returns:
            종목 코드 리스트
        """
        all_stock_codes = set()

        # 각 유니버스별로 종목 코드 수집
        for universe_id in universe_ids:
            universe_config = None
            market_type = None

            for market, universes in self.UNIVERSES.items():
                if universe_id in universes:
                    universe_config = universes[universe_id]
                    market_type = market
                    break

            if not universe_config:
                logger.warning(f"유효하지 않은 유니버스 ID: {universe_id}")
                continue

            # 조건 설정
            conditions = [
                StockPrice.trade_date == trade_date,
                Company.market_type == market_type,
                StockPrice.market_cap.isnot(None),
                StockPrice.market_cap >= universe_config["min_cap"]
            ]

            if universe_config["max_cap"] is not None:
                conditions.append(StockPrice.market_cap < universe_config["max_cap"])

            # 쿼리 실행
            stmt = (
                select(Company.stock_code)
                .select_from(Company)
                .join(StockPrice, Company.company_id == StockPrice.company_id)
                .where(and_(*conditions))
            )

            result = await self.db.execute(stmt)
            stock_codes = [row.stock_code for row in result.all()]
            all_stock_codes.update(stock_codes)

        logger.info(f"🔄 동적 계산으로 {len(all_stock_codes)}개 종목 조회")
        return list(all_stock_codes)
