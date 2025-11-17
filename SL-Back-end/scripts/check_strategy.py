"""
전략 설정 상세 확인
"""
import asyncio
import sys
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def check_strategy(session_id: str):
    """전략 설정 확인"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 세션 및 전략 정보 조회
            result = await session.execute(text("""
                SELECT
                    ss.session_id,
                    ss.strategy_id,
                    ss.initial_capital,
                    s.stock_list,
                    tr.buy_condition,
                    tr.sell_condition,
                    tr.position_sizing,
                    tr.rebalance_frequency
                FROM simulation_sessions ss
                JOIN strategies s ON s.strategy_id = ss.strategy_id
                JOIN trading_rules tr ON tr.strategy_id = ss.strategy_id
                WHERE ss.session_id = :session_id
            """), {"session_id": session_id})

            row = result.fetchone()
            if not row:
                print(f"❌ 세션을 찾을 수 없습니다: {session_id}")
                return

            session_id = row[0]
            strategy_id = row[1]
            initial_capital = row[2]
            stock_list = row[3]
            buy_condition = row[4]
            sell_condition = row[5]
            position_sizing = row[6]
            rebalance_frequency = row[7]

            print(f"\n{'='*80}")
            print(f"백테스트 전략 설정 상세")
            print(f"{'='*80}\n")

            print(f"세션 ID: {session_id}")
            print(f"전략 ID: {strategy_id}")
            print(f"초기 자본: {initial_capital:,}원")

            print(f"\n종목 리스트:")
            if stock_list:
                print(f"  선택 방식: {stock_list.get('selection_type', 'N/A')}")
                print(f"  업종: {stock_list.get('industries', 'N/A')}")
                print(f"  최대 종목 수: {stock_list.get('max_holdings', 'N/A')}")

            print(f"\n매수 조건:")
            print(json.dumps(buy_condition, indent=2, ensure_ascii=False))

            print(f"\n매도 조건:")
            print(json.dumps(sell_condition, indent=2, ensure_ascii=False))

            print(f"\n포지션 사이징:")
            if position_sizing:
                print(f"  유형: {position_sizing.get('type', 'N/A')}")
                print(f"  값: {position_sizing.get('value', 'N/A')}")
                print(f"  세부 설정: {position_sizing}")

            print(f"\n리밸런싱 주기: {rebalance_frequency}")

            # 13이라는 숫자와 관련된 설정 찾기
            print(f"\n{'='*80}")
            print(f"13이라는 숫자 추적")
            print(f"{'='*80}")

            potential_thirteens = []
            if stock_list and stock_list.get('max_holdings') == 13:
                potential_thirteens.append(f"최대 보유 종목: {stock_list.get('max_holdings')}")

            if buy_condition:
                for key, value in buy_condition.items():
                    if value == 13 or (isinstance(value, dict) and 13 in value.values()):
                        potential_thirteens.append(f"매수 조건 {key}: {value}")

            if position_sizing:
                for key, value in position_sizing.items():
                    if value == 13:
                        potential_thirteens.append(f"포지션 사이징 {key}: {value}")

            if potential_thirteens:
                print(f"\n13과 관련된 설정 발견:")
                for item in potential_thirteens:
                    print(f"  - {item}")
                print(f"\n⚠️  13번 중복 거래의 원인일 가능성이 높습니다!")
            else:
                print(f"\n❓ 13과 직접 관련된 설정을 찾을 수 없습니다.")
                print(f"   코드 내부 로직에서 13번 반복되는 버그일 가능성이 높습니다.")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "7d775ce4-2a8f-409a-bceb-1ff5dfb4a166"
    asyncio.run(check_strategy(session_id))
