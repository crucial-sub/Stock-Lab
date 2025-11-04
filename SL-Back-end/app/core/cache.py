"""
Redis 캐싱 유틸리티
팩터 계산 결과 및 메타데이터 캐싱
"""
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import pickle
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 캐시 관리자"""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def initialize(self):
        """Redis 연결 초기화"""
        if not self._pool:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                max_connections=20,
                decode_responses=False  # Binary 데이터 처리용
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # 연결 테스트
            try:
                await self._client.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def close(self):
        """Redis 연결 종료"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 파라미터를 정렬하여 일관된 키 생성
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        hash_digest = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{settings.CACHE_PREFIX}:{prefix}:{hash_digest}"

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        try:
            if not settings.ENABLE_CACHE:
                return None

            value = await self._client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """캐시에 값 저장"""
        try:
            if not settings.ENABLE_CACHE:
                return False

            serialized = pickle.dumps(value)
            ttl = ttl or settings.CACHE_TTL_SECONDS

            await self._client.setex(
                key,
                timedelta(seconds=ttl),
                serialized
            )
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, pattern: str) -> int:
        """패턴과 일치하는 키 삭제"""
        try:
            if not settings.ENABLE_CACHE:
                return 0

            # 패턴과 일치하는 모든 키 찾기
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            if not settings.ENABLE_CACHE:
                return False
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {e}")
            return False

    async def get_or_set(
        self,
        key: str,
        func,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        캐시에서 값을 가져오거나, 없으면 함수 실행 후 저장
        """
        # 캐시에서 조회
        cached_value = await self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit for key: {key}")
            return cached_value

        # 캐시 미스 - 함수 실행
        logger.debug(f"Cache miss for key: {key}")
        value = await func(*args, **kwargs)

        # 결과 캐싱
        await self.set(key, value, ttl)
        return value

    async def invalidate_factor(self, factor_id: str, base_date: Optional[str] = None):
        """특정 팩터의 캐시 무효화"""
        if base_date:
            pattern = f"{settings.CACHE_PREFIX}:factor:{factor_id}:{base_date}:*"
        else:
            pattern = f"{settings.CACHE_PREFIX}:factor:{factor_id}:*"

        deleted = await self.delete(pattern)
        logger.info(f"Invalidated {deleted} cache entries for factor {factor_id}")
        return deleted

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        try:
            info = await self._client.info("stats")
            memory = await self._client.info("memory")

            return {
                "connected": True,
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_ratio": (
                    info.get("keyspace_hits", 0) /
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    if info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0) > 0
                    else 0
                ),
                "used_memory_human": memory.get("used_memory_human", "0"),
                "used_memory_peak_human": memory.get("used_memory_peak_human", "0")
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}


# 싱글톤 인스턴스
cache = RedisCache()


# 캐시 데코레이터
def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_params: Optional[list] = None
):
    """
    비동기 함수용 캐시 데코레이터

    Usage:
        @cached(prefix="factor_per", ttl=3600)
        async def calculate_per(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성을 위한 파라미터 추출
            cache_params = {}
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        cache_params[param] = kwargs[param]
            else:
                # 모든 kwargs를 사용
                cache_params = kwargs

            # 캐시 키 생성
            key = cache._generate_key(prefix, cache_params)

            # 캐시에서 조회 또는 실행
            return await cache.get_or_set(
                key=key,
                func=func,
                ttl=ttl,
                *args,
                **kwargs
            )

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator