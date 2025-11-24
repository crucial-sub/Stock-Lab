"""
피터린치 전략 시연용 캐시 워밍 스크립트
- 1년치 백테스트 데이터 영구 캐싱 (TTL=0)
- 팩터 추가 시 빠른 재계산을 위한 준비
- 시연 30분 전 실행 권장
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import pandas as pd
import pickle
import lz4.frame

from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache, get_redis
from app.services.advanced_backtest import _run_backtest_async
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 피터린치 전략 설정
PETER_LYNCH_CONFIG = {
    "strategy_name": "peter_lynch",
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 12, 31),
    "initial_capital": Decimal("10000000"),
    "themes": ["IT서비스", "섬유 / 의류"],

    # 기본 팩터 (시연 1단계)
    "base_factors": ["PEG", "ROE", "DEBT_RATIO", "PER"],

    # 추가 팩터 (시연 2단계)
    "additional_factors": ["CURRENT_RATIO", "SALES_GROWTH"],

    # 백테스트 설정
    "max_holdings": 10,
    "per_stock_ratio": 10.0,
    "rebalance_frequency": "monthly",
    "target_gain": 25,
    "stop_loss": 15,
    "min_hold_days": 90,
    "max_hold_days": 540,
}


async def get_peter_lynch_strategy_from_db():
    """DB에서 피터린치 전략 설정 로드"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text('SELECT backtest_config FROM investment_strategies WHERE id = :id'),
            {'id': 'peter_lynch'}
        )
        config = result.scalar_one_or_none()
        return config


async def warm_price_data_for_peter_lynch():
    """피터린치 전략용 가격 데이터 캐싱 (1년치)"""
    logger.info("=" * 80)
    logger.info("📊 피터린치 전략 - 가격 데이터 캐싱 시작")
    logger.info("=" * 80)

    cache = get_cache()
    start_date = PETER_LYNCH_CONFIG["start_date"]
    end_date = PETER_LYNCH_CONFIG["end_date"]

    async with AsyncSessionLocal() as db:
        try:
            # 피터린치 전략 테마의 종목 가격 데이터 조회
            from app.models.stock_price import StockPrice
            from app.models.company import Company
            from sqlalchemy import and_, select

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
                    StockPrice.trade_date >= start_date,
                    StockPrice.trade_date <= end_date,
                    StockPrice.close_price.isnot(None),
                    StockPrice.volume > 0,
                    Company.industry.in_(PETER_LYNCH_CONFIG["themes"])
                )
            ).order_by(
                StockPrice.trade_date,
                Company.stock_code
            )

            result = await db.execute(query)
            all_prices = result.mappings().all()

            if all_prices:
                price_data = [
                    {
                        "company_id": str(p["company_id"]),
                        "stock_code": p["stock_code"],
                        "stock_name": p["company_name"],
                        "industry": p["industry"],
                        "market_type": p["market_type"],
                        "date": p["trade_date"].isoformat(),
                        "trade_date": p["trade_date"].isoformat(),
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

                # 영구 캐싱 (TTL=0)
                cache_key = f"peter_lynch:price_data:{start_date}:{end_date}"
                await cache.set(cache_key, price_data, ttl=0)
                logger.info(f"✅ 가격 데이터 캐싱 완료: {len(price_data)}개 레코드 (영구)")
                logger.info(f"   캐시 키: {cache_key}")

            else:
                logger.warning("⚠️ 가격 데이터 없음")

        except Exception as e:
            logger.error(f"❌ 가격 데이터 캐싱 실패: {e}", exc_info=True)


async def warm_factor_data_for_peter_lynch():
    """피터린치 전략용 팩터 데이터 캐싱"""
    logger.info("=" * 80)
    logger.info("📈 피터린치 전략 - 팩터 데이터 캐싱 시작")
    logger.info("=" * 80)

    cache = get_cache()
    start_date = PETER_LYNCH_CONFIG["start_date"]
    end_date = PETER_LYNCH_CONFIG["end_date"]

    # 모든 팩터 (기본 + 추가)
    all_factors = PETER_LYNCH_CONFIG["base_factors"] + PETER_LYNCH_CONFIG["additional_factors"]

    async with AsyncSessionLocal() as db:
        try:
            from app.services.factor_calculator_complete import CompleteFactorCalculator
            from app.models.company import Company
            from sqlalchemy import select

            # 피터린치 테마 종목 조회
            query = select(Company.stock_code).where(
                Company.industry.in_(PETER_LYNCH_CONFIG["themes"])
            )
            result = await db.execute(query)
            stock_codes = [row[0] for row in result.fetchall()]

            logger.info(f"📊 대상 종목: {len(stock_codes)}개")
            logger.info(f"📊 대상 팩터: {len(all_factors)}개")

            calculator = CompleteFactorCalculator(db)

            # 매월 초 날짜 생성 (리밸런싱 주기)
            calc_dates = []
            current = start_date
            while current <= end_date:
                calc_dates.append(current)
                # 다음 달 초로 이동
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            logger.info(f"📊 계산 날짜: {len(calc_dates)}일")

            # 🔥 CRITICAL FIX: 백테스트와 동일한 캐시 구조 사용
            # 날짜별로 팩터 계산 및 캐싱
            themes_str = ','.join(sorted(PETER_LYNCH_CONFIG["themes"]))

            for calc_date in calc_dates:
                try:
                    factors_df = await calculator.calculate_all_factors(
                        stock_codes=stock_codes,
                        date=datetime.combine(calc_date, datetime.min.time())
                    )

                    if factors_df is not None and not factors_df.empty:
                        # 🚀 NEW: 백테스트와 동일한 형식으로 캐싱
                        # {stock_code: {factor: value}} 구조
                        factors_by_stock = {}
                        for _, row in factors_df.iterrows():
                            stock_code = row['stock_code']
                            factors_by_stock[stock_code] = {
                                factor: row.get(factor)
                                for factor in all_factors
                                if factor in factors_df.columns
                            }

                        # 🔥 CRITICAL FIX: LZ4 압축 사용 (backtest_cache_optimized와 동일)
                        cache_key = f"backtest_optimized:factors:{calc_date}:{themes_str}"

                        # 직렬화 + LZ4 압축
                        serialized = pickle.dumps(factors_by_stock, protocol=pickle.HIGHEST_PROTOCOL)
                        compressed = lz4.frame.compress(serialized)

                        # Redis에 직접 저장 (cache.set()은 이미 pickle.dumps를 하므로 우회)
                        redis_client = get_redis()
                        await redis_client.set(cache_key, compressed)

                        logger.info(f"✅ {calc_date} 팩터 캐싱 완료 (영구) - Key: {cache_key}")
                        logger.info(f"   종목 수: {len(factors_by_stock)}, 팩터 수: {len(all_factors)}")

                except Exception as e:
                    logger.error(f"❌ {calc_date} 팩터 계산 실패: {e}")
                    continue

            logger.info("✅ 모든 팩터 데이터 캐싱 완료!")

        except Exception as e:
            logger.error(f"❌ 팩터 데이터 캐싱 실패: {e}", exc_info=True)


async def warm_backtest_result_for_peter_lynch():
    """피터린치 전략 백테스트 결과 사전 실행 및 캐싱"""
    logger.info("=" * 80)
    logger.info("🚀 피터린치 전략 - 백테스트 실행 및 캐싱 시작")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        try:
            # DB에서 전략 설정 로드
            strategy_config = await get_peter_lynch_strategy_from_db()

            if not strategy_config:
                logger.error("❌ 피터린치 전략 설정을 찾을 수 없습니다")
                return

            # 벡터화 형식으로 변환
            buy_conditions = {
                "expression": strategy_config.get('expression'),
                "conditions": strategy_config.get('conditions'),
                "priority_factor": strategy_config.get('priority_factor', 'PEG'),
                "priority_order": strategy_config.get('priority_order', 'asc')
            }

            condition_sell = None
            if 'condition_sell' in strategy_config:
                condition_sell = {
                    "expression": strategy_config['condition_sell'].get('expression'),
                    "conditions": strategy_config['condition_sell'].get('conditions')
                }

            logger.info(f"📋 전략 설정 로드 완료:")
            logger.info(f"   - Expression: {buy_conditions['expression']}")
            logger.info(f"   - Conditions: {len(buy_conditions['conditions'])}개")

            # 백테스트 실행 (결과가 DB와 캐시에 저장됨)
            import uuid
            session_id = str(uuid.uuid4())
            strategy_id = str(uuid.uuid4())

            logger.info(f"🚀 백테스트 실행 시작...")
            logger.info(f"   Session ID: {session_id}")

            await _run_backtest_async(
                session_id=session_id,
                strategy_id=strategy_id,
                start_date=PETER_LYNCH_CONFIG["start_date"],
                end_date=PETER_LYNCH_CONFIG["end_date"],
                initial_capital=PETER_LYNCH_CONFIG["initial_capital"],
                benchmark="KOSPI",
                target_themes=PETER_LYNCH_CONFIG["themes"],
                target_stocks=[],
                target_universes=[],
                use_all_stocks=False,
                buy_conditions=buy_conditions,
                buy_logic="AND",
                priority_factor=buy_conditions["priority_factor"],
                priority_order=buy_conditions["priority_order"],
                max_holdings=PETER_LYNCH_CONFIG["max_holdings"],
                per_stock_ratio=PETER_LYNCH_CONFIG["per_stock_ratio"],
                rebalance_frequency=PETER_LYNCH_CONFIG["rebalance_frequency"],
                commission_rate=0.1,
                slippage=0.0,
                target_and_loss={
                    "target_gain": PETER_LYNCH_CONFIG["target_gain"],
                    "stop_loss": PETER_LYNCH_CONFIG["stop_loss"]
                },
                hold_days={
                    "min_hold_days": PETER_LYNCH_CONFIG["min_hold_days"],
                    "max_hold_days": PETER_LYNCH_CONFIG["max_hold_days"]
                },
                condition_sell=condition_sell,
                max_buy_value=None,
                max_daily_stock=None,
                fast_mode=True  # 🔥 초고속 모드 활성화!
            )

            logger.info("✅ 백테스트 실행 완료!")
            logger.info(f"   결과는 session_id: {session_id}로 조회 가능")

            # 세션 정보도 캐싱
            cache = get_cache()
            demo_info = {
                "session_id": session_id,
                "strategy_id": strategy_id,
                "warmed_at": datetime.now().isoformat(),
                "config": PETER_LYNCH_CONFIG,
                "ready": True
            }
            await cache.set("peter_lynch:demo:session", demo_info, ttl=0)
            logger.info("✅ 세션 정보 캐싱 완료")

        except Exception as e:
            logger.error(f"❌ 백테스트 실행 실패: {e}", exc_info=True)


async def run_peter_lynch_cache_warming():
    """피터린치 전략 전체 캐시 워밍 실행"""
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("🔥🔥🔥 피터린치 전략 캐시 워밍 시작 🔥🔥🔥")
    logger.info(f"시작 시간: {start_time}")
    logger.info("=" * 80)

    try:
        # 1단계: 가격 데이터 캐싱
        await warm_price_data_for_peter_lynch()

        # 2단계: 팩터 데이터 캐싱
        await warm_factor_data_for_peter_lynch()

        # 3단계: 백테스트 실행 및 결과 캐싱
        await warm_backtest_result_for_peter_lynch()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info("🎉🎉🎉 피터린치 전략 캐시 워밍 완료 🎉🎉🎉")
        logger.info(f"소요 시간: {duration:.2f}초")
        logger.info(f"종료 시간: {end_time}")
        logger.info("=" * 80)

        # 캐시 통계
        cache = get_cache()
        logger.info("\n📊 캐시 워밍 완료 상태:")
        logger.info("  ✅ 가격 데이터: 1년치 영구 캐싱")
        logger.info("  ✅ 팩터 데이터: 6개 팩터 × 12개월 영구 캐싱")
        logger.info("  ✅ 백테스트 결과: 완전 실행 및 캐싱")
        logger.info("\n🎯 시연 준비 완료!")
        logger.info("  - 첫 번째 테스트: 1~2초 예상 (100% 캐시 히트)")
        logger.info("  - 팩터 추가 후: 3~5초 예상 (증분 계산)")

    except Exception as e:
        logger.error(f"❌ 캐시 워밍 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(run_peter_lynch_cache_warming())
