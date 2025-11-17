"""
API를 통해 매도 조건 테스트
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"


def test_hold_days_sell():
    """보유기간 매도 테스트"""
    payload = {
        "buy_conditions": [
            {
                "id": "A",
                "factor": "PER",
                "operator": "<",
                "value": 10
            }
        ],
        "sell_conditions": [],
        "hold_days": {
            "min_hold_days": 5,
            "max_hold_days": 20,
            "sell_price_basis": "CURRENT",
            "sell_price_offset": None
        },
        "start_date": "2023-01-01",
        "end_date": "2023-03-31",
        "initial_capital": 100000000,
        "rebalance_frequency": "DAILY",
        "max_positions": 10,
        "position_sizing": "EQUAL_WEIGHT",
        "commission_rate": 0.00015,
        "slippage": 0.001
    }

    print("\n" + "="*80)
    print("📊 보유기간 매도 테스트")
    print("="*80)
    print(f"요청 데이터: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    response = requests.post(f"{BASE_URL}/api/backtest", json=payload, timeout=120)

    if response.status_code == 200:
        result = response.json()
        stats = result.get('statistics', {})
        print(f"\n✅ 백테스트 성공!")
        print(f"총 거래 횟수: {stats.get('total_trades')}")
        print(f"총 수익률: {stats.get('total_return')}%")
        print(f"승률: {stats.get('win_rate')}%")

        # 매도 거래 확인
        trades = result.get('trades', [])
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']
        print(f"\n매도 거래: {len(sell_trades)}건")

        hold_day_sells = [t for t in sell_trades if 'hold' in t.get('selection_reason', '').lower()]
        print(f"보유기간 만료 매도: {len(hold_day_sells)}건")

        if hold_day_sells:
            print("\n보유기간 매도 사례:")
            for trade in hold_day_sells[:5]:
                print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']}")

        return result
    else:
        print(f"\n❌ 백테스트 실패: {response.status_code}")
        print(f"에러: {response.text}")
        return None


def test_condition_sell():
    """조건 매도 테스트"""
    payload = {
        "buy_conditions": [
            {
                "id": "A",
                "factor": "PER",
                "operator": "<",
                "value": 10
            }
        ],
        "sell_conditions": [],
        "condition_sell": {
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
        },
        "start_date": "2023-01-01",
        "end_date": "2023-03-31",
        "initial_capital": 100000000,
        "rebalance_frequency": "DAILY",
        "max_positions": 10,
        "position_sizing": "EQUAL_WEIGHT",
        "commission_rate": 0.00015,
        "slippage": 0.001
    }

    print("\n" + "="*80)
    print("📊 조건 매도 테스트")
    print("="*80)
    print(f"요청 데이터: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    response = requests.post(f"{BASE_URL}/api/backtest", json=payload, timeout=120)

    if response.status_code == 200:
        result = response.json()
        stats = result.get('statistics', {})
        print(f"\n✅ 백테스트 성공!")
        print(f"총 거래 횟수: {stats.get('total_trades')}")
        print(f"총 수익률: {stats.get('total_return')}%")
        print(f"승률: {stats.get('win_rate')}%")

        # 매도 거래 확인
        trades = result.get('trades', [])
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']
        print(f"\n매도 거래: {len(sell_trades)}건")

        condition_sells = [t for t in sell_trades if 'condition' in t.get('selection_reason', '').lower()]
        print(f"조건 매도: {len(condition_sells)}건")

        if condition_sells:
            print("\n조건 매도 사례:")
            for trade in condition_sells[:5]:
                print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']}")

        return result
    else:
        print(f"\n❌ 백테스트 실패: {response.status_code}")
        print(f"에러: {response.text}")
        return None


def test_combined_sell():
    """통합 매도 조건 테스트"""
    payload = {
        "buy_conditions": [
            {
                "id": "A",
                "factor": "PER",
                "operator": "<",
                "value": 10
            }
        ],
        "sell_conditions": [],
        "target_and_loss": {
            "target_gain": 10,
            "stop_loss": 5
        },
        "hold_days": {
            "min_hold_days": 3,
            "max_hold_days": 15,
            "sell_price_basis": "CURRENT",
            "sell_price_offset": None
        },
        "condition_sell": {
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
        },
        "start_date": "2023-01-01",
        "end_date": "2023-03-31",
        "initial_capital": 100000000,
        "rebalance_frequency": "DAILY",
        "max_positions": 10,
        "position_sizing": "EQUAL_WEIGHT",
        "commission_rate": 0.00015,
        "slippage": 0.001
    }

    print("\n" + "="*80)
    print("📊 통합 매도 조건 테스트")
    print("="*80)
    print(f"요청 데이터: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    response = requests.post(f"{BASE_URL}/api/backtest", json=payload, timeout=120)

    if response.status_code == 200:
        result = response.json()
        stats = result.get('statistics', {})
        print(f"\n✅ 백테스트 성공!")
        print(f"총 거래 횟수: {stats.get('total_trades')}")
        print(f"총 수익률: {stats.get('total_return')}%")
        print(f"승률: {stats.get('win_rate')}%")

        # 매도 거래 확인
        trades = result.get('trades', [])
        sell_trades = [t for t in trades if t.get('trade_type') == 'SELL']
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
        for trade in sell_trades[:10]:
            print(f"  - {trade['stock_name']} | {trade['hold_days']}일 보유 | {trade['selection_reason']} | 수익률: {trade.get('profit_rate', 0):.2f}%")

        return result
    else:
        print(f"\n❌ 백테스트 실패: {response.status_code}")
        print(f"에러: {response.text}")
        return None


def main():
    """모든 테스트 실행"""
    print("\n🚀 매도 조건 API 테스트 시작\n")

    # 1. 보유기간 테스트
    try:
        test_hold_days_sell()
    except Exception as e:
        print(f"\n❌ 보유기간 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    # 2. 조건 매도 테스트
    try:
        test_condition_sell()
    except Exception as e:
        print(f"\n❌ 조건 매도 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    # 3. 통합 테스트
    try:
        test_combined_sell()
    except Exception as e:
        print(f"\n❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ 모든 테스트 완료\n")


if __name__ == "__main__":
    main()
