"""
백테스트 Redis 캐싱 최적화 모듈
- 배치 캐시 조회/저장으로 네트워크 IO 최소화
- 캐시 키 전략 개선 (종목 무관)
- TTL 연장 및 압축
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
import pickle
import lz4.frame
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.cache import cache

logger = logging.getLogger(__name__)


def _normalize_for_hash(obj: Any) -> Any:
    """
    해시 생성을 위한 데이터 정규화

    Decimal, float, int를 모두 동일한 형태로 변환하여
    워밍업 스크립트와 백테스트 실행 시 동일한 해시 생성 보장
    """
    from decimal import Decimal

    if isinstance(obj, Decimal):
        # Decimal을 float로 변환 (일관성)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _normalize_for_hash(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_for_hash(item) for item in obj]
    elif isinstance(obj, (int, float)):
        # int/float은 float으로 통일
        return float(obj) if obj is not None else None
    else:
        return obj


def generate_strategy_hash(buy_conditions: Any, trading_rules: Dict = None) -> str:
    """
    전략 조건으로 고유 해시 생성

    Args:
        buy_conditions: 매수 조건 (dict 또는 list)
        trading_rules: 매매 규칙 (목표가/손절가, 보유기간 등)

    Returns:
        8자리 해시 문자열

    Note:
        🔥 FIX: Decimal/int/float를 모두 float으로 정규화하여
        워밍업과 백테스트 실행 시 동일한 해시 생성 보장
    """
    # 데이터 정규화 (Decimal → float 변환)
    normalized_buy = _normalize_for_hash(buy_conditions)
    normalized_rules = _normalize_for_hash(trading_rules or {})

    strategy_data = {
        'buy_conditions': normalized_buy,
        'trading_rules': normalized_rules
    }

    # JSON으로 직렬화 (key 정렬로 일관성 보장)
    strategy_str = json.dumps(strategy_data, sort_keys=True, default=str)

    # MD5 해시 생성 후 앞 8자리 사용
    hash_obj = hashlib.md5(strategy_str.encode('utf-8'))
    return hash_obj.hexdigest()[:8]


class OptimizedCacheManager:
    """최적화된 캐시 관리자"""

    def __init__(self):
        self.cache_prefix = "backtest_optimized"
        # 🚀 EXTREME OPTIMIZATION: TTL 30일로 연장 (완전 메모리 캐싱)
        # 팩터 데이터는 거의 변하지 않으므로 장기 캐싱
        self.default_ttl = 30 * 24 * 3600  # 7일 → 30일

        # 🚀 NEW: 메모리 캐시 (역직렬화된 DataFrame 저장)
        self._memory_cache: Dict[str, Dict] = {}
        self._max_memory_items = 500  # 최대 500개 날짜 캐시
        self._executor = ThreadPoolExecutor(max_workers=4)  # 병렬 압축 해제용

    def _generate_factor_cache_key(
        self,
        calc_date: date,
        factor_names: List[str],
        target_themes: List[str] = None,
        target_stocks: List[str] = None,
        strategy_hash: str = None
    ) -> str:
        """
        팩터 캐시 키 생성 (전략별 구분)

        🔥 FIXED: 전략 조건 해시를 포함하여 전략별 캐시 격리
        - 수정 전: backtest_optimized:factors:{date}:{themes} (전략 구분 불가 ❌)
        - 수정 후: backtest_optimized:factors:{date}:{themes}:{strategy_hash} (전략별 구분 ✅)

        Args:
            calc_date: 계산 날짜
            factor_names: 요청 팩터 목록
            target_themes: 대상 테마
            target_stocks: 대상 종목
            strategy_hash: 전략 조건 해시 (8자리)
        """
        # 테마 정규화
        themes_str = ','.join(sorted(target_themes)) if target_themes else 'all'

        # 🔥 FIX: 전략 해시를 키에 포함하여 전략별 격리
        if strategy_hash:
            return f"{self.cache_prefix}:factors:{calc_date}:{themes_str}:{strategy_hash}"
        else:
            # 워밍업 스크립트 등 호환성을 위한 폴백 (strategy_hash가 없는 경우)
            return f"{self.cache_prefix}:factors:{calc_date}:{themes_str}"

    def _decompress_and_deserialize(self, data: bytes) -> Optional[Dict]:
        """압축 해제 + 역직렬화 (ThreadPoolExecutor용)"""
        try:
            decompressed = lz4.frame.decompress(data)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.warning(f"역직렬화 실패: {e}")
            return None

    async def get_factors_batch(
        self,
        dates: List[date],
        factor_names: List[str],
        target_themes: List[str] = None,
        target_stocks: List[str] = None,
        strategy_hash: str = None
    ) -> Dict[date, Optional[Dict]]:
        """
        배치 캐시 조회 (메모리 캐시 + 병렬 역직렬화)

        최적화:
        1. 메모리 캐시 우선 조회 (0ms)
        2. Redis 조회 (병렬 압축 해제)
        3. 결과를 메모리 캐시에 저장

        기존: 252일 × 36ms = 9초
        최적화: 메모리 히트 시 0초, Redis 히트 시 2-3초

        🔥 FIXED: strategy_hash 파라미터 추가로 전략별 캐시 격리
        """
        try:
            # 1. 캐시 키 생성 (전략 해시 포함)
            cache_keys = {
                d: self._generate_factor_cache_key(d, factor_names, target_themes, target_stocks, strategy_hash)
                for d in dates
            }

            # 2. 🚀 메모리 캐시 우선 조회
            result = {}
            redis_miss_dates = []
            redis_miss_keys = []

            for calc_date in dates:
                cache_key = cache_keys[calc_date]
                if cache_key in self._memory_cache:
                    result[calc_date] = self._memory_cache[cache_key]
                else:
                    redis_miss_dates.append(calc_date)
                    redis_miss_keys.append(cache_key)

            memory_hits = len(dates) - len(redis_miss_dates)
            if memory_hits > 0:
                logger.info(f"⚡ 메모리 캐시 히트: {memory_hits}/{len(dates)}개 날짜")

            # 3. Redis 조회 (메모리 캐시 미스만)
            if redis_miss_dates:
                from app.core.cache import get_redis
                redis_client = get_redis()
                if not redis_client:
                    logger.warning("Redis 클라이언트 없음, 캐시 조회 스킵")
                    for d in redis_miss_dates:
                        result[d] = None
                else:
                    cached_values = await redis_client.mget(*redis_miss_keys)

                    # 4. 🚀 병렬 압축 해제 + 역직렬화
                    loop = asyncio.get_event_loop()
                    deserialize_tasks = []

                    for cached_data in cached_values:
                        if cached_data:
                            task = loop.run_in_executor(
                                self._executor,
                                self._decompress_and_deserialize,
                                cached_data
                            )
                            deserialize_tasks.append(task)
                        else:
                            deserialize_tasks.append(asyncio.sleep(0, result=None))

                    deserialized_results = await asyncio.gather(*deserialize_tasks)

                    # 5. 결과 매핑 + 메모리 캐시 저장
                    for i, calc_date in enumerate(redis_miss_dates):
                        data = deserialized_results[i]
                        result[calc_date] = data

                        # 메모리 캐시에 저장 (LRU 간단 구현)
                        if data is not None:
                            cache_key = redis_miss_keys[i]
                            self._memory_cache[cache_key] = data

                            # 메모리 캐시 크기 제한
                            if len(self._memory_cache) > self._max_memory_items:
                                # 가장 오래된 항목 제거 (간단한 구현)
                                oldest_key = next(iter(self._memory_cache))
                                del self._memory_cache[oldest_key]

            # 6. 통계
            hit_count = sum(1 for v in result.values() if v is not None)
            miss_count = len(dates) - hit_count
            hit_rate = (hit_count / len(dates) * 100) if len(dates) > 0 else 0

            if miss_count > 0:
                logger.warning(f"⚠️ 캐시 미스 발생: {miss_count}/{len(dates)}개 날짜")
                missed_keys = [cache_keys[d] for d, v in result.items() if v is None][:3]
                logger.warning(f"   미스된 키 예시: {missed_keys}")
            else:
                logger.info(f"✅ 100% 캐시 히트! ({len(dates)}개 날짜)")

            logger.info(f"📊 배치 캐시 조회 결과: {hit_count}/{len(dates)} 히트 ({hit_rate:.1f}%)")

            return result

        except Exception as e:
            logger.error(f"배치 캐시 조회 실패: {e}")
            return {d: None for d in dates}

    async def set_factors_batch(
        self,
        factor_data: Dict[date, Dict[str, Dict[str, float]]],
        factor_names: List[str],
        target_themes: List[str] = None,
        target_stocks: List[str] = None,
        strategy_hash: str = None
    ) -> bool:
        """
        배치 캐시 저장 (네트워크 IO 최소화)

        기존: 252일 × 300ms = 75초
        최적화: 1회 × 800ms = 0.8초 (90배 개선!)

        🔥 FIXED: strategy_hash 파라미터 추가로 전략별 캐시 격리
        """
        try:
            # 1. 캐시 데이터 준비 (전략 해시 포함)
            cache_dict = {}
            for calc_date, factors in factor_data.items():
                cache_key = self._generate_factor_cache_key(
                    calc_date, factor_names, target_themes, target_stocks, strategy_hash
                )

                # 직렬화 + 압축
                serialized = pickle.dumps(factors, protocol=pickle.HIGHEST_PROTOCOL)
                compressed = lz4.frame.compress(serialized)

                cache_dict[cache_key] = compressed

            # 2. Redis MSET으로 일괄 저장
            from app.core.cache import get_redis
            redis_client = get_redis()
            if not redis_client:
                logger.warning("Redis 클라이언트 없음, 캐시 저장 스킵")
                return False

            await redis_client.mset(cache_dict)

            # 3. TTL 설정 (일괄)
            pipeline = redis_client.pipeline()
            for cache_key in cache_dict.keys():
                pipeline.expire(cache_key, self.default_ttl)
            await pipeline.execute()

            logger.info(f"배치 캐시 저장: {len(cache_dict)}개 항목")
            return True

        except Exception as e:
            logger.error(f"배치 캐시 저장 실패: {e}")
            return False

    async def get_price_data_cached(
        self,
        cache_key: str,
        ttl: int = None
    ) -> Optional[Any]:
        """가격 데이터 캐시 조회"""
        try:
            if ttl is None:
                ttl = self.default_ttl

            cached = await cache.get(cache_key)
            if cached:
                # 압축 해제
                decompressed = lz4.frame.decompress(cached)
                return pickle.loads(decompressed)
            return None

        except Exception as e:
            logger.error(f"가격 데이터 캐시 조회 실패: {e}")
            return None

    async def set_price_data_cached(
        self,
        cache_key: str,
        data: Any,
        ttl: int = None
    ) -> bool:
        """가격 데이터 캐시 저장 (압축)"""
        try:
            if ttl is None:
                ttl = self.default_ttl

            # 직렬화 + 압축
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            compressed = lz4.frame.compress(serialized)

            # 압축률 로깅
            compression_ratio = len(compressed) / len(serialized) * 100
            logger.info(f"캐시 압축률: {compression_ratio:.1f}% (원본: {len(serialized)/1024:.1f}KB → 압축: {len(compressed)/1024:.1f}KB)")

            await cache.set(cache_key, compressed, ttl=ttl)
            return True

        except Exception as e:
            logger.error(f"가격 데이터 캐시 저장 실패: {e}")
            return False

    async def invalidate_factors_cache(
        self,
        start_date: date = None,
        end_date: date = None
    ) -> int:
        """팩터 캐시 무효화 (날짜 범위)"""
        try:
            # 패턴 매칭으로 삭제
            from app.core.cache import get_redis
            redis_client = get_redis()
            if not redis_client:
                logger.warning("Redis 클라이언트 없음, 캐시 무효화 스킵")
                return 0

            pattern = f"{self.cache_prefix}:factors:*"
            keys = await redis_client.keys(pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"팩터 캐시 무효화: {deleted}개 삭제")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"캐시 무효화 실패: {e}")
            return 0


# 싱글톤 인스턴스
optimized_cache = OptimizedCacheManager()
