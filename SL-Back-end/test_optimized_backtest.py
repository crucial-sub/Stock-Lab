#!/usr/bin/env python3
"""
최적화된 백테스트 테스트
병렬 처리, 선택적 팩터 계산, Redis 캐싱이 적용된 백테스트를 테스트합니다.
"""

import asyncio
import sys
import logging
import time
from datetime import date
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine
from app.schemas.backtest import BacktestCondition

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_optimized_backtest():
    """최적화된 백테스트 테스트"""

    logger.info("=" * 80)
    logger.info("최적화된 백테스트 테스트 시작")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db)

        # 테스트 설정
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        # 매수 조건 (PBR < 5)
        buy_conditions = [{
            "exp_left_side": "기본값({PBR})",
            "inequality": "<",
            "exp_right_side": 5.0,
            "priority_factor": "PER"
        }]

        # 매도 조건
        sell_conditions = [{
            "profit_target": 10,  # 10% 익절
            "stop_loss": -5       # 5% 손절
        }]

        logger.info(f"기간: {start_date} ~ {end_date}")
        logger.info(f"매수 조건: PBR < 5")
        logger.info(f"우선순위: PER (오름차순)")
        logger.info(f"매도 조건: 익절 10%, 손절 -5%")

        try:
            start_time = time.time()

            # 백테스트 실행
            result = await engine.run_backtest(
                backtest_id=uuid4(),
                buy_conditions=buy_conditions,
                sell_conditions=sell_conditions,
                start_date=start_date,
                end_date=end_date,
                initial_capital=Decimal("100000000"),  # 1억원
                rebalance_frequency="MONTHLY",
                max_positions=20,
                position_sizing="EQUAL_WEIGHT",
                benchmark="KOSPI",
                commission_rate=0.00015,
                slippage=0.001,
                target_themes=[],  # 전체 종목
                target_stocks=["005930", "000660", "035720", "207940", "005380"]  # 주요 종목만
            )

            elapsed = time.time() - start_time

            logger.info("=" * 80)
            logger.info(f"✅ 백테스트 완료! (소요시간: {elapsed:.1f}초)")
            logger.info(f"최종 수익률: {result.statistics.total_return:.2f}%")
            logger.info(f"샤프 비율: {result.statistics.sharpe_ratio:.2f}")
            logger.info(f"최대 낙폭: {result.statistics.max_drawdown:.2f}%")
            logger.info(f"승률: {result.statistics.win_rate:.2f}%")
            logger.info(f"총 거래 횟수: {result.statistics.total_trades}")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error(f"❌ 백테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            return None


async def compare_performance():
    """기존 방식과 최적화된 방식의 성능 비교"""

    logger.info("=" * 80)
    logger.info("성능 비교 테스트")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        # 테스트 데이터
        start_date = date(2024, 10, 1)
        end_date = date(2024, 12, 31)

        # 가격 및 재무 데이터 로드 (공통)
        from app.services.backtest import BacktestEngine
        engine = BacktestEngine(db)

        price_data = await engine._load_price_data(
            start_date, end_date,
            target_themes=[],
            target_stocks=["005930", "000660"]
        )

        financial_data = await engine._load_financial_data(
            start_date, end_date
        )

        # 매수 조건 설정
        buy_conditions = [
            BacktestCondition(
                exp_left_side="기본값({PBR})",
                inequality="<",
                exp_right_side=5.0
            )
        ]
        priority_factor = "PER"

        # 1. 기존 방식 (모든 팩터 계산)
        logger.info("\n[기존 방식] 모든 팩터 계산 중...")
        start_time = time.time()

        # 최적화 없이 호출 (buy_conditions와 priority_factor를 None으로)
        factor_df_old = await engine._calculate_all_factors_optimized(
            price_data, financial_data,
            start_date, end_date,
            buy_conditions=None,  # 모든 팩터 계산
            priority_factor=None
        )

        old_time = time.time() - start_time
        logger.info(f"기존 방식 완료: {old_time:.2f}초, {len(factor_df_old)}개 레코드")

        # 2. 최적화된 방식 (선택적 팩터만 계산)
        logger.info("\n[최적화 방식] 필요한 팩터만 계산 중...")
        start_time = time.time()

        factor_df_new = await engine._calculate_all_factors_optimized(
            price_data, financial_data,
            start_date, end_date,
            buy_conditions=buy_conditions,
            priority_factor=priority_factor
        )

        new_time = time.time() - start_time
        logger.info(f"최적화 방식 완료: {new_time:.2f}초, {len(factor_df_new)}개 레코드")

        # 결과 비교
        improvement = (old_time - new_time) / old_time * 100 if old_time > 0 else 0
        speedup = old_time / new_time if new_time > 0 else 0

        logger.info("=" * 80)
        logger.info("📊 성능 비교 결과")
        logger.info(f"기존 방식: {old_time:.2f}초")
        logger.info(f"최적화 방식: {new_time:.2f}초")
        logger.info(f"성능 개선: {improvement:.1f}%")
        logger.info(f"속도 향상: {speedup:.1f}배")
        logger.info("=" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        # 성능 비교 모드
        asyncio.run(compare_performance())
    else:
        # 일반 테스트 모드
        asyncio.run(test_optimized_backtest())