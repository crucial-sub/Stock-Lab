"""
매도 우선순위 테스트 - 목표가/손절가가 보유일보다 우선하는지 확인
"""

import asyncio
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.core.database import AsyncSessionLocal
from app.services.advanced_backtest import run_advanced_backtest


async def test_target_priority():
    """
    테스트: 목표가 10% 도달 시 보유일 5일 이전에도 매도되는지 확인

    조건:
    - PBR > 1.0
    - 목표가: 10%
    - 손절가: 10%
    - 최대 보유일: 5일
    - 초기자본: 5천만원
    """

    session_id = str(uuid4())

    print("=" * 100)
    print("매도 우선순위 테스트 시작")
    print("=" * 100)
    print(f"Session ID: {session_id}")
    print()
    print("테스트 조건:")
    print("  - 매수 조건: PBR > 1.0")
    print("  - 목표가: 10%")
    print("  - 손절가: 10%")
    print("  - 최대 보유일: 5일")
    print("  - 예상 결과: 목표가 10% 도달 시 즉시 매도 (보유일 무관)")
    print("=" * 100)

    # 백테스트 실행
    try:
        from app.services.advanced_backtest import _run_backtest_async
        result = await _run_backtest_async(
            session_id=session_id,
            strategy_id="test_strategy",
            start_date=date(2024, 11, 18),
            end_date=date(2025, 11, 18),
            initial_capital=Decimal("50000000"),
            benchmark="KOSPI",
            target_themes=['부동산', '운송·창고', '기타제조', '증권', '통신', '보험'],
            target_stocks=[],
            use_all_stocks=False,
            buy_conditions=[{
                'name': 'A',
                'exp_left_side': '기본값({pbr})',
                'inequality': '>',
                'exp_right_side': 1.0
            }],
            buy_logic="AND",
            priority_factor="{PER}",
            priority_order="desc",
            max_holdings=10,
            per_stock_ratio=10.0,
            rebalance_frequency="DAILY",
            commission_rate=0.1,
            slippage=0.0,
            target_and_loss={'target_gain': 10.0, 'stop_loss': 10.0},
            hold_days={'max_hold_days': 5},
            condition_sell=None,
            max_buy_value=None,
            max_daily_stock=None
        )

        print("\n✅ 백테스트 완료!")
        print()

        # 결과 조회
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text

            # 통계 조회
            stats_query = text('''
                SELECT
                    sst.total_return,
                    sst.total_trades,
                    sst.win_rate
                FROM simulation_statistics sst
                WHERE sst.session_id = :session_id
            ''')

            result = await db.execute(stats_query, {'session_id': session_id})
            stats = result.fetchone()

            if stats:
                print("📊 백테스트 결과:")
                print(f"  총 수익률: {stats[0]:.2f}%")
                print(f"  총 거래: {stats[1]}건")
                print(f"  승률: {stats[2]:.2f}%")
                print()

            # 매도 사유별 통계
            reason_query = text('''
                SELECT
                    selection_reason,
                    COUNT(*) as count,
                    AVG(profit_rate) as avg_return,
                    MIN(profit_rate) as min_return,
                    MAX(profit_rate) as max_return
                FROM backtest_trades
                WHERE backtest_id = :session_id
                AND trade_type = 'SELL'
                GROUP BY selection_reason
                ORDER BY count DESC
            ''')

            result = await db.execute(reason_query, {'session_id': session_id})
            reasons = result.fetchall()

            print("📋 매도 사유별 통계:")
            print("=" * 100)

            take_profit_count = 0
            max_hold_count = 0

            for reason, count, avg_ret, min_ret, max_ret in reasons:
                print(f"{reason}: {count}건")
                print(f"  평균 수익률: {avg_ret:.2f}%")
                print(f"  범위: {min_ret:.2f}% ~ {max_ret:.2f}%")
                print()

                if "Take profit" in reason:
                    take_profit_count += count
                elif "Max hold days" in reason:
                    max_hold_count += count

            print("=" * 100)
            print("✅ 검증 결과:")
            print("=" * 100)

            if take_profit_count > max_hold_count:
                print(f"✅ PASS: 목표가 매도가 더 많음 ({take_profit_count}건 vs {max_hold_count}건)")
                print("   → 목표가 우선순위가 정상 작동!")
            elif take_profit_count == 0:
                print(f"❌ FAIL: 목표가 매도가 하나도 없음 (보유일 매도: {max_hold_count}건)")
                print("   → 목표가 로직이 작동하지 않음")
            else:
                print(f"⚠️  WARNING: 목표가 매도({take_profit_count}건) < 보유일 매도({max_hold_count}건)")
                print("   → 일부만 목표가 매도됨")

            # 10% 초과 수익률 샘플 확인
            over_10_query = text('''
                SELECT
                    stock_code,
                    stock_name,
                    profit_rate,
                    hold_days,
                    selection_reason
                FROM backtest_trades
                WHERE backtest_id = :session_id
                AND trade_type = 'SELL'
                AND profit_rate > 10
                ORDER BY profit_rate DESC
                LIMIT 5
            ''')

            result = await db.execute(over_10_query, {'session_id': session_id})
            over_10 = result.fetchall()

            if over_10:
                print()
                print("📌 10% 초과 수익률 샘플 (상위 5건):")
                print("-" * 100)

                all_correct = True
                for stock_code, stock_name, profit_rate, hold_days, reason in over_10:
                    status = "✅" if "Take profit" in reason else "❌"
                    print(f"{status} {stock_code} ({stock_name}): {profit_rate:.2f}% | "
                          f"{hold_days}일 보유 | {reason}")

                    if "Take profit" not in reason:
                        all_correct = False

                if all_correct:
                    print()
                    print("✅ 모든 10% 초과 수익률이 목표가로 매도됨!")
                else:
                    print()
                    print("❌ 일부 10% 초과 수익률이 보유일로 매도됨 (버그!)")

            print("=" * 100)

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_target_priority())
