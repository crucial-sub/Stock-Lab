#!/usr/bin/env python3
"""
삼성전자만으로 백테스트 간단 테스트
PER 값이 유효한지 확인하고 실제 거래가 발생하는지 검증
"""

import asyncio
import sys
import logging
from datetime import date
from pathlib import Path
from decimal import Decimal

sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_samsung():
    """삼성전자 단일 종목 테스트"""

    logger.info("=" * 80)
    logger.info("삼성전자 백테스트 테스트")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)

        import uuid
        backtest_id = uuid.uuid4()

        # 매우 간단한 조건: PBR만 사용
        buy_conditions = [
            {"factor": "PBR", "operator": ">=", "value": 0.0},  # PBR >= 0 (거의 모든 종목)
        ]

        logger.info(f"백테스트 ID: {backtest_id}")
        logger.info(f"조건: PBR >= 0.0 (완화된 조건)")
        logger.info(f"대상: 삼성전자(005930)")
        logger.info(f"기간: 2024-06-01 ~ 2024-12-31 (7개월)")
        logger.info("")

        try:
            result = await engine.run_backtest(
                backtest_id=backtest_id,
                start_date=date(2024, 6, 1),
                end_date=date(2024, 12, 31),
                initial_capital=Decimal("10000000"),
                benchmark="KOSPI",
                target_themes=[],  # 테마 없음
                target_stocks=["005930"],  # 삼성전자만
                buy_conditions=buy_conditions,
                sell_conditions=[],
                condition_sell={
                    "profit_target": 10.0,  # 10% 익절
                    "stop_loss": -5.0  # 5% 손절
                },
                rebalance_frequency="WEEKLY",
                max_positions=1,
                position_sizing="equal",
            )

            logger.info("=" * 80)
            logger.info("✅ 백테스트 완료!")
            logger.info("=" * 80)

            # Pydantic 모델로 접근
            logger.info(f"백테스트 ID: {result.backtest_id}")
            logger.info("")

            logger.info("📊 통계 결과:")
            logger.info(f"  최종 자산: {result.statistics.final_capital:,.0f}원")
            logger.info(f"  총 수익률: {result.statistics.total_return:.2f}%")
            logger.info(f"  연환산 수익률: {result.statistics.annualized_return:.2f}%")
            logger.info(f"  최대 낙폭(MDD): {result.statistics.max_drawdown:.2f}%")
            logger.info(f"  샤프비율: {result.statistics.sharpe_ratio:.2f}")
            logger.info("")

            logger.info("📈 거래 통계:")
            logger.info(f"  총 거래: {result.statistics.total_trades}건")
            logger.info(f"  승리 거래: {result.statistics.winning_trades}건")
            logger.info(f"  패배 거래: {result.statistics.losing_trades}건")
            logger.info(f"  승률: {result.statistics.win_rate:.2f}%")
            logger.info("")

            if result.trades:
                logger.info(f"💰 거래 내역 ({len(result.trades)}건):")
                for i, trade in enumerate(result.trades[:10], 1):
                    logger.info(f"  {i}. {trade.stock_name} ({trade.stock_code})")
                    logger.info(f"     매수: {trade.buy_date} @ {trade.buy_price:,.0f}원")
                    logger.info(f"     매도: {trade.sell_date} @ {trade.sell_price:,.0f}원")
                    logger.info(f"     손익: {trade.profit:,.0f}원 ({trade.profit_rate:.2f}%)")
                    logger.info("")
            else:
                logger.warning("⚠️  거래 내역이 없습니다!")

            logger.info("=" * 80)

            # 검증
            if result.statistics.total_trades > 0:
                logger.info("✅ 테스트 성공: 거래 발생 확인")
            else:
                logger.warning("⚠️  거래 미발생: 조건 또는 데이터 문제")

            return result

        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    asyncio.run(test_samsung())
