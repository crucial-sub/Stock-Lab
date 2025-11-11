"""
백테스트 엔진 테스트
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.services.backtest import BacktestEngine
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_backtest():
    """백테스트 테스트"""

    # 데이터베이스 연결
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 백테스트 엔진 생성
        engine = BacktestEngine(db)

        # 백테스트 파라미터 설정
        backtest_id = uuid4()

        # 매수 조건: 저PER + 고ROE + 모멘텀
        buy_conditions = [
            {
                "factor": "PER",
                "operator": "<",
                "value": 15,
                "weight": 1.0
            },
            {
                "factor": "ROE",
                "operator": ">",
                "value": 10,
                "weight": 1.0
            },
            {
                "factor": "MOMENTUM_3M",
                "operator": ">",
                "value": 0,
                "weight": 0.5
            }
        ]

        # 매도 조건: 손절(-10%), 익절(20%), 보유기간(60일)
        sell_conditions = [
            {
                "type": "STOP_LOSS",
                "value": 10  # -10% 손절
            },
            {
                "type": "TAKE_PROFIT",
                "value": 20  # 20% 익절
            },
            {
                "type": "HOLD_DAYS",
                "value": 60  # 60일 보유
            }
        ]

        # 백테스트 실행
        try:
            result = await engine.run_backtest(
                backtest_id=backtest_id,
                buy_conditions=buy_conditions,
                sell_conditions=sell_conditions,
                start_date=date(2023, 1, 1),
                end_date=date(2024, 1, 1),
                initial_capital=Decimal("100000000"),  # 1억원
                rebalance_frequency="MONTHLY",
                max_positions=20,
                position_sizing="EQUAL_WEIGHT",
                benchmark="KOSPI",
                commission_rate=0.00015,  # 0.015% 수수료 (사용자 설정 가능)
                slippage=0.001  # 0.1% 슬리피지 (사용자 설정 가능)
            )

            # 결과 출력
            logger.info("=" * 80)
            logger.info("백테스트 완료!")
            logger.info("=" * 80)

            # 설정 출력
            logger.info("백테스트 설정:")
            logger.info(f"  - 수수료율: {result.settings.commission_rate*100:.3f}%")
            logger.info(f"  - 거래세율: {result.settings.tax_rate*100:.2f}% (고정)")
            logger.info(f"  - 슬리피지: {result.settings.slippage*100:.2f}%")
            logger.info("")

            # 통계 출력
            stats = result.statistics
            logger.info(f"총 수익률: {stats.total_return:.2f}%")
            logger.info(f"연환산 수익률: {stats.annualized_return:.2f}%")
            logger.info(f"최대 낙폭: {stats.max_drawdown:.2f}%")
            logger.info(f"샤프 비율: {stats.sharpe_ratio:.2f}")
            logger.info(f"소르티노 비율: {stats.sortino_ratio:.2f}")
            logger.info(f"변동성: {stats.volatility:.2f}%")

            # 거래 통계
            logger.info("=" * 80)
            logger.info("거래 통계")
            logger.info("=" * 80)
            logger.info(f"총 거래 수: {stats.total_trades}")
            logger.info(f"승리 거래: {stats.winning_trades}")
            logger.info(f"패배 거래: {stats.losing_trades}")
            logger.info(f"승률: {stats.win_rate:.2f}%")
            logger.info(f"평균 수익: {stats.avg_win:.2f}%")
            logger.info(f"평균 손실: {stats.avg_loss:.2f}%")
            logger.info(f"손익비: {stats.profit_loss_ratio:.2f}")

            # 자본 정보
            logger.info("=" * 80)
            logger.info("자본 정보")
            logger.info("=" * 80)
            logger.info(f"초기 자본: {stats.initial_capital:,.0f}원")
            logger.info(f"최종 자본: {stats.final_capital:,.0f}원")
            logger.info(f"최고 자본: {stats.peak_capital:,.0f}원")
            logger.info(f"거래일 수: {stats.trading_days}")

            # 현재 보유 종목
            if result.current_holdings:
                logger.info("=" * 80)
                logger.info("현재 보유 종목")
                logger.info("=" * 80)
                for holding in result.current_holdings[:5]:  # 상위 5개만
                    logger.info(f"{holding.stock_name} ({holding.stock_code})")
                    logger.info(f"  - 수량: {holding.quantity:,}")
                    logger.info(f"  - 평균가: {holding.avg_price:,.0f}원")
                    logger.info(f"  - 현재가: {holding.current_price:,.0f}원")
                    logger.info(f"  - 수익률: {holding.profit_rate:.2f}%")
                    logger.info(f"  - 비중: {holding.weight:.2f}%")

            # 월별 성과
            if result.monthly_performance:
                logger.info("=" * 80)
                logger.info("월별 성과 (최근 6개월)")
                logger.info("=" * 80)
                for monthly in result.monthly_performance[-6:]:
                    logger.info(f"{monthly.year}년 {monthly.month}월: {monthly.return_rate:.2f}%")

            # 연도별 성과
            if result.yearly_performance:
                logger.info("=" * 80)
                logger.info("연도별 성과")
                logger.info("=" * 80)
                for yearly in result.yearly_performance:
                    logger.info(f"{yearly.year}년:")
                    logger.info(f"  - 수익률: {yearly.return_rate:.2f}%")
                    logger.info(f"  - MDD: {yearly.max_drawdown:.2f}%")
                    logger.info(f"  - 샤프: {yearly.sharpe_ratio:.2f}")
                    logger.info(f"  - 거래: {yearly.trades}건")

            # 차트 데이터 샘플
            if result.chart_data:
                logger.info("=" * 80)
                logger.info("차트 데이터 샘플")
                logger.info("=" * 80)
                logger.info(f"데이터 포인트 수: {len(result.chart_data.get('dates', []))}")
                if result.chart_data.get('dates'):
                    logger.info(f"시작일: {result.chart_data['dates'][0]}")
                    logger.info(f"종료일: {result.chart_data['dates'][-1]}")

                    # 최종 누적 수익률
                    if result.chart_data.get('cumulative_returns'):
                        final_return = result.chart_data['cumulative_returns'][-1]
                        logger.info(f"최종 누적 수익률: {final_return:.2f}%")

                    # 최대 낙폭
                    if result.chart_data.get('drawdowns'):
                        max_dd = min(result.chart_data['drawdowns'])
                        logger.info(f"차트상 최대 낙폭: {max_dd:.2f}%")

            logger.info("=" * 80)
            logger.info("백테스트 테스트 완료!")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error(f"백테스트 실행 중 오류: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(test_backtest())
