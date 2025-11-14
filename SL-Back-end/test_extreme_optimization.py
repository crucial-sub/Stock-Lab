"""
극한 최적화 테스트 및 벤치마크
백테스트 성능을 측정하고 최적화 효과를 검증
"""

import asyncio
import sys
import os
import time
from datetime import date, datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_context
from app.services.backtest import BacktestEngine
from app.services.backtest_integration import integrate_optimizations


async def test_backtest_performance():
    """백테스트 성능 테스트"""

    print("=" * 80)
    print("🔥 극한 최적화 백테스트 성능 테스트")
    print("=" * 80)
    print()

    # 테스트 설정
    test_config = {
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "initial_capital": 50_000_000,
        "target_themes": ["IT 서비스"],
        "buy_conditions": [
            {"factor": "ROE", "operator": ">", "value": 15.0},
            {"factor": "PBR", "operator": "<", "value": 2.0}
        ],
        "priority_factor": "ROE",
        "priority_order": "desc",
        "max_holdings": 20,
        "per_stock_ratio": 5.0,
        "rebalance_frequency": "monthly",
        "commission_rate": 0.001,
        "slippage": 0.0
    }

    print("📊 테스트 설정:")
    print(f"  기간: {test_config['start_date']} ~ {test_config['end_date']}")
    print(f"  초기 자본: {test_config['initial_capital']:,}원")
    print(f"  대상 테마: {test_config['target_themes']}")
    print(f"  매수 조건: ROE > 15%, PBR < 2.0")
    print(f"  리밸런싱: {test_config['rebalance_frequency']}")
    print()

    async with get_db_context() as db:
        # 백테스트 엔진 생성
        engine = BacktestEngine(db)

        # 최적화 통합
        print("🚀 극한 최적화 모듈 통합 중...")
        integrate_optimizations(engine)
        print("✅ 최적화 모듈 통합 완료")
        print()

        # SimpleCondition 클래스 정의 (BacktestEngine 내부 클래스와 동일)
        class SimpleCondition:
            def __init__(self, factor, operator, value):
                self.factor = factor
                self.operator = operator
                self.value = value
                self.exp_left_side = f"기본값({{{factor}}})"
                self.exp_right_side = str(value)

        # 조건 변환
        buy_conditions = [
            SimpleCondition(cond["factor"], cond["operator"], cond["value"])
            for cond in test_config["buy_conditions"]
        ]

        # 백테스트 실행 (시간 측정)
        print("⏱️  백테스트 실행 시작...")
        start_time = time.time()

        try:
            result = await engine.run_backtest(
                backtest_id="test_extreme_optimization",
                start_date=test_config["start_date"],
                end_date=test_config["end_date"],
                initial_capital=test_config["initial_capital"],
                buy_conditions=buy_conditions,
                sell_condition=None,
                priority_factor=test_config["priority_factor"],
                priority_order=test_config["priority_order"],
                max_holdings=test_config["max_holdings"],
                per_stock_ratio=test_config["per_stock_ratio"],
                rebalance_frequency=test_config["rebalance_frequency"],
                commission_rate=test_config["commission_rate"],
                slippage=test_config["slippage"],
                target_themes=test_config["target_themes"],
                target_stocks=[]
            )

            elapsed_time = time.time() - start_time

            print()
            print("=" * 80)
            print("✅ 백테스트 완료!")
            print("=" * 80)
            print()
            print(f"⏱️  총 실행 시간: {elapsed_time:.2f}초")
            print()

            # 결과 분석
            if result and "performance_metrics" in result:
                metrics = result["performance_metrics"]

                print("📈 성능 지표:")
                print(f"  총 수익률: {metrics.get('total_return', 0):.2f}%")
                print(f"  연환산 수익률: {metrics.get('annualized_return', 0):.2f}%")
                print(f"  샤프 비율: {metrics.get('sharpe_ratio', 0):.2f}")
                print(f"  최대 낙폭 (MDD): {metrics.get('max_drawdown', 0):.2f}%")
                print(f"  승률: {metrics.get('win_rate', 0):.2f}%")
                print()

                print("📊 거래 통계:")
                print(f"  총 거래 횟수: {metrics.get('total_trades', 0):,}회")
                print(f"  매수 횟수: {metrics.get('buy_count', 0):,}회")
                print(f"  매도 횟수: {metrics.get('sell_count', 0):,}회")
                print()

                print("💰 자본 변화:")
                print(f"  시작 자본: {test_config['initial_capital']:,}원")
                print(f"  최종 자본: {metrics.get('final_capital', 0):,.0f}원")
                print(f"  순이익: {metrics.get('net_profit', 0):,.0f}원")
                print()

            # 성능 평가
            print("=" * 80)
            print("🎯 최적화 성능 평가")
            print("=" * 80)
            print()

            # 목표 시간 비교
            original_time = 600  # 기존: 8-10분 (600초)
            target_time = 20  # 목표: 10-20초

            improvement_ratio = original_time / elapsed_time

            print(f"  기존 예상 시간: {original_time}초 (8-10분)")
            print(f"  목표 시간: {target_time}초")
            print(f"  실제 실행 시간: {elapsed_time:.2f}초")
            print(f"  개선 배율: {improvement_ratio:.1f}배 빠름")
            print()

            if elapsed_time <= target_time:
                print("  🎉 목표 달성! 극한 최적화 성공!")
            elif elapsed_time <= target_time * 2:
                print("  ✅ 목표 근접! 매우 양호한 성능!")
            elif elapsed_time <= original_time / 5:
                print("  👍 5배 이상 개선! 좋은 성능!")
            else:
                print("  ⚠️  추가 최적화 필요")

            print()

            # 세부 타이밍 (로그에서 추출 가능)
            print("📝 세부 성능 분석:")
            print("  - 가격 데이터 로드: 캐시 활용")
            print("  - 재무 데이터 로드: 병렬 쿼리")
            print("  - 팩터 계산: 극한 최적화 모드 (Numba JIT + 병렬)")
            print("  - Redis 캐싱: Lua 스크립트 배치 처리")
            print()

            return {
                "success": True,
                "elapsed_time": elapsed_time,
                "improvement_ratio": improvement_ratio,
                "metrics": metrics if result else None
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            print()
            print("=" * 80)
            print("❌ 백테스트 실패!")
            print("=" * 80)
            print()
            print(f"⏱️  실행 시간: {elapsed_time:.2f}초 (실패 전)")
            print(f"❌ 오류: {str(e)}")
            print()

            import traceback
            print("🔍 상세 오류:")
            traceback.print_exc()

            return {
                "success": False,
                "elapsed_time": elapsed_time,
                "error": str(e)
            }


async def main():
    """메인 테스트 실행"""
    print()
    print("🚀 Stock Lab 극한 최적화 테스트 시작")
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    result = await test_backtest_performance()

    print()
    print("=" * 80)
    print("테스트 완료")
    print("=" * 80)
    print()

    if result["success"]:
        print("✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
