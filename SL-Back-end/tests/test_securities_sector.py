#!/usr/bin/env python3
"""
증권 테마 백테스트 통합 테스트
전체 로직 검증 및 매매내역 확인
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

async def test_securities_sector():
    """증권 테마 전체 백테스트 테스트"""

    logger.info("=" * 80)
    logger.info("증권 테마 백테스트 통합 테스트")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)

        import uuid
        backtest_id = uuid.uuid4()

        # 테스트 조건: PER >= 0 (완화된 조건으로 거래 발생 확인)
        buy_conditions = [
            {"factor": "PER", "operator": ">=", "value": 0.0},
        ]

        logger.info(f"백테스트 ID: {backtest_id}")
        logger.info(f"조건: PER >= 0.0 (NaN 아닌 모든 종목)")
        logger.info(f"대상: 증권 테마 (전체 증권 종목)")
        logger.info(f"기간: 2024-01-01 ~ 2024-06-30 (6개월)")
        logger.info(f"초기자본: 50,000,000원")
        logger.info(f"리밸런싱: 주간 (WEEKLY)")
        logger.info(f"최대포지션: 5개")
        logger.info("")

        try:
            result = await engine.run_backtest(
                backtest_id=backtest_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 6, 30),
                initial_capital=Decimal("50000000"),
                benchmark="KOSPI",
                target_themes=["증권"],  # 증권 테마
                target_stocks=[],
                buy_conditions=buy_conditions,
                sell_conditions=[],
                condition_sell={
                    "profit_target": 20.0,  # 20% 익절
                    "stop_loss": -10.0  # 10% 손절
                },
                rebalance_frequency="WEEKLY",
                max_positions=5,
                position_sizing="equal",
            )

            logger.info("=" * 80)
            logger.info("✅ 백테스트 완료!")
            logger.info("=" * 80)

            # Pydantic 모델로 접근
            logger.info(f"백테스트 ID: {result.backtest_id}")
            logger.info("")

            logger.info("📊 통계 결과:")
            logger.info(f"  초기 자본: {result.statistics.initial_capital:,.0f}원")
            logger.info(f"  최종 자산: {result.statistics.final_capital:,.0f}원")
            logger.info(f"  총 수익률: {result.statistics.total_return:.2f}%")
            logger.info(f"  연환산 수익률: {result.statistics.annualized_return:.2f}%")
            logger.info(f"  최대 낙폭(MDD): {result.statistics.max_drawdown:.2f}%")
            logger.info(f"  변동성: {result.statistics.volatility:.2f}%")
            logger.info(f"  샤프비율: {result.statistics.sharpe_ratio:.2f}")
            logger.info("")

            logger.info("📈 거래 통계:")
            logger.info(f"  총 거래: {result.statistics.total_trades}건")
            logger.info(f"  승리 거래: {result.statistics.winning_trades}건")
            logger.info(f"  패배 거래: {result.statistics.losing_trades}건")
            logger.info(f"  승률: {result.statistics.win_rate:.2f}%")
            logger.info(f"  손익비: {result.statistics.profit_factor:.2f}")
            logger.info("")

            if result.trades:
                logger.info(f"💰 거래 내역 ({len(result.trades)}건):")
                for i, trade in enumerate(result.trades[:20], 1):  # 최대 20개
                    logger.info(f"  {i}. {trade.stock_name} ({trade.stock_code})")
                    logger.info(f"     매수: {trade.buy_date} @ {trade.buy_price:,.0f}원")
                    logger.info(f"     매도: {trade.sell_date} @ {trade.sell_price:,.0f}원")
                    logger.info(f"     손익: {trade.profit:,.0f}원 ({trade.profit_rate:.2f}%)")
                    logger.info("")

                if len(result.trades) > 20:
                    logger.info(f"  ... 외 {len(result.trades) - 20}건")
            else:
                logger.warning("⚠️  거래 내역이 없습니다!")
                logger.info("   가능한 원인:")
                logger.info("   1. 조건을 만족하는 종목이 없음")
                logger.info("   2. PER 값이 모두 NaN (음수 순이익)")

            logger.info("")
            logger.info("=" * 80)

            # 검증
            logger.info("🔍 검증 결과:")
            checks = []

            checks.append(("수익률 계산됨", result.statistics.total_return is not None))
            checks.append(("거래 발생", result.statistics.total_trades > 0))
            checks.append(("최종 자본 > 0", result.statistics.final_capital > 0))
            checks.append(("거래 내역 존재", len(result.trades) > 0))

            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                logger.info(f"  {status} {check_name}")

            logger.info("=" * 80)

            # RDS 저장 확인
            from sqlalchemy import text

            logger.info("")
            logger.info("💾 RDS 저장 데이터 확인:")

            result_check = await db.execute(text('''
                SELECT
                    (SELECT COUNT(*) FROM backtest_sessions WHERE backtest_id = :id) as sessions,
                    (SELECT COUNT(*) FROM backtest_statistics WHERE backtest_id = :id) as statistics,
                    (SELECT COUNT(*) FROM backtest_trades WHERE backtest_id = :id) as trades,
                    (SELECT COUNT(*) FROM backtest_holdings WHERE backtest_id = :id) as holdings,
                    (SELECT COUNT(*) FROM backtest_daily_snapshots WHERE backtest_id = :id) as snapshots
            '''), {'id': str(backtest_id)})

            counts = result_check.first()
            logger.info(f"  Sessions: {counts[0]}개")
            logger.info(f"  Statistics: {counts[1]}개")
            logger.info(f"  Trades: {counts[2]}개")
            logger.info(f"  Holdings: {counts[3]}개")
            logger.info(f"  Daily Snapshots: {counts[4]}개")
            logger.info("")

            # 최종 판정
            if all([check[1] for check in checks]) and counts[2] > 0:
                logger.info("🎉 모든 검증 통과!")
            else:
                logger.warning("⚠️  일부 검증 실패")

            return result

        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    asyncio.run(test_securities_sector())
