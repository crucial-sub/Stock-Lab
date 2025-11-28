"""
유명 전략 통합 캐시 워밍 스크립트

전략:
- 피터린치 (Peter Lynch): 성장주 투자 (PEG < 2.0, ROE > 3%)
- 워렌버핏 (Warren Buffett): 가치주 투자 (ROE > 12%, PER < 20)
- 벤저민 그레이엄 (Benjamin Graham): 저평가 가치주 (PER < 15, PBR < 1.5)

캐시 데이터:
- 가격 데이터 (1년치, Redis)
- 팩터 데이터 (전략별 독립, LZ4 압축)

실행 방법:
    python3 scripts/warm_famous_strategies.py
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
from app.services.backtest_cache_optimized import generate_strategy_hash

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==================== 전략 설정 ====================

# 피터린치 전략
PETER_LYNCH_CONFIG = {
    "strategy_name": "peter_lynch",
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 12, 31),
    "initial_capital": Decimal("10000000"),
    "themes": ["IT서비스", "섬유 / 의류"],

    # 매수 조건 (벡터화 평가용)
    "expression": "A and B and C and D and E and F",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 40},
        {"id": "B", "factor": "PEG", "operator": ">", "value": 0},
        {"id": "C", "factor": "PEG", "operator": "<", "value": 2.0},
        {"id": "D", "factor": "DEBT_RATIO", "operator": "<", "value": 180},
        {"id": "E", "factor": "ROE", "operator": ">", "value": 3},
        {"id": "F", "factor": "ROA", "operator": ">", "value": 0.5},
    ],

    # 매매 규칙
    "target_gain": 25,
    "stop_loss": 15,
    "min_hold_days": 90,
    "max_hold_days": 540,

    # 조건부 매도
    "condition_sell_expression": "A or B",
    "condition_sell_conditions": [
        {"id": "A", "factor": "PEG", "operator": ">", "value": 2.5},
        {"id": "B", "factor": "DEBT_RATIO", "operator": ">", "value": 200},
    ],
}

# 워렌버핏 전략
WARREN_BUFFETT_CONFIG = {
    "strategy_name": "warren_buffett",
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 12, 31),
    "initial_capital": Decimal("10000000"),
    "themes": ["IT서비스", "금융", "전기 / 가스 / 수도", "보험"],

    # 매수 조건
    "expression": "A and B and C and D and E and F",
    "conditions": [
        {"id": "A", "factor": "ROE", "operator": ">", "value": 12},
        {"id": "B", "factor": "CURRENT_RATIO", "operator": ">", "value": 1.2},
        {"id": "C", "factor": "PER", "operator": "<", "value": 20},
        {"id": "D", "factor": "PBR", "operator": "<", "value": 2.0},
        {"id": "E", "factor": "DEBT_RATIO", "operator": "<", "value": 170},
        {"id": "F", "factor": "EARNINGS_GROWTH_1Y", "operator": ">", "value": 5},
    ],

    # 매매 규칙
    "target_gain": 40,
    "stop_loss": 20,
    "min_hold_days": 180,
    "max_hold_days": 720,

    # 조건부 매도
    "condition_sell_expression": "A or B",
    "condition_sell_conditions": [
        {"id": "A", "factor": "PBR", "operator": ">", "value": 2.5},
        {"id": "B", "factor": "ROE", "operator": "<", "value": 8},
    ],
}

# 벤저민 그레이엄 전략 (migrate_strategies.py에 없지만 추가)
BENJAMIN_GRAHAM_CONFIG = {
    "strategy_name": "benjamin_graham",
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 12, 31),
    "initial_capital": Decimal("10000000"),
    "themes": ["금융", "보험", "음식료 / 담배", "전기 / 가스 / 수도"],

    # 매수 조건 (방어적 투자자 기준)
    "expression": "A and B and C and D and E",
    "conditions": [
        {"id": "A", "factor": "PER", "operator": "<", "value": 15},
        {"id": "B", "factor": "PBR", "operator": "<", "value": 1.5},
        {"id": "C", "factor": "CURRENT_RATIO", "operator": ">", "value": 2.0},
        {"id": "D", "factor": "DEBT_RATIO", "operator": "<", "value": 100},
        {"id": "E", "factor": "ROE", "operator": ">", "value": 10},
    ],

    # 매매 규칙
    "target_gain": 30,
    "stop_loss": 15,
    "min_hold_days": 180,
    "max_hold_days": 900,

    # 조건부 매도
    "condition_sell_expression": "A or B",
    "condition_sell_conditions": [
        {"id": "A", "factor": "PER", "operator": ">", "value": 20},
        {"id": "B", "factor": "PBR", "operator": ">", "value": 2.0},
    ],
}


# ==================== 전략 해시 생성 ====================

def generate_strategy_hashes():
    """각 전략의 해시 생성"""
    strategies = {
        "peter_lynch": PETER_LYNCH_CONFIG,
        "warren_buffett": WARREN_BUFFETT_CONFIG,
        "benjamin_graham": BENJAMIN_GRAHAM_CONFIG,
    }

    hashes = {}
    for name, config in strategies.items():
        buy_conditions = {
            "expression": config["expression"],
            "conditions": config["conditions"]
        }
        trading_rules = {
            "target_gain": config["target_gain"],
            "stop_loss": config["stop_loss"],
            "min_hold_days": config["min_hold_days"],
            "max_hold_days": config["max_hold_days"]
        }
        strategy_hash = generate_strategy_hash(buy_conditions, trading_rules)
        hashes[name] = strategy_hash
        logger.info(f"🔐 전략 해시 생성: {name} → {strategy_hash}")

    return hashes


# ==================== 캐시 워밍 함수 ====================

async def warm_price_data_for_all_strategies():
    """모든 전략용 가격 데이터 캐싱 (1년치, 공통)"""
    logger.info("=" * 80)
    logger.info("📈 가격 데이터 캐싱 시작 (2024-01-01 ~ 2024-12-31)")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        # 모든 전략의 테마 수집
        all_themes = set()
        for config in [PETER_LYNCH_CONFIG, WARREN_BUFFETT_CONFIG, BENJAMIN_GRAHAM_CONFIG]:
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

    return all_themes_list


async def warm_factor_data_for_strategy(strategy_name: str, config: dict, strategy_hash: str):
    """특정 전략용 팩터 데이터 캐싱"""
    logger.info("=" * 80)
    logger.info(f"🎯 전략: {strategy_name} (해시: {strategy_hash})")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        themes = config["themes"]
        themes_str = ','.join(sorted(themes))

        logger.info(f"📊 테마: {themes_str}")
        logger.info(f"📅 기간: {config['start_date']} ~ {config['end_date']}")

        # 날짜 범위 생성 (주간 단위)
        start_date = config["start_date"]
        end_date = config["end_date"]
        current_date = start_date
        dates = []

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=7)  # 1주일 간격

        logger.info(f"📆 캐싱 날짜: {len(dates)}개 (주간 단위)")

        import time
        overall_start = time.time()
        cached_count = 0

        # 배치 처리
        from app.services.backtest_cache_optimized import optimized_cache

        for i, calc_date in enumerate(dates, 1):
            cache_key = f"backtest_optimized:factors:{calc_date}:{themes_str}:{strategy_hash}"

            # 캐시 확인
            cached = await optimized_cache.get(cache_key)
            if cached is not None:
                logger.info(f"   [{i}/{len(dates)}] {calc_date}: ✅ 캐시 존재")
                cached_count += 1
                continue

            # 팩터 계산 및 캐싱
            try:
                batch_start = time.time()

                # 팩터 계산
                factors = await engine._calculate_all_factors_optimized(
                    calc_date=calc_date,
                    target_themes=themes,
                    target_stocks=None
                )

                if not factors.empty:
                    # 캐시 저장
                    await optimized_cache.set_factors_batch(
                        cache_key=cache_key,
                        factors_df=factors
                    )

                    batch_elapsed = time.time() - batch_start
                    logger.info(f"   [{i}/{len(dates)}] {calc_date}: 🔥 캐싱 완료 ({len(factors)}개 종목, {batch_elapsed:.2f}초)")
                else:
                    logger.warning(f"   [{i}/{len(dates)}] {calc_date}: ⚠️  팩터 없음")

            except Exception as e:
                logger.error(f"   [{i}/{len(dates)}] {calc_date}: ❌ 오류 - {e}")

        overall_elapsed = time.time() - overall_start
        logger.info(f"✅ 전략 캐싱 완료: {cached_count}/{len(dates)}개 이미 존재, 총 {overall_elapsed:.2f}초")


async def warm_all_strategies():
    """모든 유명 전략 캐시 워밍"""
    logger.info("🚀 유명 전략 통합 캐시 워밍 시작")
    logger.info(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    import time
    total_start = time.time()

    # 1. 전략 해시 생성
    strategy_hashes = generate_strategy_hashes()

    # 2. 가격 데이터 캐싱 (공통)
    await warm_price_data_for_all_strategies()

    # 3. 각 전략별 팩터 데이터 캐싱
    strategies = [
        ("peter_lynch", PETER_LYNCH_CONFIG),
        ("warren_buffett", WARREN_BUFFETT_CONFIG),
        ("benjamin_graham", BENJAMIN_GRAHAM_CONFIG),
    ]

    for strategy_name, config in strategies:
        strategy_hash = strategy_hashes[strategy_name]
        await warm_factor_data_for_strategy(strategy_name, config, strategy_hash)

    total_elapsed = time.time() - total_start

    logger.info("=" * 80)
    logger.info("🎉 캐시 워밍 완료!")
    logger.info(f"⏱️  총 소요 시간: {total_elapsed:.2f}초 ({total_elapsed/60:.1f}분)")
    logger.info(f"⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # 캐시 크기 추정
    await estimate_cache_size(strategy_hashes)


async def estimate_cache_size(strategy_hashes: dict):
    """캐시 메모리 사용량 추정"""
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

        for strategy_name, strategy_hash in strategy_hashes.items():
            # 해당 전략의 캐시 키 패턴
            pattern = f"backtest_optimized:factors:*:*:{strategy_hash}"
            keys = await redis_client.keys(pattern)

            strategy_size = 0
            for key in keys:
                size = await redis_client.memory_usage(key)
                if size:
                    strategy_size += size

            total_size += strategy_size

            logger.info(f"   {strategy_name:20s}: {len(keys):3d}개 키, {strategy_size/1024/1024:8.2f} MB")

        logger.info(f"   {'=' * 50}")
        logger.info(f"   {'총 캐시 크기':20s}: {len(strategy_hashes)*52:3d}개 키 (예상), {total_size/1024/1024:8.2f} MB")

        # 가격 데이터 캐시 크기
        price_keys = await redis_client.keys("price_data:*")
        price_size = 0
        for key in price_keys:
            size = await redis_client.memory_usage(key)
            if size:
                price_size += size

        logger.info(f"   {'가격 데이터 캐시':20s}: {len(price_keys):3d}개 키, {price_size/1024/1024:8.2f} MB")
        logger.info(f"   {'=' * 50}")
        logger.info(f"   {'전체 캐시 크기':20s}: {total_size + price_size:8.0f} bytes ({(total_size + price_size)/1024/1024:.2f} MB)")

    finally:
        await redis_client.close()

    logger.info("=" * 80)


# ==================== 메인 실행 ====================

if __name__ == "__main__":
    asyncio.run(warm_all_strategies())
