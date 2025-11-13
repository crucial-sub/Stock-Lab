#!/usr/bin/env python3
"""
백테스트 로직 검증 스크립트
실제 조건으로 백테스트를 실행하여 검증합니다.
"""

import asyncio
import sys
import logging
from datetime import date
from pathlib import Path
from decimal import Decimal

# 프로젝트 경로 추가
sys.path.append(str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal
from app.services.backtest import BacktestEngine

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_backtest_with_actual_conditions():
    """실제 조건으로 백테스트 테스트"""

    logger.info("=" * 80)
    logger.info("백테스트 로직 검증 시작")
    logger.info("=" * 80)

    async with AsyncSessionLocal() as db:
        engine = BacktestEngine(db=db)

        # 테스트 조건 (사용자가 사용한 조건과 유사)
        test_params = {
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 12, 31),
            "initial_capital": Decimal("10000000"),
            "benchmark": "KOSPI",
            "target_themes": ["증권"],  # 증권 종목
            "target_stocks": ["005930"],  # 삼성전자
            "use_all_stocks": False,
            "buy_conditions": [
                {"factor": "PBR", "operator": ">=", "value": 0.0},  # PBR >= 0
                {"factor": "PER", "operator": ">=", "value": 3.0},  # PER >= 3
            ],
            "priority_factor": "PER",
            "priority_order": "asc",
            "sell_conditions": [],
            "condition_sell": {
                "profit_target": 10.0,
                "stop_loss": -5.0
            },
            "rebalance_frequency": "WEEKLY",
            "max_positions": 5,
            "position_sizing": "equal",
        }

        logger.info(f"테스트 조건:")
        logger.info(f"  기간: {test_params['start_date']} ~ {test_params['end_date']}")
        logger.info(f"  초기자본: {test_params['initial_capital']:,}원")
        logger.info(f"  매매대상: 증권 종목 + 삼성전자")
        logger.info(f"  매수조건: PBR >= 0.0 AND PER >= 3.0")
        logger.info(f"  우선순위: PER 오름차순")
        logger.info(f"  리밸런싱: 주간")
        logger.info(f"  최대포지션: 5개")
        logger.info("")

        try:
            import uuid
            backtest_id = uuid.uuid4()

            logger.info(f"백테스트 ID: {backtest_id}")
            logger.info("백테스트 실행 중...")
            logger.info("")

            # 백테스트 실행 (priority_factor를 buy_conditions에 포함)
            buy_conditions_with_priority = {
                "conditions": test_params["buy_conditions"],
                "priority_factor": test_params["priority_factor"],
                "priority_order": test_params["priority_order"]
            }

            result = await engine.run_backtest(
                backtest_id=backtest_id,
                start_date=test_params["start_date"],
                end_date=test_params["end_date"],
                initial_capital=test_params["initial_capital"],
                benchmark=test_params["benchmark"],
                target_themes=test_params["target_themes"],
                target_stocks=test_params["target_stocks"],
                buy_conditions=test_params["buy_conditions"],
                sell_conditions=test_params["sell_conditions"],
                condition_sell=test_params["condition_sell"],
                rebalance_frequency=test_params["rebalance_frequency"],
                max_positions=test_params["max_positions"],
                position_sizing=test_params["position_sizing"],
            )

            logger.info("=" * 80)
            logger.info("✅ 백테스트 완료!")
            logger.info("=" * 80)

            # 결과 출력
            stats = result.get("statistics", {})
            logger.info("📊 통계 결과:")
            logger.info(f"  최종 자산: {stats.get('final_capital', 0):,.0f}원")
            logger.info(f"  총 수익률: {stats.get('total_return', 0):.2f}%")
            logger.info(f"  연환산 수익률: {stats.get('annualized_return', 0):.2f}%")
            logger.info(f"  최대 낙폭(MDD): {stats.get('max_drawdown', 0):.2f}%")
            logger.info(f"  변동성: {stats.get('volatility', 0):.2f}%")
            logger.info(f"  샤프비율: {stats.get('sharpe_ratio', 0):.2f}")
            logger.info("")

            logger.info("📈 거래 통계:")
            logger.info(f"  총 거래: {stats.get('total_trades', 0)}건")
            logger.info(f"  승리 거래: {stats.get('winning_trades', 0)}건")
            logger.info(f"  패배 거래: {stats.get('losing_trades', 0)}건")
            logger.info(f"  승률: {stats.get('win_rate', 0):.2f}%")
            logger.info(f"  손익비(Profit Factor): {stats.get('profit_factor', 0):.2f}")
            logger.info("")

            # 거래 샘플 출력
            trades = result.get("trades", [])
            if trades:
                logger.info(f"💰 거래 내역 (최근 5건):")
                for i, trade in enumerate(trades[:5], 1):
                    logger.info(f"  {i}. {trade.get('stock_name', 'N/A')} ({trade.get('stock_code', 'N/A')})")
                    logger.info(f"     매수: {trade.get('buy_date', 'N/A')} @ {trade.get('buy_price', 0):,.0f}원")
                    logger.info(f"     매도: {trade.get('sell_date', 'N/A')} @ {trade.get('sell_price', 0):,.0f}원")
                    logger.info(f"     손익: {trade.get('profit', 0):,.0f}원 ({trade.get('profit_rate', 0):.2f}%)")
                    logger.info("")
            else:
                logger.warning("⚠️  거래 내역이 없습니다!")
                logger.info("   가능한 원인:")
                logger.info("   1. 조건을 만족하는 종목이 없음")
                logger.info("   2. 가격 데이터 누락")
                logger.info("   3. 팩터 계산 실패")

            logger.info("=" * 80)

            # 검증 체크리스트
            logger.info("🔍 검증 체크리스트:")
            checks = []

            # 1. 결과 객체 존재
            checks.append(("결과 객체 존재", result is not None))

            # 2. 통계 데이터 존재
            checks.append(("통계 데이터 존재", bool(stats)))

            # 3. 수익률 계산됨
            checks.append(("수익률 계산됨", stats.get('total_return') is not None))

            # 4. 거래 내역 존재
            checks.append(("거래 내역 존재", len(trades) > 0))

            # 5. 수익률 포인트 존재
            yield_points = result.get("yield_points", [])
            checks.append(("수익률 차트 데이터 존재", len(yield_points) > 0))

            # 6. 에러 없음
            checks.append(("에러 없음", "error" not in result))

            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                logger.info(f"  {status} {check_name}")

            logger.info("=" * 80)

            # 실패한 체크 항목 상세 설명
            failed_checks = [name for name, result in checks if not result]
            if failed_checks:
                logger.warning("")
                logger.warning("⚠️  실패한 검증 항목:")
                for check in failed_checks:
                    logger.warning(f"  - {check}")

                    if check == "거래 내역 존재":
                        logger.warning("    → 조건을 만족하는 종목을 찾지 못했거나 매수/매도가 실행되지 않았습니다")
                        logger.warning("    → 로그에서 '조건 만족 종목' 메시지를 확인하세요")
                    elif check == "수익률 차트 데이터 존재":
                        logger.warning("    → 일별 포트폴리오 가치 스냅샷이 생성되지 않았습니다")

                logger.warning("")

            return result

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ 백테스트 실패: {e}")
            logger.error("=" * 80)
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    asyncio.run(test_backtest_with_actual_conditions())
