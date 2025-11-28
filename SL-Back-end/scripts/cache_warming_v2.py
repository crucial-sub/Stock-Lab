#!/usr/bin/env python3
"""
백테스트 30초 이내 최적화를 위한 캐시 워밍 스크립트 v2

전략:
1. backtest.py의 기존 캐시 구조를 활용
2. 대표 백테스트를 실행하여 분기별 팩터 캐시를 채움
3. 매일 03:00 KST에 스케줄 실행

캐시 구조 (backtest.py 호환):
- price_data:all:{start_date}:{end_date} - 전체 종목 가격 데이터
- backtest_factors_v2 + {quarter, version} - 분기별 전체 팩터
"""

import asyncio
import sys
import os
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from decimal import Decimal
from uuid import uuid4
import time

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 설정 및 모듈 임포트 전에 환경 변수 설정
os.environ.setdefault('ENABLE_CACHE', 'True')

from app.core.database import AsyncSessionLocal
from app.core.cache import get_cache
from app.services.backtest import BacktestEngine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 대표 전략 정의 (캐시 워밍용) - migrate_strategies.py 유명전략 전체 포함
# ============================================================================
WARMING_STRATEGIES = [
    # 1. 급등주 전략 (surge_stocks)
    {
        'name': 'surge_stocks',
        'description': '급등주 전략 - 시가총액 70억 이상',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({MARKET_CAP})', 'inequality': '>', 'exp_right_side': 7000000000}
        ]
    },
    # 2. 꾸준한 성장주 전략 (steady_growth)
    {
        'name': 'steady_growth',
        'description': '꾸준한 성장주 - 매출성장, ROE, 부채비율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({REVENUE_GROWTH_1Y})', 'inequality': '>', 'exp_right_side': -5},
            {'name': 'B', 'exp_left_side': '기본값({OPERATING_INCOME_GROWTH_YOY})', 'inequality': '>', 'exp_right_side': -5},
            {'name': 'C', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '<', 'exp_right_side': 120},
            {'name': 'D', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 8}
        ]
    },
    # 3. 피터 린치 전략 (peter_lynch)
    {
        'name': 'peter_lynch',
        'description': '피터 린치 - PER, PEG, 부채비율, ROE, ROA',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 40},
            {'name': 'B', 'exp_left_side': '기본값({PEG})', 'inequality': '>', 'exp_right_side': 0},
            {'name': 'C', 'exp_left_side': '기본값({PEG})', 'inequality': '<', 'exp_right_side': 2.0},
            {'name': 'D', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '<', 'exp_right_side': 180},
            {'name': 'E', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 3},
            {'name': 'F', 'exp_left_side': '기본값({ROA})', 'inequality': '>', 'exp_right_side': 0.5}
        ]
    },
    # 4. 워렌 버핏 전략 (warren_buffett)
    {
        'name': 'warren_buffett',
        'description': '워렌 버핏 - ROE, 유동비율, PER, PBR, 부채비율, 순이익증가율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'B', 'exp_left_side': '기본값({CURRENT_RATIO})', 'inequality': '>', 'exp_right_side': 1.2},
            {'name': 'C', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 20},
            {'name': 'D', 'exp_left_side': '기본값({PBR})', 'inequality': '<', 'exp_right_side': 2.0},
            {'name': 'E', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '<', 'exp_right_side': 170},
            {'name': 'F', 'exp_left_side': '기본값({EARNINGS_GROWTH_1Y})', 'inequality': '>', 'exp_right_side': 5}
        ]
    },
    # 5. 윌리엄 오닐 전략 (william_oneil)
    {
        'name': 'william_oneil',
        'description': '윌리엄 오닐 - EPS성장률, ROE, 52주 신고가 근접',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({EARNINGS_GROWTH_1Y})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'B', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'C', 'exp_left_side': '기본값({DISTANCE_FROM_52W_HIGH})', 'inequality': '>', 'exp_right_side': -25}
        ]
    },
    # 6. 빌 애크먼 전략 (bill_ackman)
    {
        'name': 'bill_ackman',
        'description': '빌 애크먼 - ROIC, PER, PBR, 부채비율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({ROIC})', 'inequality': '>', 'exp_right_side': 10},
            {'name': 'B', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 22},
            {'name': 'C', 'exp_left_side': '기본값({PBR})', 'inequality': '<', 'exp_right_side': 2.5},
            {'name': 'D', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '>', 'exp_right_side': 100}
        ]
    },
    # 7. 찰리 멍거 전략 (charlie_munger)
    {
        'name': 'charlie_munger',
        'description': '찰리 멍거 - ROIC, PER, PBR, ROE, 매출성장률, 부채비율, 유동비율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({ROIC})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'B', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 14},
            {'name': 'C', 'exp_left_side': '기본값({PBR})', 'inequality': '<', 'exp_right_side': 2.0},
            {'name': 'D', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'E', 'exp_left_side': '기본값({REVENUE_GROWTH_1Y})', 'inequality': '>', 'exp_right_side': 10},
            {'name': 'F', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '<', 'exp_right_side': 70},
            {'name': 'G', 'exp_left_side': '기본값({CURRENT_RATIO})', 'inequality': '>', 'exp_right_side': 1.5}
        ]
    },
    # 8. 글렌 웰링 전략 (glenn_welling)
    {
        'name': 'glenn_welling',
        'description': '글렌 웰링 - EV/EBITDA, ROIC, PBR, PSR, PEG',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({EV_EBITDA})', 'inequality': '<', 'exp_right_side': 10},
            {'name': 'B', 'exp_left_side': '기본값({ROIC})', 'inequality': '<', 'exp_right_side': 12},
            {'name': 'C', 'exp_left_side': '기본값({PBR})', 'inequality': '<', 'exp_right_side': 2.0},
            {'name': 'D', 'exp_left_side': '기본값({PSR})', 'inequality': '<', 'exp_right_side': 2.0},
            {'name': 'E', 'exp_left_side': '기본값({PEG})', 'inequality': '>', 'exp_right_side': 0},
            {'name': 'F', 'exp_left_side': '기본값({PEG})', 'inequality': '<', 'exp_right_side': 1.2}
        ]
    },
    # 9. 캐시 우드 전략 (cathie_wood)
    {
        'name': 'cathie_wood',
        'description': '캐시 우드 - PEG, PSR, 매출성장률, 유동비율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({PEG})', 'inequality': '>', 'exp_right_side': 0},
            {'name': 'B', 'exp_left_side': '기본값({PEG})', 'inequality': '<', 'exp_right_side': 3},
            {'name': 'C', 'exp_left_side': '기본값({PSR})', 'inequality': '<', 'exp_right_side': 30},
            {'name': 'D', 'exp_left_side': '기본값({REVENUE_GROWTH_1Y})', 'inequality': '>', 'exp_right_side': 10},
            {'name': 'E', 'exp_left_side': '기본값({CURRENT_RATIO})', 'inequality': '>', 'exp_right_side': 1.2}
        ]
    },
    # 10. 글렌 그린버그 전략 (glenn_greenberg)
    {
        'name': 'glenn_greenberg',
        'description': '글렌 그린버그 - PER, ROIC, 부채비율',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 20},
            {'name': 'B', 'exp_left_side': '기본값({ROIC})', 'inequality': '>', 'exp_right_side': 12},
            {'name': 'C', 'exp_left_side': '기본값({DEBT_RATIO})', 'inequality': '<', 'exp_right_side': 70}
        ]
    },
    # 11. 기본 저PER_고ROE (범용 캐싱용)
    {
        'name': '저PER_고ROE',
        'description': 'PER 낮고 ROE 높은 가치주 (범용)',
        'buy_conditions': [
            {'name': 'A', 'exp_left_side': '기본값({PER})', 'inequality': '<', 'exp_right_side': 10},
            {'name': 'B', 'exp_left_side': '기본값({ROE})', 'inequality': '>', 'exp_right_side': 10}
        ]
    }
]


async def run_warming_backtest(strategy: Dict[str, Any], start_date: date, end_date: date) -> Dict[str, Any]:
    """
    캐시 워밍을 위한 백테스트 실행
    """
    logger.info(f"  {strategy['name']} 백테스트 시작...")
    start_time = time.time()

    try:
        async with AsyncSessionLocal() as db:
            engine = BacktestEngine(db=db)
            engine.skip_db_save = True  # DB 저장 스킵 (캐시만 채움)

            result = await engine.run_backtest(
                backtest_id=uuid4(),
                buy_conditions=strategy['buy_conditions'],
                sell_conditions=[],
                start_date=start_date,
                end_date=end_date,
                target_and_loss={'target_gain': 20, 'stop_loss': 10},
                hold_days={
                    'min_hold_days': 5,
                    'max_hold_days': 60,
                    'sell_price_basis': '시가',
                    'sell_price_offset': 0
                },
                initial_capital=Decimal('10000000'),
                rebalance_frequency='DAILY',
                max_positions=10,
                position_sizing='EQUAL_WEIGHT',
                benchmark='KOSPI',
                commission_rate=0.00015,
                slippage=0.001,
                per_stock_ratio=0.1,
                max_daily_stock=3
            )

            elapsed = time.time() - start_time

            if result and result.statistics:
                return {
                    'strategy': strategy['name'],
                    'success': True,
                    'elapsed': elapsed,
                    'total_return': result.statistics.total_return,
                    'total_trades': result.statistics.total_trades
                }
            else:
                return {
                    'strategy': strategy['name'],
                    'success': False,
                    'elapsed': elapsed,
                    'error': 'No result returned'
                }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"  {strategy['name']} 백테스트 실패: {e}")
        return {
            'strategy': strategy['name'],
            'success': False,
            'elapsed': elapsed,
            'error': str(e)
        }


async def warm_price_data_cache(start_year: int = 2020, end_year: int = 2025) -> int:
    """
    가격 데이터 캐시 워밍 - 백테스트 실행 시 자동 캐싱되므로 스킵

    참고: 가격 데이터는 backtest.py의 _load_price_data에서 자동으로 캐싱됩니다.
    이 함수는 호환성을 위해 유지하지만, 실제 캐싱은 백테스트 실행을 통해 수행됩니다.
    """
    logger.info("=" * 80)
    logger.info("1. 가격 데이터 캐시 워밍")
    logger.info(f"   기간: {start_year} ~ {end_year}")
    logger.info("   ⏭️ 가격 데이터는 백테스트 실행 시 자동 캐싱됩니다 (스킵)")
    logger.info("=" * 80)

    # 가격 데이터 캐싱은 백테스트 실행 시 자동으로 수행되므로 스킵
    # backtest.py의 _load_price_data에서 price_data:{start}:{end} 키로 캐싱됨
    return 0


async def warm_factor_cache_via_backtest(
    start_date: date = None,
    end_date: date = None
) -> Dict[str, Any]:
    """
    백테스트 실행을 통한 팩터 캐시 워밍
    """
    if start_date is None:
        # 최근 1년
        end_date = date.today() - timedelta(days=1)
        start_date = date(end_date.year - 1, end_date.month, end_date.day)

    logger.info("=" * 80)
    logger.info("2. 팩터 캐시 워밍 (백테스트 실행)")
    logger.info(f"   기간: {start_date} ~ {end_date}")
    logger.info(f"   전략 수: {len(WARMING_STRATEGIES)}개")
    logger.info("=" * 80)

    results = []

    for strategy in WARMING_STRATEGIES:
        result = await run_warming_backtest(strategy, start_date, end_date)
        results.append(result)

        if result['success']:
            logger.info(f"    {result['strategy']}: {result['elapsed']:.1f}초, 수익률 {result['total_return']:.2f}%")
        else:
            logger.warning(f"    {result['strategy']}: 실패 - {result.get('error', 'Unknown')}")

    successful = sum(1 for r in results if r['success'])
    total_time = sum(r['elapsed'] for r in results)

    logger.info(f"   완료: {successful}/{len(results)} 성공, 총 {total_time:.1f}초")

    return {
        'total': len(results),
        'successful': successful,
        'total_time': total_time,
        'results': results
    }


async def run_cache_warming():
    """전체 캐시 워밍 실행 - 동적 날짜 기준"""
    start_time = datetime.now()

    # 동적 날짜 계산: 현재 날짜 기준 최근 1년, 2년
    today = date.today()
    # 어제 날짜를 end_date로 사용 (오늘 데이터는 아직 완전하지 않을 수 있음)
    end_date_dynamic = today - timedelta(days=1)

    # 최근 1년: 오늘 - 1년
    start_date_1y = date(end_date_dynamic.year - 1, end_date_dynamic.month, end_date_dynamic.day)

    # 최근 2년: 오늘 - 2년
    start_date_2y = date(end_date_dynamic.year - 2, end_date_dynamic.month, end_date_dynamic.day)

    # 가격 데이터 연도 범위: 2020년부터 현재 연도까지
    current_year = today.year

    logger.info("=" * 80)
    logger.info("백테스트 최적화 캐시 워밍 v2 시작")
    logger.info(f"   시작 시간: {start_time}")
    logger.info(f"   현재 날짜: {today}")
    logger.info(f"   1년 기간: {start_date_1y} ~ {end_date_dynamic}")
    logger.info(f"   2년 기간: {start_date_2y} ~ {end_date_dynamic}")
    logger.info("=" * 80)

    results = {}

    try:
        # 1. 가격 데이터 캐싱 (2020년 ~ 현재 연도)
        price_count = await warm_price_data_cache(start_year=2020, end_year=current_year)
        results["price_data"] = price_count

        # 2. 백테스트 실행을 통한 팩터 캐시 워밍
        # 2-1. 최근 1년 (동적 계산)
        factor_results_1y = await warm_factor_cache_via_backtest(
            start_date=start_date_1y,
            end_date=end_date_dynamic
        )
        results["factors_1y"] = factor_results_1y

        # 2-2. 최근 2년 (동적 계산)
        factor_results_2y = await warm_factor_cache_via_backtest(
            start_date=start_date_2y,
            end_date=end_date_dynamic
        )
        results["factors_2y"] = factor_results_2y

    except Exception as e:
        logger.error(f"캐시 워밍 중 오류 발생: {e}", exc_info=True)
        raise

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    logger.info("=" * 80)
    logger.info("캐시 워밍 완료!")
    logger.info(f"   소요 시간: {elapsed:.2f}초")
    logger.info("=" * 80)
    logger.info("캐싱 결과:")
    logger.info(f"   가격 데이터: {results.get('price_data', 0):,}개 레코드")
    logger.info(f"   1년 팩터 ({start_date_1y} ~ {end_date_dynamic}): {results.get('factors_1y', {}).get('successful', 0)}/{results.get('factors_1y', {}).get('total', 0)} 전략")
    logger.info(f"   2년 팩터 ({start_date_2y} ~ {end_date_dynamic}): {results.get('factors_2y', {}).get('successful', 0)}/{results.get('factors_2y', {}).get('total', 0)} 전략")
    logger.info("=" * 80)

    return results


async def scheduled_warming():
    """스케줄러에서 호출되는 워밍 함수 (03:00 KST)"""
    try:
        import pytz
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst)
    except ImportError:
        now = datetime.now()

    logger.info(f"스케줄된 캐시 워밍 시작: {now}")

    try:
        await run_cache_warming()
        logger.info("스케줄된 캐시 워밍 완료")
    except Exception as e:
        logger.error(f"스케줄된 캐시 워밍 실패: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_cache_warming())
