"""
백테스트 최적화 통합 예제
====================================

이 파일은 두 가지 주요 최적화를 실제 백테스트 서비스에 통합하는 방법을 보여줍니다:

1. 재무 데이터 장기 캐싱 (financial_cache.py)
2. 조건식 사전 분석 및 선택적 팩터 계산 (factor_dependency_analyzer.py)
"""

from datetime import date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
import polars as pl
import logging

from app.services.financial_cache import financial_cache
from app.services.factor_dependency_analyzer import factor_analyzer
from app.services.backtest_extreme_optimized import ExtremeOptimizer
from app.schemas.backtest import BacktestCreateRequest, BacktestResult

logger = logging.getLogger(__name__)


async def run_optimized_backtest_example(
    db: AsyncSession,
    request: BacktestCreateRequest,
    stock_universe: List[str]
) -> BacktestResult:
    """
    최적화가 적용된 백테스트 실행 예제

    Args:
        db: 데이터베이스 세션
        request: 백테스트 요청 (조건 포함)
        stock_universe: 종목 유니버스

    Returns:
        BacktestResult
    """

    start_date = request.start_date
    end_date = request.end_date

    logger.info(f"🚀 최적화 백테스트 시작: {start_date} ~ {end_date}")
    logger.info(f"종목 수: {len(stock_universe)}")

    # ========================================================================
    # OPTIMIZATION 1: 재무 데이터 장기 캐싱
    # ========================================================================

    logger.info("=" * 80)
    logger.info("최적화 1: 재무 데이터 Redis 캐싱 (3개월 TTL)")
    logger.info("=" * 80)

    # 필요한 연도 범위 계산 (1년 전부터)
    years_needed = [
        str(start_date.year - 1),
        str(start_date.year),
        str(end_date.year)
    ]
    years_needed = sorted(list(set(years_needed)))  # 중복 제거

    logger.info(f"📅 재무 데이터 조회 연도: {years_needed}")

    # 캐시를 통한 재무 데이터 조회 (첫 실행은 DB 조회, 이후는 Redis 캐시)
    financial_data_by_year = {}

    for year in years_needed:
        logger.info(f"  - {year}년 데이터 조회 중...")

        # 사업보고서 (연결 재무제표)
        annual_data = await financial_cache.get_financial_statements_cached(
            db=db,
            stock_codes=stock_universe,
            fiscal_year=year,
            report_code='11011'  # 사업보고서
        )

        financial_data_by_year[year] = annual_data

        logger.info(f"    ✅ {year}년: {len(annual_data)}개 종목")

    # 재무 데이터를 Polars DataFrame으로 변환 (backtest_extreme_optimized.py 형식)
    financial_records = []

    for year, year_data in financial_data_by_year.items():
        for stock_code, statements in year_data.items():
            # 재무제표에서 필요한 항목 추출
            bs = statements.get('balance_sheet', {})
            is_data = statements.get('income_statement', {})
            cf = statements.get('cashflow_statement', {})

            record = {
                'stock_code': stock_code,
                'fiscal_year': int(year),
                # 손익계산서
                '매출액': is_data.get('매출액', {}).get('thstrm_amount'),
                '영업이익': is_data.get('영업이익', {}).get('thstrm_amount'),
                '당기순이익': is_data.get('당기순이익', {}).get('thstrm_amount'),
                '매출총이익': is_data.get('매출총이익', {}).get('thstrm_amount'),
                '매출원가': is_data.get('매출원가', {}).get('thstrm_amount'),
                # 재무상태표
                '자산총계': bs.get('자산총계', {}).get('thstrm_amount'),
                '자본총계': bs.get('자본총계', {}).get('thstrm_amount'),
                '부채총계': bs.get('부채총계', {}).get('thstrm_amount'),
                '유동자산': bs.get('유동자산', {}).get('thstrm_amount'),
                '유동부채': bs.get('유동부채', {}).get('thstrm_amount'),
                '현금및현금성자산': bs.get('현금및현금성자산', {}).get('thstrm_amount'),
                # 현금흐름표
                '영업활동현금흐름': cf.get('영업활동현금흐름', {}).get('thstrm_amount'),
                '투자활동현금흐름': cf.get('투자활동현금흐름', {}).get('thstrm_amount'),
                '재무활동현금흐름': cf.get('재무활동현금흐름', {}).get('thstrm_amount'),
            }

            financial_records.append(record)

    financial_pl = pl.DataFrame(financial_records)
    logger.info(f"✅ 재무 데이터 변환 완료: {len(financial_records)}개 레코드")

    # ========================================================================
    # OPTIMIZATION 2: 조건식 사전 분석 및 선택적 팩터 계산
    # ========================================================================

    logger.info("=" * 80)
    logger.info("최적화 2: 조건식 분석 및 선택적 팩터 계산")
    logger.info("=" * 80)

    # 사용자의 매수 조건 추출
    buy_conditions = request.buy_conditions if request.buy_conditions else []
    buy_expression = request.buy_expression

    logger.info(f"📋 매수 조건 수: {len(buy_conditions)}")

    # 조건식에서 필요한 팩터 추출
    required_factors = factor_analyzer.extract_factors_from_conditions(
        conditions=buy_conditions,
        buy_expression=buy_expression
    )

    logger.info(f"🔍 필요 팩터: {sorted(required_factors) if required_factors else '모든 팩터'}")

    # 팩터 계산 마스크 생성
    compute_mask = factor_analyzer.get_factor_compute_mask(required_factors)

    # 복잡도 분석
    complexity = factor_analyzer.analyze_condition_complexity(
        conditions=buy_conditions,
        buy_expression=buy_expression
    )

    logger.info(f"📊 팩터 사용: {complexity['factor_count']}/{complexity['total_factors']}개")
    logger.info(f"⚡ 예상 속도 향상: {complexity['estimated_speedup']:.1f}x")

    if complexity['optimization_enabled']:
        logger.info("✅ 선택적 팩터 계산 최적화 활성화")
    else:
        logger.info("ℹ️ 모든 팩터 계산 (최적화 미적용)")

    # ========================================================================
    # 팩터 계산 (최적화 적용)
    # ========================================================================

    logger.info("=" * 80)
    logger.info("팩터 계산 시작 (최적화 적용)")
    logger.info("=" * 80)

    # 여기서는 price_pl과 stock_prices_pl을 이미 로드했다고 가정
    # 실제로는 DB에서 가격 데이터를 조회해야 함
    # (이 예제에서는 생략)

    # 거래일 리스트 생성
    trading_dates = []  # 실제로는 영업일 기준으로 생성
    current = start_date
    while current <= end_date:
        trading_dates.append(current)
        current += timedelta(days=1)

    logger.info(f"📅 거래일 수: {len(trading_dates)}")

    # ExtremeOptimizer 초기화
    optimizer = ExtremeOptimizer()

    # 🚀 최적화된 팩터 계산 실행
    # compute_mask를 전달하여 필요한 팩터만 계산
    """
    factor_results = optimizer.calculate_all_indicators_batch_extreme(
        price_pl=price_pl,  # OHLCV 데이터 (Polars DataFrame)
        financial_pl=financial_pl,  # 재무 데이터 (위에서 캐시로 로드)
        calc_dates=trading_dates,
        stock_prices_pl=stock_prices_pl,  # 시가총액 데이터
        compute_mask=compute_mask  # ⚡ 최적화: 필요한 팩터만 계산
    )

    logger.info(f"✅ 팩터 계산 완료: {len(factor_results)}개 날짜")
    """

    # ========================================================================
    # 백테스트 실행 (이후 로직)
    # ========================================================================

    # 이 시점에서 factor_results를 사용하여 매수/매도 로직 실행
    # 포트폴리오 시뮬레이션, 성과 계산 등

    logger.info("=" * 80)
    logger.info("✅ 최적화 백테스트 완료")
    logger.info("=" * 80)

    # BacktestResult 반환 (실제 구현에서는 상세 결과 포함)
    # return backtest_result


async def demonstrate_cache_warming():
    """
    캐시 워밍업 예제
    자주 사용되는 데이터를 미리 캐싱하여 첫 실행 시 성능 향상
    """
    logger.info("🔥 캐시 워밍업 시작")

    from app.core.database import get_db

    async for db in get_db():
        # 주요 종목들의 최근 3년 재무 데이터 미리 로드
        major_stocks = ['005930', '000660', '035420', '051910', '035720']  # 삼성전자, SK하이닉스 등

        current_year = 2024
        years = [str(current_year - i) for i in range(3)]

        for year in years:
            await financial_cache.get_financial_statements_cached(
                db=db,
                stock_codes=major_stocks,
                fiscal_year=year,
                report_code='11011'
            )
            logger.info(f"  ✅ {year}년 데이터 캐싱 완료")

        logger.info("🔥 캐시 워밍업 완료")
        break


async def demonstrate_cache_invalidation():
    """
    캐시 무효화 예제
    재무 데이터가 업데이트될 때 사용
    """
    logger.info("🗑️ 캐시 무효화 예제")

    # 특정 종목의 특정 연도만 무효화
    await financial_cache.invalidate_financial_cache(
        stock_code='005930',
        fiscal_year='2023'
    )
    logger.info("  ✅ 삼성전자 2023년 캐시 무효화")

    # 특정 연도 전체 무효화 (모든 종목)
    await financial_cache.invalidate_financial_cache(
        fiscal_year='2024'
    )
    logger.info("  ✅ 2024년 전체 캐시 무효화")

    # 전체 캐시 무효화 (주의: 신중하게 사용)
    # await financial_cache.invalidate_financial_cache()
    # logger.info("  ✅ 전체 캐시 무효화")


def demonstrate_factor_analysis():
    """
    팩터 분석 예제
    다양한 조건식에서 팩터 추출 시연
    """
    logger.info("🔍 팩터 분석 예제")

    # 예제 1: 단순 조건
    simple_conditions = [
        {'factor': 'PER', 'operator': '<', 'value': 10},
        {'factor': 'PBR', 'operator': '<', 'value': 1},
    ]

    factors1 = factor_analyzer.extract_factors_from_conditions(
        conditions=simple_conditions
    )
    logger.info(f"  예제 1 (단순): {factors1}")

    # 예제 2: 논리식 조건
    complex_expression = {
        'expression': '(PER < 10 and PBR < 1) or (ROE > 15 and DEBT_RATIO < 50)',
        'conditions': [
            {'id': 'A', 'factor': 'PER', 'operator': '<', 'value': 10},
            {'id': 'B', 'factor': 'PBR', 'operator': '<', 'value': 1},
            {'id': 'C', 'factor': 'ROE', 'operator': '>', 'value': 15},
            {'id': 'D', 'factor': 'DEBT_RATIO', 'operator': '<', 'value': 50},
        ]
    }

    factors2 = factor_analyzer.extract_factors_from_conditions(
        buy_expression=complex_expression
    )
    logger.info(f"  예제 2 (복잡): {factors2}")

    # 복잡도 분석
    analysis = factor_analyzer.analyze_condition_complexity(
        buy_expression=complex_expression
    )
    logger.info(f"  복잡도 분석: {analysis}")


if __name__ == "__main__":
    """
    이 스크립트를 직접 실행하여 예제를 테스트할 수 있습니다.

    실행 방법:
    python INTEGRATION_EXAMPLE.py
    """
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 팩터 분석 예제 (동기 함수)
    demonstrate_factor_analysis()

    # 비동기 예제들
    # asyncio.run(demonstrate_cache_warming())
    # asyncio.run(demonstrate_cache_invalidation())
