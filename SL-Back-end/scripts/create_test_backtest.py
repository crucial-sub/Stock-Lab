"""
종합 백테스트 테스트 - DB 직접 생성
"""
import asyncio
import sys
from uuid import uuid4
from datetime import date, datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def create_comprehensive_backtest():
    """종합 백테스트 생성 및 실행"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 사용자 조회
            result = await session.execute(text("SELECT user_id FROM users LIMIT 1"))
            user_row = result.fetchone()
            if not user_row:
                print("❌ 사용자를 찾을 수 없습니다.")
                return None

            user_id = user_row[0]

            # 포트폴리오 전략 생성
            strategy_id = str(uuid4())

            await session.execute(text("""
                INSERT INTO portfolio_strategies (
                    strategy_id, user_id, strategy_name, description,
                    stock_list, is_public, created_at, updated_at
                )
                VALUES (
                    :strategy_id, :user_id, :strategy_name, :description,
                    :stock_list, false, NOW(), NOW()
                )
            """), {
                "strategy_id": strategy_id,
                "user_id": user_id,
                "strategy_name": "종합 테스트 전략",
                "description": "OR 로직, 테마+개별 종목, 다양한 매도 조건 테스트",
                "stock_list": {
                    "selection_type": "custom",
                    "max_holdings": 20
                }
            })

            # 매매 규칙 생성
            await session.execute(text("""
                INSERT INTO trading_rules (
                    strategy_id, buy_condition, sell_condition,
                    position_sizing, rebalance_frequency
                )
                VALUES (
                    :strategy_id, :buy_condition, :sell_condition,
                    :position_sizing, :rebalance_frequency
                )
            """), {
                "strategy_id": strategy_id,
                "buy_condition": {
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
                },
                "sell_condition": {
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
                },
                "position_sizing": {
                    "type": "equal_weight",
                    "value": 5.0
                },
                "rebalance_frequency": "WEEKLY"
            })

            # 시뮬레이션 세션 생성
            session_id = str(uuid4())

            await session.execute(text("""
                INSERT INTO simulation_sessions (
                    session_id, strategy_id, user_id, session_name,
                    start_date, end_date, initial_capital,
                    status, progress, created_at, updated_at
                )
                VALUES (
                    :session_id, :strategy_id, :user_id, :session_name,
                    :start_date, :end_date, :initial_capital,
                    'PENDING', 0, NOW(), NOW()
                )
            """), {
                "session_id": session_id,
                "strategy_id": strategy_id,
                "user_id": user_id,
                "session_name": "종합 테스트 백테스트",
                "start_date": date(2024, 6, 1),
                "end_date": date(2025, 1, 31),
                "initial_capital": 100000000
            })

            await session.commit()

            print(f"✅ 백테스트 세션 생성 완료!")
            print(f"Session ID: {session_id}")
            print(f"Strategy ID: {strategy_id}")

            return session_id

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return None
        finally:
            await engine.dispose()


async def execute_backtest(session_id: str):
    """백테스트 실행"""
    print(f"\n백테스트 실행 시작...")

    # 백테스트 서비스를 직접 import하여 실행
    from app.services.advanced_backtest import _run_backtest_async
    from app.core.database import get_async_db

    async for db in get_async_db():
        try:
            await _run_backtest_async(
                db=db,
                session_id=session_id
            )
            print(f"✅ 백테스트 실행 완료!")
        except Exception as e:
            print(f"❌ 백테스트 실행 실패: {e}")
            import traceback
            traceback.print_exc()
        break


if __name__ == "__main__":
    print("=" * 80)
    print("종합 백테스트 테스트")
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
    print(f"  - 개별 종목: 삼성전자, SK하이닉스, NAVER, LG화학")
    print(f"\n리밸런싱: 주간")
    print(f"종목당 비율: 5% (최대 20개 종목)")
    print(f"일일 최대 매수: 3종목\n")

    session_id = asyncio.run(create_comprehensive_backtest())

    if session_id:
        print(f"\n백테스트 실행 중... (이 작업은 1-2분 소요됩니다)")
        asyncio.run(execute_backtest(session_id))
        print(f"\n프론트엔드에서 결과 확인: http://localhost:3000/backtest/{session_id}")
