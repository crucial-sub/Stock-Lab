"""
종합 백테스트 테스트 스크립트
- 다양한 매수 조건 (OR 로직 포함)
- 목표수익/손절 매도 조건
- 최소/최대 보유일
- 테마 + 개별 종목 혼합
"""
import asyncio
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

# 테스트용 사용자 토큰 (실제로는 로그인해서 받아야 함)
# 임시로 백테스트 API를 직접 호출
async def run_comprehensive_backtest():
    """종합 백테스트 실행"""

    payload = {
        "strategy_name": "종합 테스트 전략",
        "start_date": "2024-06-01",
        "end_date": "2025-01-31",
        "initial_capital": 100000000,
        "buy_conditions": [
            {
                "name": "A",
                "exp_left_side": "기본값({pbr})",
                "inequality": "<",
                "exp_right_side": 2.5
            },
            {
                "name": "B",
                "exp_left_side": "기본값({per})",
                "inequality": "<",
                "exp_right_side": 20
            },
            {
                "name": "C",
                "exp_left_side": "기본값({roe})",
                "inequality": ">",
                "exp_right_side": 8
            }
        ],
        "buy_logic": "(A and B) or C",
        "buy_priority_factor": "기본값({roe})",
        "buy_priority_order": "desc",
        "per_stock_ratio": 5.0,
        "max_daily_stock": 3,
        "sell_conditions": {
            "target_and_loss": {
                "target_gain": 20.0,
                "stop_loss": 10.0
            },
            "hold_days": {
                "min_hold_days": 3,
                "max_hold_days": 90
            }
        },
        "rebalance_frequency": "WEEKLY",
        "trade_targets": {
            "use_all_stocks": False,
            "selected_themes": ["IT 서비스", "반도체"],
            "selected_stocks": ["005930", "000660", "035420", "051910"]
        }
    }

    print("=" * 80)
    print("종합 백테스트 실행")
    print("=" * 80)
    print(f"\n매수 조건:")
    print(f"  - A: PBR < 2.5")
    print(f"  - B: PER < 20")
    print(f"  - C: ROE > 8%")
    print(f"  - 로직: (A and B) or C")
    print(f"\n매도 조건:")
    print(f"  - 목표수익: 20%")
    print(f"  - 손절: 10%")
    print(f"  - 최소 보유: 3일")
    print(f"  - 최대 보유: 90일")
    print(f"\n매매 대상:")
    print(f"  - 테마: IT 서비스, 반도체")
    print(f"  - 개별 종목: 삼성전자(005930), SK하이닉스(000660), NAVER(035420), LG화학(051910)")
    print(f"\n리밸런싱: 주간")
    print(f"종목당 비율: 5% (최대 20개 종목)")
    print(f"일일 최대 매수: 3종목")

    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/backtest/run",
            json=payload,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"\n✅ 백테스트 시작됨!")
            print(f"Session ID: {session_id}")

            # 완료 대기
            print("\n백테스트 실행 중...")
            max_wait = 120  # 최대 2분 대기
            waited = 0

            while waited < max_wait:
                await asyncio.sleep(5)
                waited += 5

                status_response = requests.get(
                    f"{BACKEND_URL}/api/v1/backtest/{session_id}/status"
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    progress = status_data.get("progress", 0)

                    print(f"진행률: {progress}% (상태: {status})")

                    if status == "COMPLETED":
                        print(f"\n✅ 백테스트 완료!")
                        return session_id
                    elif status == "FAILED":
                        print(f"\n❌ 백테스트 실패: {status_data.get('error_message')}")
                        return None

            print(f"\n⚠️  타임아웃 (2분 초과)")
            return session_id

        else:
            print(f"\n❌ 백테스트 시작 실패: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    session_id = asyncio.run(run_comprehensive_backtest())

    if session_id:
        print(f"\n프론트엔드에서 확인: http://localhost:3000/backtest/{session_id}")
