"""
유명 전략 전체 캐시 워밍 스크립트

전략 (10개):
1. surge_stocks (급등주 전략)
2. steady_growth (안정 성장 전략)
3. peter_lynch (피터린치)
4. warren_buffett (워렌버핏)
5. william_oneil (윌리엄 오닐)
6. bill_ackman (빌 애크먼)
7. charlie_munger (찰리 멍거)
8. glenn_welling (글렌 웰링)
9. cathie_wood (캐시 우드)
10. glenn_greenberg (글렌 그린버그)

캐시 데이터:
- 가격 데이터 (1년치, Redis)
- 팩터 데이터 (전략별 독립, LZ4 압축)

실행 방법:
    python3 scripts/warm_all_famous_strategies.py
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine
from app.services.backtest_integration import integrate_optimizations
from app.services.backtest_cache_optimized import generate_strategy_hash

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==================== 전략 설정 (10개 전략) ====================

STRATEGIES_CONFIG = {
    # 1. 급등주 전략
    "surge_stocks": {
        "name": "급등주 전략",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["전기 / 전자", "증권"],
        "expression": "A",
        "conditions": [
            {"id": "A", "factor": "MARKET_CAP", "operator": ">", "value": 7000000000},
        ],
        "target_gain": 12,
        "stop_loss": 7,
        "min_hold_days": 3,
        "max_hold_days": 15,
    },

    # 2. 안정 성장 전략
    "steady_growth": {
        "name": "안정 성장 전략",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["IT서비스", "전기 / 가스 / 수도", "음식료 / 담배"],
        "expression": "A and B and C and D",
        "conditions": [
            {"id": "A", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": -5},
            {"id": "B", "factor": "OPERATING_INCOME_GROWTH_YOY", "operator": ">", "value": -5},
            {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 120},
            {"id": "D", "factor": "ROE", "operator": ">", "value": 8},
        ],
        "target_gain": 20,
        "stop_loss": 12,
        "min_hold_days": 60,
        "max_hold_days": 360,
    },

    # 3. 피터린치 (Peter Lynch)
    "peter_lynch": {
        "name": "피터린치",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["IT서비스", "섬유 / 의류"],
        "expression": "A and B and C and D and E and F",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 40},
            {"id": "B", "factor": "PEG", "operator": ">", "value": 0},
            {"id": "C", "factor": "PEG", "operator": "<", "value": 2.0},
            {"id": "D", "factor": "DEBT_RATIO", "operator": "<", "value": 180},
            {"id": "E", "factor": "ROE", "operator": ">", "value": 3},
            {"id": "F", "factor": "ROA", "operator": ">", "value": 0.5},
        ],
        "target_gain": 25,
        "stop_loss": 15,
        "min_hold_days": 90,
        "max_hold_days": 540,
    },

    # 4. 워렌버핏 (Warren Buffett)
    "warren_buffett": {
        "name": "워렌버핏",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["IT서비스", "금융", "전기 / 가스 / 수도", "보험"],
        "expression": "A and B and C and D and E and F",
        "conditions": [
            {"id": "A", "factor": "ROE", "operator": ">", "value": 12},
            {"id": "B", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.2},
            {"id": "C", "factor": "PER", "operator": "<", "value": 20},
            {"id": "D", "factor": "PBR", "operator": "<", "value": 2.0},
            {"id": "E", "factor": "DEBT_RATIO", "operator": "<", "value": 170},
            {"id": "F", "factor": "EARNINGS_GROWTH_1Y", "operator": ">", "value": 5},
        ],
        "target_gain": 40,
        "stop_loss": 20,
        "min_hold_days": 180,
        "max_hold_days": 720,
    },

    # 5. 윌리엄 오닐 (William O'Neil)
    "william_oneil": {
        "name": "윌리엄 오닐",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["전기 / 전자", "통신"],
        "expression": "A and B and C",
        "conditions": [
            {"id": "A", "factor": "EARNINGS_GROWTH_1Y", "operator": ">", "value": 12},
            {"id": "B", "factor": "ROE", "operator": ">", "value": 12},
            {"id": "C", "factor": "DISTANCE_FROM_52W_HIGH", "operator": ">", "value": -25},
        ],
        "target_gain": 28,
        "stop_loss": 12,
        "min_hold_days": 20,
        "max_hold_days": 180,
    },

    # 6. 빌 애크먼 (Bill Ackman)
    "bill_ackman": {
        "name": "빌 애크먼",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["IT서비스", "금융", "증권"],
        "expression": "A and B and C and D",
        "conditions": [
            {"id": "A", "factor": "ROIC", "operator": ">", "value": 10},
            {"id": "B", "factor": "PER", "operator": "<", "value": 22},
            {"id": "C", "factor": "PBR", "operator": "<", "value": 2.5},
            {"id": "D", "factor": "DEBT_RATIO", "operator": ">", "value": 100},
        ],
        "target_gain": 30,
        "stop_loss": 15,
        "min_hold_days": 90,
        "max_hold_days": 360,
    },

    # 7. 찰리 멍거 (Charlie Munger)
    "charlie_munger": {
        "name": "찰리 멍거",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["화학", "비금속", "전기 / 가스 / 수도"],
        "expression": "A and B and C and D and E and F and G",
        "conditions": [
            {"id": "A", "factor": "ROIC", "operator": ">", "value": 12},
            {"id": "B", "factor": "PER", "operator": "<", "value": 14},
            {"id": "C", "factor": "PBR", "operator": "<", "value": 2.0},
            {"id": "D", "factor": "ROE", "operator": ">", "value": 12},
            {"id": "E", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": 10},
            {"id": "F", "factor": "DEBT_RATIO", "operator": "<", "value": 70},
            {"id": "G", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.5},
        ],
        "target_gain": 35,
        "stop_loss": 18,
        "min_hold_days": 180,
        "max_hold_days": 900,
    },

    # 8. 글렌 웰링 (Glenn Welling)
    "glenn_welling": {
        "name": "글렌 웰링",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["기계 / 장비", "기타 제조", "비금속"],
        "expression": "A and B and C and D and E and F",
        "conditions": [
            {"id": "A", "factor": "EV_EBITDA", "operator": "<", "value": 10},
            {"id": "B", "factor": "ROIC", "operator": "<", "value": 12},
            {"id": "C", "factor": "PBR", "operator": "<", "value": 2.0},
            {"id": "D", "factor": "PSR", "operator": "<", "value": 2.0},
            {"id": "E", "factor": "PEG", "operator": ">", "value": 0},
            {"id": "F", "factor": "PEG", "operator": "<", "value": 1.2},
        ],
        "target_gain": 25,
        "stop_loss": 15,
        "min_hold_days": 120,
        "max_hold_days": 540,
    },

    # 9. 캐시 우드 (Cathie Wood)
    "cathie_wood": {
        "name": "캐시 우드",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["전기 / 전자", "통신"],
        "expression": "A and B and C and D and E",
        "conditions": [
            {"id": "A", "factor": "PEG", "operator": ">", "value": 0},
            {"id": "B", "factor": "PEG", "operator": "<", "value": 2.5},
            {"id": "C", "factor": "PSR", "operator": "<", "value": 25},
            {"id": "D", "factor": "REVENUE_GROWTH_1Y", "operator": ">", "value": 15},
            {"id": "E", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.5},
        ],
        "target_gain": 40,
        "stop_loss": 20,
        "min_hold_days": 90,
        "max_hold_days": 360,
    },

    # 10. 글렌 그린버그 (Glenn Greenberg)
    "glenn_greenberg": {
        "name": "글렌 그린버그",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "themes": ["유통", "증권", "은행"],
        "expression": "A and B and C",
        "conditions": [
            {"id": "A", "factor": "PER", "operator": "<", "value": 20},
            {"id": "B", "factor": "ROIC", "operator": ">", "value": 12},
            {"id": "C", "factor": "DEBT_RATIO", "operator": "<", "value": 70},
        ],
        "target_gain": 30,
        "stop_loss": 15,
        "min_hold_days": 120,
        "max_hold_days": 540,
    },
}


# ==================== 전략 해시 생성 ====================

def generate_all_strategy_hashes():
    """모든 전략의 해시 생성"""
    logger.info("=" * 80)
    logger.info("🔐 전략 해시 생성 (10개 전략)")
    logger.info("=" * 80)

    hashes = {}
    for strategy_id, config in STRATEGIES_CONFIG.items():
        # 🔥 FIX: buy_conditions 구조를 백테스트 실행 시와 동일하게 맞춤
        # backtest.py:356-360에서 loaded_strategy_config에 priority_factor, priority_order 추가됨
        # DB에 priority_factor가 없으면 request.priority_factor(빈 문자열)가 사용됨
        buy_conditions = {
            "expression": config["expression"],
            "conditions": config["conditions"],
            "priority_factor": config.get("priority_factor"),  # DB에 없으면 None
            "priority_order": config.get("priority_order", "desc")  # 기본값: desc
        }
        # 🔥 프론트엔드 → 백엔드 API 요청과 동일한 구조로 설정 (해시 일치 보장)
        # 프론트엔드에서 전송하는 값: sell_price_basis="전일 종가", sell_price_offset=0
        trading_rules = {
            "target_and_loss": {
                "target_gain": config["target_gain"],
                "stop_loss": config["stop_loss"]
            },
            "hold_days": {
                "min_hold_days": config["min_hold_days"],
                "max_hold_days": config["max_hold_days"],
                "sell_price_basis": "전일 종가",  # 프론트엔드 기본값
                "sell_price_offset": 0            # 프론트엔드 기본값 (Decimal(0)으로 정규화됨)
            },
            "condition_sell_meta": None
        }
        strategy_hash = generate_strategy_hash(buy_conditions, trading_rules)
        hashes[strategy_id] = strategy_hash
        logger.info(f"   {config['name']:15s} ({strategy_id:20s}) → {strategy_hash}")

    logger.info("=" * 80)
    return hashes


# ==================== 캐시 워밍 함수 ====================

async def warm_price_data_for_all_strategies():
    """모든 전략용 가격 데이터 캐싱 (1년치, 공통)"""
    logger.info("=" * 80)
    logger.info("📈 가격 데이터 캐싱 시작 (2024-01-01 ~ 2024-12-31)")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)
        integrate_optimizations(engine)

        # 모든 전략의 테마 수집
        all_themes = set()
        for config in STRATEGIES_CONFIG.values():
            all_themes.update(config["themes"])

        all_themes_list = sorted(list(all_themes))
        logger.info(f"📊 대상 테마 ({len(all_themes_list)}개): {', '.join(all_themes_list)}")

        import time
        start_time = time.time()

        # 가격 데이터 로드 (캐싱 자동 적용)
        price_data = await engine._load_price_data(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            target_themes=all_themes_list,
            target_stocks=None
        )

        elapsed = time.time() - start_time
        logger.info(f"✅ 가격 데이터 캐싱 완료: {len(price_data)}개 종목, {elapsed:.2f}초")
        logger.info("=" * 80)

    return all_themes_list


async def warm_factor_data_for_strategy(strategy_id: str, config: dict, strategy_hash: str):
    """특정 전략용 팩터 데이터 캐싱"""
    logger.info(f"\n🎯 전략: {config['name']} ({strategy_id})")
    logger.info(f"   해시: {strategy_hash}")

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)
        integrate_optimizations(engine)

        themes = config["themes"]
        themes_str = ','.join(sorted(themes))

        logger.info(f"   테마: {themes_str}")

        # 날짜 범위 생성 (일간 단위 - 100% 캐시 히트를 위해)
        start_date = config["start_date"]
        end_date = config["end_date"]
        current_date = start_date
        dates = []

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)  # 매일 (100% 캐시 히트)

        logger.info(f"   캐싱 날짜: {len(dates)}개 (일간 단위 - 모든 거래일)")

        import time
        overall_start = time.time()
        cached_count = 0
        new_cached = 0

        # 배치 처리 (진행률 표시 개선)
        from app.services.backtest_cache_optimized import optimized_cache

        # 진행률 업데이트 간격 설정 (10% 단위)
        progress_interval = max(1, len(dates) // 10)

        # 캐시 직접 사용 (OptimizedCacheManager가 아닌 core.cache)
        from app.core.cache import get_cache
        cache = get_cache()

        for i, calc_date in enumerate(dates, 1):
            cache_key = f"backtest_optimized:factors:{calc_date}:{themes_str}:{strategy_hash}"

            # 캐시 확인
            cached = await cache.get(cache_key)
            if cached is not None:
                cached_count += 1
                # 진행률 로그 (10% 단위)
                if i % progress_interval == 0 or i == len(dates):
                    progress = (i / len(dates)) * 100
                    logger.info(f"      진행: {progress:5.1f}% ({i:3d}/{len(dates)}) | 기존: {cached_count:3d}, 신규: {new_cached:3d}")
                continue

            # 팩터 계산 및 캐싱
            try:
                # 팩터 계산
                factors = await engine._calculate_all_factors_optimized(
                    calc_date=calc_date,
                    target_themes=themes,
                    target_stocks=None
                )

                if not factors.empty:
                    # 캐시 저장: DataFrame을 직렬화하여 저장
                    import lz4.frame
                    import pickle

                    # DataFrame을 pickle로 직렬화
                    serialized = pickle.dumps(factors)
                    # LZ4 압축
                    compressed = lz4.frame.compress(serialized)

                    # 캐시 저장 (TTL=영구, 30일)
                    await cache.set(cache_key, compressed, ttl=30*24*3600)
                    new_cached += 1

                    # 진행률 로그 (10% 단위)
                    if i % progress_interval == 0 or i == len(dates):
                        progress = (i / len(dates)) * 100
                        logger.info(f"      진행: {progress:5.1f}% ({i:3d}/{len(dates)}) | 기존: {cached_count:3d}, 신규: {new_cached:3d}")

            except Exception as e:
                logger.error(f"      [{i}/{len(dates)}] {calc_date}: ❌ 오류 - {e}")

        overall_elapsed = time.time() - overall_start
        logger.info(f"   ✅ 완료: 기존 {cached_count}개, 신규 {new_cached}개, 총 {overall_elapsed:.2f}초")


async def warm_all_strategies():
    """모든 유명 전략 캐시 워밍 (병렬 처리)"""
    logger.info("🚀 유명 전략 전체 캐시 워밍 시작 (10개 전략 - 병렬 처리)")
    logger.info(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    import time
    total_start = time.time()

    # 1. 전략 해시 생성
    strategy_hashes = generate_all_strategy_hashes()
    logger.info("")

    # 2. 가격 데이터 캐싱 (공통)
    await warm_price_data_for_all_strategies()

    # 3. 각 전략별 팩터 데이터 캐싱 (병렬 처리)
    logger.info("=" * 80)
    logger.info("🔥 팩터 데이터 캐싱 시작 (전략별 독립 - 병렬 처리)")
    logger.info("=" * 80)

    # 병렬 처리: 4개씩 동시 실행
    BATCH_SIZE = 4
    strategy_items = list(STRATEGIES_CONFIG.items())

    for batch_idx in range(0, len(strategy_items), BATCH_SIZE):
        batch = strategy_items[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        total_batches = (len(strategy_items) + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 배치 {batch_num}/{total_batches} 시작 ({len(batch)}개 전략 병렬 처리)")
        logger.info(f"{'='*80}")

        tasks = []
        for idx, (strategy_id, config) in enumerate(batch, 1):
            global_idx = batch_idx + idx
            logger.info(f"   [{global_idx}/10] {config['name']} 준비")
            strategy_hash = strategy_hashes[strategy_id]
            task = warm_factor_data_for_strategy(strategy_id, config, strategy_hash)
            tasks.append(task)

        # 병렬 실행
        await asyncio.gather(*tasks)

    total_elapsed = time.time() - total_start

    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 캐시 워밍 완료!")
    logger.info(f"⏱️  총 소요 시간: {total_elapsed:.2f}초 ({total_elapsed/60:.1f}분)")
    logger.info(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # 캐시 크기 추정
    await estimate_cache_size(strategy_hashes)


async def estimate_cache_size(strategy_hashes: dict):
    """캐시 메모리 사용량 추정"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("💾 캐시 메모리 사용량 추정")
    logger.info("=" * 80)

    from app.services.backtest_cache_optimized import optimized_cache

    # Redis에서 캐시 키 조회
    import redis.asyncio as redis
    redis_client = redis.from_url("redis://localhost:6379/0")

    try:
        # 전략별 캐시 크기 추정
        total_size = 0
        total_keys = 0

        for strategy_id, strategy_hash in strategy_hashes.items():
            # 해당 전략의 캐시 키 패턴
            pattern = f"backtest_optimized:factors:*:*:{strategy_hash}"
            keys = await redis_client.keys(pattern)

            strategy_size = 0
            for key in keys:
                size = await redis_client.memory_usage(key)
                if size:
                    strategy_size += size

            total_size += strategy_size
            total_keys += len(keys)

            strategy_name = STRATEGIES_CONFIG[strategy_id]["name"]
            logger.info(f"   {strategy_name:15s}: {len(keys):3d}개 키, {strategy_size/1024/1024:8.2f} MB")

        logger.info(f"   {'─' * 60}")
        logger.info(f"   {'팩터 캐시 총계':15s}: {total_keys:3d}개 키, {total_size/1024/1024:8.2f} MB")

        # 가격 데이터 캐시 크기
        price_keys = await redis_client.keys("price_data:*")
        price_size = 0
        for key in price_keys:
            size = await redis_client.memory_usage(key)
            if size:
                price_size += size

        logger.info(f"   {'가격 데이터 캐시':15s}: {len(price_keys):3d}개 키, {price_size/1024/1024:8.2f} MB")
        logger.info(f"   {'═' * 60}")
        logger.info(f"   {'전체 캐시 크기':15s}: {total_keys + len(price_keys):3d}개 키, {(total_size + price_size)/1024/1024:8.2f} MB")

    finally:
        await redis_client.close()

    logger.info("=" * 80)


# ==================== 메인 실행 ====================

if __name__ == "__main__":
    asyncio.run(warm_all_strategies())
