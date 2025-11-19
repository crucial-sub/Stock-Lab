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
    """Redis 캐시 관리자 (Multi Event Loop 지원)"""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._loop_clients: Dict[int, redis.Redis] = {}  # Event loop별 클라이언트 저장

    async def initialize(self):
        """Redis 연결 초기화"""
        if not self._pool:
            self._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                # 🚀 PRODUCTION OPTIMIZATION: Connection Pool 확장 (동시 사용자 지원)
                max_connections=100,    # 20 → 100으로 확장 (동시 100명 백테스트 지원)
                socket_keepalive=True,  # TCP keepalive 활성화
                # socket_keepalive_options 제거 (Docker 환경 호환성)
                health_check_interval=30,  # 30초마다 연결 상태 확인
                decode_responses=False,  # Binary 데이터 처리용
                socket_connect_timeout=5,  # 연결 타임아웃 5초
                retry_on_timeout=True  # 타임아웃 시 재시도
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
        # Loop-local 클라이언트도 모두 종료
        for client in self._loop_clients.values():
            await client.close()
        self._loop_clients.clear()

    def _get_loop_client(self) -> Optional[redis.Redis]:
        """현재 event loop에 맞는 Redis 클라이언트 반환"""
        try:
            import asyncio

            # 현재 event loop 가져오기
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                # 실행 중인 루프가 없으면 기본 클라이언트 사용
                return self._client

            loop_id = id(current_loop)

            # 메인 클라이언트의 루프와 같으면 메인 클라이언트 사용
            if self._client:
                try:
                    # 메인 클라이언트가 현재 루프에서 사용 가능한지 확인
                    return self._client
                except Exception:
                    pass

            # 현재 루프용 클라이언트가 이미 있으면 반환
            if loop_id in self._loop_clients:
                return self._loop_clients[loop_id]

            # 새 루프용 클라이언트 생성
            logger.info(f"Creating new Redis client for event loop {loop_id}")
            new_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if hasattr(settings, 'REDIS_PASSWORD') else None,
                decode_responses=False,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            self._loop_clients[loop_id] = new_client
            return new_client

        except Exception as e:
            logger.warning(f"Failed to get loop-specific Redis client: {e}")
            return self._client

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

            client = self._get_loop_client()
            if not client:
                return None

            value = await client.get(key)
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

            client = self._get_loop_client()
            if not client:
                return False

            serialized = pickle.dumps(value)

            # ttl이 None이거나 0이면 만료 시간 없이 저장
            if ttl is None:
                ttl = settings.CACHE_TTL_SECONDS

            if ttl == 0:
                # TTL 없이 영구 저장
                await client.set(key, serialized)
            else:
                # TTL 설정하여 저장
                await client.setex(
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

            client = self._get_loop_client()
            if not client:
                return 0

            # 패턴과 일치하는 모든 키 찾기
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            if not settings.ENABLE_CACHE:
                return False

            client = self._get_loop_client()
            if not client:
                return False

            return await client.exists(key) > 0
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
            client = self._get_loop_client()
            if not client:
                return {"connected": False, "error": "No Redis client available"}

            info = await client.info("stats")
            memory = await client.info("memory")

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


def get_cache() -> RedisCache:
    """
    RedisCache 인스턴스 반환
    데이터 캐싱용
    """
    return cache


def get_redis() -> Optional[redis.Redis]:
    """
    Redis 클라이언트 인스턴스 반환 (Event Loop 안전)
    백테스트 진행률 등 실시간 데이터 저장용
    """
    return cache._get_loop_client()


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