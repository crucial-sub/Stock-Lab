"""
백테스트 캐시 Pre-warming 서비스
매일 새벽에 인기 백테스트 조건을 미리 실행하여 캐싱
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from app.core.cache import get_cache
from app.core.database import AsyncSessionLocal
from app.models.backtest import BacktestSession
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.services.factor_calculator_complete import CompleteFactorCalculator

logger = logging.getLogger(__name__)


# 인기 백테스트 조건 (실제 사용자 로그 기반으로 업데이트 필요)
POPULAR_BACKTEST_CONDITIONS = [
    # 저PER 고ROE 전략 (가치주 투자)
    {
        "name": "저PER_고ROE",
        "factors": ["PER", "ROE"],
        "period_days": 365,
        "top_n": 20,
        "description": "PER 낮고 ROE 높은 가치주"
    },
    # 고배당 저PBR 전략
    {
        "name": "고배당_저PBR",
        "factors": ["배당수익률", "PBR"],
        "period_days": 365,
        "top_n": 30,
        "description": "배당 높고 PBR 낮은 안정주"
    },
    # 모멘텀 전략
    {
        "name": "고ROE_고영업이익률",
        "factors": ["ROE", "영업이익률"],
        "period_days": 180,
        "top_n": 20,
        "description": "수익성 높은 성장주"
    },
    # 퀄리티 전략
    {
        "name": "저부채비율_고자기자본비율",
        "factors": ["부채비율", "자기자본비율"],
        "period_days": 365,
        "top_n": 25,
        "description": "재무 건전성 우수 기업"
    },
]


async def get_popular_conditions_from_db() -> List[Dict[str, Any]]:
    """
    실제 사용자가 자주 사용한 백테스트 조건 분석
    최근 30일간 실행 횟수 상위 50개 추출
    """
    try:
        async with AsyncSessionLocal() as db:
            # 최근 30일간 실행된 백테스트 조건 분석
            thirty_days_ago = datetime.now() - timedelta(days=30)

            # BacktestSession에서 자주 사용된 조합 분석
            query = select(BacktestSession).where(
                BacktestSession.created_at >= thirty_days_ago
            ).order_by(desc(BacktestSession.created_at)).limit(100)

            result = await db.execute(query)
            sessions = result.scalars().all()

            # 조건 빈도 분석 (실제 구현 필요)
            # 지금은 기본 조건 반환
            return POPULAR_BACKTEST_CONDITIONS

    except Exception as e:
        logger.error(f"Failed to get popular conditions: {e}")
        return POPULAR_BACKTEST_CONDITIONS


async def get_all_active_stocks(db: AsyncSession) -> List[str]:
    """
    모든 활성 종목 코드 조회
    """
    try:
        # 최근 거래가 있는 종목만 조회
        latest_date_query = select(func.max(StockPrice.trade_date))
        latest_date_result = await db.execute(latest_date_query)
        latest_date = latest_date_result.scalar()

        if not latest_date:
            logger.warning("No stock price data found")
            return []

        # 최근 30일 이내 거래가 있는 종목
        cutoff_date = latest_date - timedelta(days=30)

        # Company 테이블과 조인하여 stock_code 가져오기
        query = select(Company.stock_code).join(
            StockPrice, Company.company_id == StockPrice.company_id
        ).where(
            StockPrice.trade_date >= cutoff_date
        ).distinct()

        result = await db.execute(query)
        stock_codes = [row[0] for row in result.fetchall()]

        logger.info(f"Found {len(stock_codes)} active stocks")
        return stock_codes

    except Exception as e:
        logger.error(f"Failed to get active stocks: {e}")
        return []


async def warm_price_data():
    """
    가격 데이터를 미리 캐싱 (백테스트 핵심 데이터)
    - 최근 3년치 전체 종목 가격 데이터 (영구 캐싱)
    - 백테스트에서 가장 자주 사용하는 데이터
    """
    logger.info("🔥 Starting price data warming (3 years, permanent cache)...")
    cache = get_cache()

    async with AsyncSessionLocal() as db:
        try:
            # 최신 날짜 조회
            latest_date_query = select(func.max(StockPrice.trade_date))
            latest_date_result = await db.execute(latest_date_query)
            latest_date = latest_date_result.scalar()

            if not latest_date:
                logger.warning("No stock price data found")
                return

            # 최근 3년치 데이터 (백테스트 최대 커버리지)
            three_years_ago = latest_date - timedelta(days=1095)  # 365 * 3

            logger.info(f"Warming price data from {three_years_ago} to {latest_date}")

            # 전체 종목 가격 데이터 조회 (필터 없음, Company 정보 포함)
            from app.models.company import Company

            query = select(
                StockPrice.company_id,
                Company.stock_code,
                Company.company_name,
                Company.industry,
                Company.market_type,
                StockPrice.trade_date,
                StockPrice.open_price,
                StockPrice.high_price,
                StockPrice.low_price,
                StockPrice.close_price,
                StockPrice.volume,
                StockPrice.trading_value,
                StockPrice.market_cap,
                StockPrice.listed_shares
            ).join(
                Company, StockPrice.company_id == Company.company_id
            ).where(
                and_(
                    StockPrice.trade_date >= three_years_ago,
                    StockPrice.trade_date <= latest_date,
                    StockPrice.close_price.isnot(None),
                    StockPrice.volume > 0
                )
            ).order_by(
                StockPrice.trade_date,
                Company.stock_code
            )

            result = await db.execute(query)
            all_prices = result.mappings().all()

            if all_prices:
                # 전체 가격 데이터를 캐싱 (필터 없는 베이스 데이터)
                price_data = [
                    {
                        "company_id": str(p["company_id"]),
                        "stock_code": p["stock_code"],
                        "stock_name": p["company_name"],
                        "industry": p["industry"],
                        "market_type": p["market_type"],
                        "date": p["trade_date"].isoformat(),
                        "trade_date": p["trade_date"].isoformat(),  # 호환성
                        "open_price": float(p["open_price"]) if p["open_price"] else None,
                        "high_price": float(p["high_price"]) if p["high_price"] else None,
                        "low_price": float(p["low_price"]) if p["low_price"] else None,
                        "close_price": float(p["close_price"]),
                        "volume": int(p["volume"]),
                        "trading_value": float(p["trading_value"]) if p["trading_value"] else None,
                        "market_cap": float(p["market_cap"]) if p["market_cap"] else None,
                        "listed_shares": int(p["listed_shares"]) if p["listed_shares"] else None,
                    }
                    for p in all_prices
                ]

                # 날짜 범위별로 캐싱 (절대 날짜 기준 표준 기간)
                # 백테스트와 호환되도록 고정된 표준 기간 사용
                from datetime import date

                standard_periods = [
                    (date(2024, 1, 1), date(2024, 12, 31), "2024_full"),     # 2024년 전체
                    (date(2023, 1, 1), date(2024, 12, 31), "2023-2024"),     # 2년
                    (date(2022, 1, 1), date(2024, 12, 31), "2022-2024"),     # 3년
                    (date(2024, 7, 1), date(2024, 12, 31), "2024_h2"),       # 2024 하반기
                ]

                for start_date, end_date, label in standard_periods:
                    filtered_data = [
                        p for p in price_data
                        if start_date <= datetime.fromisoformat(p["trade_date"]).date() <= end_date
                    ]

                    cache_key = f"price_data:all:{start_date}:{end_date}"
                    await cache.set(cache_key, filtered_data, ttl=0)  # 영구 캐싱 (TTL=0)
                    logger.info(f"✅ Cached {label} price data: {len(filtered_data)} records (permanent)")

            logger.info("✅ Price data warming completed!")

        except Exception as e:
            logger.error(f"❌ Price data warming failed: {e}")


async def warm_factor_calculations():
    """
    팩터 계산 결과를 미리 캐싱
    - 모든 종목의 최신 팩터 값
    - 주요 팩터만 캐싱 (메모리 효율)
    """
    logger.info("🔥 Starting factor calculation warming...")
    cache = get_cache()

    async with AsyncSessionLocal() as db:
        try:
            # 주요 팩터 리스트 (자주 사용되는 것만)
            important_factors = [
                "PER", "PBR", "ROE", "ROA", "EPS",
                "배당수익률", "영업이익률", "순이익률",
                "부채비율", "자기자본비율", "유동비율"
            ]

            # 최신 날짜 가져오기
            latest_date_query = select(func.max(StockPrice.trade_date))
            latest_date_result = await db.execute(latest_date_query)
            base_date = latest_date_result.scalar()

            if not base_date:
                logger.warning("No stock price data found")
                return

            logger.info(f"Using base date: {base_date}")

            # 활성 종목 코드 조회
            stock_codes = await get_all_active_stocks(db)
            if not stock_codes:
                logger.warning("No active stocks found")
                return

            # 팩터 계산기 초기화
            calculator = CompleteFactorCalculator(db)

            # ⚡ 전체 종목을 한 번에 계산 (배치 크기 증가)
            batch_size = 1000  # 100 -> 500으로 증가
            for i in range(0, len(stock_codes), batch_size):
                batch = stock_codes[i:i + batch_size]

                try:
                    # 모든 팩터 계산
                    factors_df = await calculator.calculate_all_factors(
                        stock_codes=batch,
                        date=datetime.combine(base_date, datetime.min.time()) if isinstance(base_date, date) else base_date
                    )

                    if factors_df is not None and not factors_df.empty:
                        # 팩터별로 캐싱
                        for factor_name in important_factors:
                            if factor_name in factors_df.columns:
                                cache_key = f"quant:factor:{factor_name}:{base_date}:batch_{i}"
                                factor_data = factors_df[[factor_name]].to_dict()
                                await cache.set(cache_key, factor_data, ttl=0)  # 영구 캐싱 (TTL=0)

                        logger.info(f"✅ Cached factors for batch {i//batch_size + 1} ({len(batch)} stocks, permanent)")

                except Exception as e:
                    logger.error(f"❌ Failed to calculate factors for batch {i}: {e}")
                    continue

            logger.info("✅ Factor warming completed!")

        except Exception as e:
            logger.error(f"❌ Factor warming failed: {e}")


async def warm_stock_rankings():
    """
    종목 랭킹 데이터를 미리 캐싱
    - 시가총액 상위 종목
    - 거래량 상위 종목
    - 각 팩터별 상위 종목
    """
    logger.info("🔥 Starting stock ranking warming...")
    cache = get_cache()

    async with AsyncSessionLocal() as db:
        try:
            # 최신 날짜
            latest_date_query = select(func.max(StockPrice.trade_date))
            latest_date_result = await db.execute(latest_date_query)
            latest_date = latest_date_result.scalar()

            if not latest_date:
                return

            # 시가총액 상위 100개 (StockPrice에서 최신 데이터 사용)
            market_cap_query = select(
                Company.stock_code,
                Company.company_name,
                StockPrice.market_cap
            ).join(
                StockPrice, Company.company_id == StockPrice.company_id
            ).where(
                and_(
                    StockPrice.trade_date == latest_date,
                    StockPrice.market_cap.isnot(None)
                )
            ).order_by(desc(StockPrice.market_cap)).limit(100)

            result = await db.execute(market_cap_query)
            top_market_cap = [
                {
                    "stock_code": row[0],
                    "company_name": row[1],
                    "market_cap": float(row[2]) if row[2] else None
                }
                for row in result.fetchall()
            ]

            cache_key = f"quant:ranking:market_cap:top100:{latest_date}"
            await cache.set(cache_key, top_market_cap, ttl=0)  # 영구 캐싱 (TTL=0)
            logger.info(f"📈 Cached market cap top 100 (permanent)")

            # 거래량 상위 100개 (최근 20일 평균)
            twenty_days_ago = latest_date - timedelta(days=20)

            volume_query = select(
                Company.stock_code,
                func.avg(StockPrice.volume).label('avg_volume')
            ).join(
                StockPrice, Company.company_id == StockPrice.company_id
            ).where(
                and_(
                    StockPrice.trade_date >= twenty_days_ago,
                    StockPrice.trade_date <= latest_date,
                    StockPrice.volume > 0
                )
            ).group_by(Company.stock_code).order_by(
                desc('avg_volume')
            ).limit(100)

            result = await db.execute(volume_query)
            top_volume = [
                {
                    "stock_code": row[0],
                    "avg_volume": float(row[1]) if row[1] else None
                }
                for row in result.fetchall()
            ]

            cache_key = f"quant:ranking:volume:top100:{latest_date}"
            await cache.set(cache_key, top_volume, ttl=0)  # 영구 캐싱 (TTL=0)
            logger.info(f"📈 Cached volume top 100 (permanent)")

            logger.info("✅ Ranking warming completed!")

        except Exception as e:
            logger.error(f"❌ Ranking warming failed: {e}")


async def warm_backtest_results():
    """
    인기 백테스트 결과를 미리 캐싱
    (실제 백테스트 실행은 매우 무거우므로 선별적으로)
    """
    logger.info("🔥 Starting backtest warming...")
    cache = get_cache()

    try:
        # 인기 조건 가져오기
        conditions = await get_popular_conditions_from_db()

        # 백테스트는 매우 무거우므로 상위 5개만 실행
        top_conditions = conditions[:5]

        for condition in top_conditions:
            try:
                cache_key = f"quant:backtest_meta:{condition['name']}"

                # 이미 캐시에 있으면 스킵
                if await cache.exists(cache_key):
                    logger.debug(f"✓ {condition['name']} already cached")
                    continue

                # 실제 백테스트 실행 대신 메타데이터만 캐싱
                # (실제 백테스트는 사용자 요청 시 실행)
                metadata = {
                    "condition": condition,
                    "warmed_at": datetime.now().isoformat(),
                    "ready": True
                }

                await cache.set(cache_key, metadata, ttl=86400)  # 1일
                logger.info(f"💰 Warmed backtest metadata: {condition['name']}")

            except Exception as e:
                logger.error(f"❌ Failed to warm {condition['name']}: {e}")
                continue

        logger.info("✅ Backtest warming completed!")

    except Exception as e:
        logger.error(f"❌ Backtest warming failed: {e}")


async def warm_famous_strategies():
    """
    유명 투자 전략 10개 캐싱 (병렬 처리)
    - 급등주, 안정성장, 피터린치, 워렌버핏 등
    - 30-35분 소요 (4개씩 병렬 처리)
    """
    logger.info("🔥 Starting famous strategies warming (10 strategies, parallel)...")

    try:
        import subprocess
        import os

        # 유명 전략 캐시 워밍 스크립트 실행
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "scripts",
            "warm_all_famous_strategies.py"
        )

        if not os.path.exists(script_path):
            logger.warning(f"⚠️ Famous strategies script not found: {script_path}")
            logger.info(f"   Expected path: {script_path}")
            return

        logger.info(f"📂 Running script: {script_path}")

        # 서브프로세스로 실행
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=3600  # 1시간 타임아웃
        )

        if result.returncode == 0:
            logger.info("✅ Famous strategies warming completed!")
            # 주요 로그만 출력
            for line in result.stdout.split('\n'):
                if any(keyword in line for keyword in ['✅', '🔄', '배치', '완료', '시작']):
                    logger.info(f"   {line}")
        else:
            logger.error(f"❌ Famous strategies warming failed!")
            logger.error(f"   Return code: {result.returncode}")
            logger.error(f"   Stderr: {result.stderr[:500]}")  # 처음 500자만

    except subprocess.TimeoutExpired:
        logger.error("❌ Famous strategies warming timeout (1 hour)")
    except Exception as e:
        logger.error(f"❌ Famous strategies warming failed: {e}")


async def run_cache_warming():
    """
    전체 캐시 워밍 프로세스 실행
    스케줄러를 통해 매일 새벽 3시에 실행됨
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("🔥🔥🔥 CACHE WARMING STARTED 🔥🔥🔥")
    logger.info(f"Start time: {start_time}")
    logger.info("=" * 80)

    try:
        # 0단계: 가격 데이터 캐싱 (최우선!) - 백테스트 핵심 데이터
        await warm_price_data()

        # 1단계: 팩터 계산 캐싱 (기본 데이터) - 가장 중요!
        await warm_factor_calculations()

        # 2단계: 종목 랭킹 캐싱
        await warm_stock_rankings()

        # 3단계: 인기 백테스트 메타데이터 캐싱
        await warm_backtest_results()

        # 4단계: 유명 투자 전략 10개 캐싱 (병렬 처리) - NEW!
        logger.info("\n" + "=" * 80)
        logger.info("📊 Phase 4: Famous Strategies Warming")
        logger.info("=" * 80)
        await warm_famous_strategies()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("🎉🎉🎉 CACHE WARMING COMPLETED 🎉🎉🎉")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"End time: {end_time}")
        logger.info("=" * 80)

        # 캐시 통계 출력
        cache = get_cache()
        stats = await cache.get_cache_stats()
        logger.info(f"📊 Cache Stats after warming:")
        logger.info(f"  - Memory Used: {stats.get('used_memory_human', 'N/A')}")
        logger.info(f"  - Hit Ratio: {stats.get('hit_ratio', 0):.2%}")

    except Exception as e:
        logger.error(f"❌❌❌ CACHE WARMING FAILED: {e}", exc_info=True)
        raise


# 수동 실행용 함수
async def manual_warm_cache():
    """수동으로 캐시 워밍 실행 (테스트용)"""
    await run_cache_warming()


if __name__ == "__main__":
    import asyncio
    asyncio.run(manual_warm_cache())
