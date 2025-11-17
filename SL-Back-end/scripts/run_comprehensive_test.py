"""
종합 백테스트 실행 - 서비스 직접 호출
"""
import asyncio
import sys
from uuid import uuid4
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# 백엔드 모듈 import
sys.path.insert(0, '/app')

from app.core.database import get_db
from app.models.user import User
from app.models.simulation import TradingRule, SimulationSession
from app.services.advanced_backtest import _run_backtest_async


async def run_comprehensive_backtest():
    """종합 백테스트 실행"""

    print("=" * 80)
    print("종합 백테스트 실행")
    print("=" * 80)

    async for db in get_db():
        try:
            # 사용자 조회
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("❌ 사용자를 찾을 수 없습니다.")
                return

            print(f"✅ 사용자: {user.email}")

            # 기존 전략이 있는지 확인
            result = await db.execute(
                select(TradingRule).limit(1)
            )
            trading_rule = result.scalar_one_or_none()

            if not trading_rule:
                print("❌ 매매 규칙을 찾을 수 없습니다.")
                return

            strategy_id = trading_rule.strategy_id
            print(f"✅ 전략 ID: {strategy_id}")

            # 매매 규칙 업데이트 (종합 테스트 조건으로)
            trading_rule.buy_condition = {
                "conditions": [
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
                "logic": "(A and B) or C",
                "priority_factor": "기본값({roe})",
                "priority_order": "desc",
                "per_stock_ratio": 5.0,
                "max_buy_value": None,
                "max_daily_stock": 3,
                "buy_price_basis": "전일 종가",
                "buy_price_offset": 0.0,
                "trade_targets": {
                    "use_all_stocks": False,
                    "selected_universes": [],
                    "selected_themes": ["IT 서비스", "반도체"],
                    "selected_stocks": ["005930", "000660", "035420", "051910"],
                    "selected_stock_count": 0,
                    "total_stock_count": 2645
                }
            }

            trading_rule.sell_condition = {
                "target_and_loss": {
                    "target_gain": 20.0,
                    "stop_loss": 10.0
                },
                "hold_days": {
                    "min_hold_days": 3,
                    "max_hold_days": 90,
                    "sell_price_basis": "전일 종가",
                    "sell_price_offset": 0.0
                },
                "condition_sell": None
            }

            trading_rule.rebalance_frequency = "WEEKLY"

            await db.commit()
            print("✅ 매매 규칙 업데이트 완료")

            # 시뮬레이션 세션 생성
            session_id = str(uuid4())

            new_session = SimulationSession(
                session_id=session_id,
                strategy_id=strategy_id,
                user_id=user.user_id,
                session_name="종합 테스트 백테스트",
                start_date=date(2024, 6, 1),
                end_date=date(2025, 1, 31),
                initial_capital=100000000,
                status="PENDING",
                progress=0
            )

            db.add(new_session)
            await db.commit()

            print(f"✅ 백테스트 세션 생성: {session_id}")

            print(f"\n백테스트 설정:")
            print(f"  매수 조건: (PBR<2.5 AND PER<20) OR ROE>8%")
            print(f"  매도 조건: 목표수익 20%, 손절 10%, 최소 3일, 최대 90일")
            print(f"  매매 대상: IT서비스+반도체 테마 + 삼성전자,SK하이닉스,NAVER,LG화학")
            print(f"  리밸런싱: 주간")
            print(f"  종목당 비율: 5% (최대 20개)")
            print(f"  일일 최대 매수: 3종목")

            print(f"\n백테스트 실행 중... (1-2분 소요)")

            # 백테스트 실행
            await _run_backtest_async(
                db=db,
                session_id=session_id
            )

            print(f"\n✅ 백테스트 완료!")
            print(f"Session ID: {session_id}")
            print(f"\n결과 확인:")
            print(f"  프론트엔드: http://localhost:3000/backtest/{session_id}")

            return session_id

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return None

        break


if __name__ == "__main__":
    asyncio.run(run_comprehensive_backtest())
