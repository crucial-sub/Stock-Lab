"""
전략 수익률 랭킹 서비스
Redis Sorted Set + DB Hybrid 방식

구조:
- Redis Sorted Set: 실시간 랭킹 (O(1) 조회)
- DB: 백업 및 복구용
- 자동 동기화: 세션 완료 시 자동 업데이트
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.simulation import (
    PortfolioStrategy, SimulationSession, SimulationStatistics
)
from app.models.user import User

logger = logging.getLogger(__name__)


class RankingService:
    """Redis Sorted Set 기반 랭킹 관리 서비스"""

    # Redis Key 상수
    RANKING_ALL = "rankings:all"  # 전체 랭킹
    RANKING_DAILY = "rankings:daily"  # 일별 랭킹
    RANKING_WEEKLY = "rankings:weekly"  # 주별 랭킹
    RANKING_MONTHLY = "rankings:monthly"  # 월별 랭킹

    # TTL 설정 (초)
    TTL_DAILY = 86400  # 1일
    TTL_WEEKLY = 604800  # 7일
    TTL_MONTHLY = 2592000  # 30일

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Args:
            redis_client: Redis 클라이언트 (None이면 기능 비활성화)
        """
        self.redis = redis_client
        self.enabled = redis_client is not None

    async def add_to_ranking(
        self,
        session_id: str,
        total_return: float,
        strategy_id: str,
        is_public: bool = True
    ) -> bool:
        """
        랭킹에 세션 추가

        Args:
            session_id: 세션 ID
            total_return: 총 수익률
            strategy_id: 전략 ID
            is_public: 공개 여부

        Returns:
            성공 여부
        """
        if not self.enabled or not is_public:
            return False

        try:
            # Sorted Set에 추가 (score = total_return)
            await self.redis.zadd(
                self.RANKING_ALL,
                {session_id: float(total_return)}
            )

            # 메타데이터 저장 (해시)
            metadata_key = f"ranking:meta:{session_id}"
            await self.redis.hset(
                metadata_key,
                mapping={
                    "session_id": session_id,
                    "strategy_id": strategy_id,
                    "total_return": str(total_return),
                    "updated_at": datetime.now().isoformat()
                }
            )

            # 시간별 랭킹에도 추가
            await self._add_to_time_based_rankings(session_id, total_return)

            # TOP 100만 유지 (메모리 절약)
            await self.redis.zremrangebyrank(self.RANKING_ALL, 0, -101)

            logger.info(f"랭킹 추가 성공: session={session_id}, return={total_return}%")
            return True

        except Exception as e:
            logger.error(f"랭킹 추가 실패: {e}", exc_info=True)
            return False

    async def _add_to_time_based_rankings(
        self,
        session_id: str,
        total_return: float
    ):
        """시간 기반 랭킹에 추가"""
        try:
            # 일별 랭킹
            await self.redis.zadd(self.RANKING_DAILY, {session_id: float(total_return)})
            await self.redis.expire(self.RANKING_DAILY, self.TTL_DAILY)

            # 주별 랭킹
            await self.redis.zadd(self.RANKING_WEEKLY, {session_id: float(total_return)})
            await self.redis.expire(self.RANKING_WEEKLY, self.TTL_WEEKLY)

            # 월별 랭킹
            await self.redis.zadd(self.RANKING_MONTHLY, {session_id: float(total_return)})
            await self.redis.expire(self.RANKING_MONTHLY, self.TTL_MONTHLY)

        except Exception as e:
            logger.warning(f"시간 기반 랭킹 추가 실패: {e}")

    async def get_top_rankings(
        self,
        limit: int = 3,
        ranking_type: str = "all"
    ) -> List[str]:
        """
        TOP N 세션 ID 조회 (Redis)

        Args:
            limit: 조회할 개수
            ranking_type: 랭킹 타입 (all/daily/weekly/monthly)

        Returns:
            세션 ID 리스트 (수익률 높은 순)
        """
        if not self.enabled:
            return []

        try:
            # 랭킹 타입별 키 선택
            key_map = {
                "all": self.RANKING_ALL,
                "daily": self.RANKING_DAILY,
                "weekly": self.RANKING_WEEKLY,
                "monthly": self.RANKING_MONTHLY
            }
            key = key_map.get(ranking_type, self.RANKING_ALL)

            # ZREVRANGE: 높은 점수부터 (O(log N + M))
            session_ids = await self.redis.zrevrange(key, 0, limit - 1)

            # bytes -> str 변환
            return [sid.decode('utf-8') if isinstance(sid, bytes) else sid
                    for sid in session_ids]

        except Exception as e:
            logger.error(f"TOP 랭킹 조회 실패: {e}", exc_info=True)
            return []

    async def get_ranking_with_scores(
        self,
        limit: int = 3,
        ranking_type: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        TOP N 랭킹 (점수 포함)

        Returns:
            [{"session_id": "xxx", "total_return": 123.45}, ...]
        """
        if not self.enabled:
            return []

        try:
            key_map = {
                "all": self.RANKING_ALL,
                "daily": self.RANKING_DAILY,
                "weekly": self.RANKING_WEEKLY,
                "monthly": self.RANKING_MONTHLY
            }
            key = key_map.get(ranking_type, self.RANKING_ALL)

            # ZREVRANGE with WITHSCORES
            results = await self.redis.zrevrange(
                key, 0, limit - 1, withscores=True
            )

            rankings = []
            for session_id, score in results:
                sid = session_id.decode('utf-8') if isinstance(session_id, bytes) else session_id
                rankings.append({
                    "session_id": sid,
                    "total_return": float(score)
                })

            return rankings

        except Exception as e:
            logger.error(f"랭킹 조회 실패: {e}", exc_info=True)
            return []

    async def remove_from_ranking(self, session_id: str) -> bool:
        """
        랭킹에서 세션 제거 (전략 삭제 시)

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        if not self.enabled:
            return False

        try:
            # 모든 랭킹에서 제거
            await self.redis.zrem(self.RANKING_ALL, session_id)
            await self.redis.zrem(self.RANKING_DAILY, session_id)
            await self.redis.zrem(self.RANKING_WEEKLY, session_id)
            await self.redis.zrem(self.RANKING_MONTHLY, session_id)

            # 메타데이터 삭제
            await self.redis.delete(f"ranking:meta:{session_id}")

            logger.info(f"랭킹 제거 성공: session={session_id}")
            return True

        except Exception as e:
            logger.error(f"랭킹 제거 실패: {e}", exc_info=True)
            return False

    async def rebuild_from_db(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> int:
        """
        DB에서 랭킹 재구축 (Redis 장애 복구용)

        Args:
            db: DB 세션
            limit: 재구축할 개수

        Returns:
            재구축된 항목 수
        """
        if not self.enabled:
            return 0

        try:
            logger.info("DB에서 랭킹 재구축 시작...")

            # 기존 랭킹 삭제
            await self.redis.delete(self.RANKING_ALL)

            # DB에서 TOP N 조회
            query = (
                select(
                    SimulationSession.session_id,
                    SimulationStatistics.total_return,
                    PortfolioStrategy.strategy_id,
                    PortfolioStrategy.is_public
                )
                .join(
                    SimulationStatistics,
                    SimulationStatistics.session_id == SimulationSession.session_id
                )
                .join(
                    PortfolioStrategy,
                    PortfolioStrategy.strategy_id == SimulationSession.strategy_id
                )
                .where(
                    and_(
                        PortfolioStrategy.is_public == True,
                        SimulationSession.status == "COMPLETED",
                        SimulationStatistics.total_return.isnot(None)
                    )
                )
                .order_by(desc(SimulationStatistics.total_return))
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.all()

            # Redis에 일괄 추가
            count = 0
            for session_id, total_return, strategy_id, is_public in rows:
                if total_return is not None:
                    await self.add_to_ranking(
                        session_id=session_id,
                        total_return=float(total_return),
                        strategy_id=strategy_id,
                        is_public=is_public
                    )
                    count += 1

            logger.info(f"랭킹 재구축 완료: {count}개 항목")
            return count

        except Exception as e:
            logger.error(f"랭킹 재구축 실패: {e}", exc_info=True)
            return 0

    async def get_user_rank(
        self,
        session_id: str,
        ranking_type: str = "all"
    ) -> Optional[int]:
        """
        특정 세션의 순위 조회

        Returns:
            순위 (1-based), 없으면 None
        """
        if not self.enabled:
            return None

        try:
            key_map = {
                "all": self.RANKING_ALL,
                "daily": self.RANKING_DAILY,
                "weekly": self.RANKING_WEEKLY,
                "monthly": self.RANKING_MONTHLY
            }
            key = key_map.get(ranking_type, self.RANKING_ALL)

            # ZREVRANK: 0-based rank
            rank = await self.redis.zrevrank(key, session_id)

            if rank is not None:
                return rank + 1  # 1-based
            return None

        except Exception as e:
            logger.error(f"순위 조회 실패: {e}", exc_info=True)
            return None


async def get_ranking_service(redis_client: Optional[Redis] = None) -> RankingService:
    """
    랭킹 서비스 팩토리

    Args:
        redis_client: Redis 클라이언트 (None이면 자동 가져오기)

    Returns:
        RankingService 인스턴스
    """
    if redis_client is None:
        try:
            from app.core.cache import get_redis
            redis_client = get_redis()
        except Exception as e:
            logger.warning(f"Redis 연결 실패, 랭킹 기능 비활성화: {e}")

    return RankingService(redis_client)
