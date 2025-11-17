"""
매도 조건 테스트
- 보유기간 (Hold Days)
- 조건 매도 (Condition Sell)
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal


async def test_hold_days_sell():
    """보유기간 매도 테스트"""
    from app.core.database import get_db_async
    from app.services.backtest import BacktestEngine

    # 테스트 설정
    start_date = date(2023, 1, 1)
    end_date = date(2023, 3, 31)

    # 매수 조건: PER < 10
    buy_conditions = [
        {
            "id": "A",
            "factor": "PER",
            "operator": "<",
            "value": 10
        }
    ]

    # 매도 조건: 없음 (보유기간만 사용)
    sell_conditions = []

    # 보유기간 설정: 최소 5일, 최대 20일
    hold_days = {
        "min_hold_days": 5,
        "max_hold_days": 20,
        "sell_price_basis": "CURRENT",
        "sell_price_offset": None
    }

    async with get_db_async() as db:
        engine = BacktestEngine(
            db=db,
            initial_capital=Decimal("100000000"),
            commission_rate=Decimal("0.00015"),
            tax_rate=Decimal("0.0023"),
            slippage=Decimal("0.001")
        )

        result = await engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions,
            hold_days=hold_days,
            rebalance_frequency="DAILY",
            max_positions=10,
            position_sizing="EQUAL_WEIGHT",
            benchmark="KOSPI",
        )

        # 결과 검증
        print("\n" + "="*80)
        print("📊 보유기간 매도 테스트 결과")
        print("="*80)
        print(f"총 거래 횟수: {result['statistics']['total_trades']}")
        print(f"총 수익률: {result['statistics']['total_return']}%")
        print(f"승률: {result['statistics']['win_rate']}%")

        # 매도 거래 확인
        sell_trades = [t for t in result['trades'] if t['trade_type'] == 'SELL']
        print(f"\n매도 거래: {len(sell_trades)}건")

        hold_day_sells = [t for t in sell_trades if 'hold' in t.get('selection_reason', '').lower()]
        print(f"보유기간 만료 매도: {len(hold_day_sells)}건")

        if hold_day_sells:
            print("\n보유기간 매도 사례:")
            for trade in hold_day_sells[:5]:  # 처음 5건만 출력
                print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']}")

        return result


async def test_condition_sell():
    """조건 매도 테스트"""
    from app.core.database import get_db_async
    from app.services.backtest import BacktestEngine

    # 테스트 설정
    start_date = date(2023, 1, 1)
    end_date = date(2023, 3, 31)

    # 매수 조건: PER < 10
    buy_conditions = [
        {
            "id": "A",
            "factor": "PER",
            "operator": "<",
            "value": 10
        }
    ]

    # 매도 조건: 없음
    sell_conditions = []

    # 조건 매도: ROE < 5 이면 매도
    condition_sell = {
        "sell_conditions": [
            {
                "id": "A",
                "factor": "ROE",
                "operator": "<",
                "value": 5
            }
        ],
        "sell_logic": "A",
        "sell_price_basis": "CURRENT",
        "sell_price_offset": None
    }

    async with get_db_async() as db:
        engine = BacktestEngine(
            db=db,
            initial_capital=Decimal("100000000"),
            commission_rate=Decimal("0.00015"),
            tax_rate=Decimal("0.0023"),
            slippage=Decimal("0.001")
        )

        result = await engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions,
            condition_sell=condition_sell,
            rebalance_frequency="DAILY",
            max_positions=10,
            position_sizing="EQUAL_WEIGHT",
            benchmark="KOSPI",
        )

        # 결과 검증
        print("\n" + "="*80)
        print("📊 조건 매도 테스트 결과")
        print("="*80)
        print(f"총 거래 횟수: {result['statistics']['total_trades']}")
        print(f"총 수익률: {result['statistics']['total_return']}%")
        print(f"승률: {result['statistics']['win_rate']}%")

        # 매도 거래 확인
        sell_trades = [t for t in result['trades'] if t['trade_type'] == 'SELL']
        print(f"\n매도 거래: {len(sell_trades)}건")

        condition_sells = [t for t in sell_trades if 'condition' in t.get('selection_reason', '').lower()]
        print(f"조건 매도: {len(condition_sells)}건")

        if condition_sells:
            print("\n조건 매도 사례:")
            for trade in condition_sells[:5]:  # 처음 5건만 출력
                print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']}")

        return result


async def test_combined_sell_conditions():
    """보유기간 + 조건 매도 통합 테스트"""
    from app.core.database import get_db_async
    from app.services.backtest import BacktestEngine

    # 테스트 설정
    start_date = date(2023, 1, 1)
    end_date = date(2023, 3, 31)

    # 매수 조건: PER < 10
    buy_conditions = [
        {
            "id": "A",
            "factor": "PER",
            "operator": "<",
            "value": 10
        }
    ]

    # 매도 조건: 목표가 +10%, 손절가 -5%
    sell_conditions = []

    # 목표가/손절가 설정
    target_and_loss = {
        "target_gain": 10,
        "stop_loss": 5
    }

    # 보유기간 설정
    hold_days = {
        "min_hold_days": 3,
        "max_hold_days": 15,
        "sell_price_basis": "CURRENT",
        "sell_price_offset": None
    }

    # 조건 매도: ROE < 3 이면 매도
    condition_sell = {
        "sell_conditions": [
            {
                "id": "A",
                "factor": "ROE",
                "operator": "<",
                "value": 3
            }
        ],
        "sell_logic": "A",
        "sell_price_basis": "CURRENT",
        "sell_price_offset": None
    }

    async with get_db_async() as db:
        engine = BacktestEngine(
            db=db,
            initial_capital=Decimal("100000000"),
            commission_rate=Decimal("0.00015"),
            tax_rate=Decimal("0.0023"),
            slippage=Decimal("0.001")
        )

        result = await engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            buy_conditions=buy_conditions,
            sell_conditions=sell_conditions,
            target_and_loss=target_and_loss,
            hold_days=hold_days,
            condition_sell=condition_sell,
            rebalance_frequency="DAILY",
            max_positions=10,
            position_sizing="EQUAL_WEIGHT",
            benchmark="KOSPI",
        )

        # 결과 검증
        print("\n" + "="*80)
        print("📊 통합 매도 조건 테스트 결과")
        print("="*80)
        print(f"총 거래 횟수: {result['statistics']['total_trades']}")
        print(f"총 수익률: {result['statistics']['total_return']}%")
        print(f"승률: {result['statistics']['win_rate']}%")

        # 매도 거래 확인
        sell_trades = [t for t in result['trades'] if t['trade_type'] == 'SELL']
        print(f"\n매도 거래: {len(sell_trades)}건")

        # 매도 사유별 분류
        target_sells = [t for t in sell_trades if 'profit' in t.get('selection_reason', '').lower()]
        stop_sells = [t for t in sell_trades if 'loss' in t.get('selection_reason', '').lower()]
        hold_sells = [t for t in sell_trades if 'hold' in t.get('selection_reason', '').lower()]
        condition_sells = [t for t in sell_trades if 'condition' in t.get('selection_reason', '').lower()]

        print(f"  - 목표가 도달: {len(target_sells)}건")
        print(f"  - 손절가 도달: {len(stop_sells)}건")
        print(f"  - 보유기간 만료: {len(hold_sells)}건")
        print(f"  - 조건 매도: {len(condition_sells)}건")

        print("\n매도 사례:")
        for trade in sell_trades[:10]:  # 처음 10건만 출력
            print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']} | 수익률: {trade.get('profit_rate', 0):.2f}%")

        return result


async def main():
    """모든 테스트 실행"""
    print("\n🚀 매도 조건 테스트 시작\n")

    # 1. 보유기간 테스트
    try:
        await test_hold_days_sell()
    except Exception as e:
        print(f"\n❌ 보유기간 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    # 2. 조건 매도 테스트
    try:
        await test_condition_sell()
    except Exception as e:
        print(f"\n❌ 조건 매도 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    # 3. 통합 테스트
    try:
        await test_combined_sell_conditions()
    except Exception as e:
        print(f"\n❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ 모든 테스트 완료\n")


if __name__ == "__main__":
    asyncio.run(main())
