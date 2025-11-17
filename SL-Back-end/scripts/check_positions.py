"""
포지션 분할 여부를 확인하는 스크립트
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def check_positions(session_id: str):
    """포지션 분할 확인"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 2024-11-18 첫 매수일 확인
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    stock_code,
                    stock_name,
                    trade_type,
                    quantity,
                    price,
                    amount
                FROM simulation_trades
                WHERE session_id = :session_id
                    AND trade_date = '2024-11-18'
                    AND stock_code = '045340'
                ORDER BY trade_type DESC
            """), {"session_id": session_id})

            trades = result.fetchall()

            print(f"\n2024-11-18 (첫 매수일) 045340 거래 내역:")
            print(f"{'유형':<6} {'수량':>10} {'가격':>12} {'금액':>15}")
            print("=" * 50)

            buy_count = 0
            total_qty = 0
            for trade in trades:
                trade_type = trade[2]
                qty = trade[3]
                price = float(trade[4])
                amount = float(trade[5]) if trade[5] else 0

                print(f"{trade_type:<6} {qty:>10}주 {price:>12,.0f}원 {amount:>15,.0f}원")

                if trade_type == 'BUY':
                    buy_count += 1
                    total_qty += qty

            print(f"\n총 매수: {buy_count}건, {total_qty:,}주")
            print(f"\n예상: 13건 × 1113주 = 14,469주" if buy_count == 13 else f"실제와 다름!")

            # 매수 원인 추적 - 백테스트 설정 확인
            print(f"\n" + "=" * 80)
            print(f"백테스트 설정 확인")
            print(f"=" * 80)

            result = await session.execute(text("""
                SELECT
                    ss.session_id,
                    ss.strategy_id,
                    tr.buy_condition,
                    tr.sell_condition
                FROM simulation_sessions ss
                JOIN trading_rules tr ON tr.strategy_id = ss.strategy_id
                WHERE ss.session_id = :session_id
            """), {"session_id": session_id})

            session_row = result.fetchone()
            if session_row:
                buy_condition = session_row[2]
                sell_condition = session_row[3]

                print(f"\n매수 조건:")
                print(f"  최대 보유 종목: {buy_condition.get('max_holdings', 'N/A')}")
                print(f"  리밸런싱 주기: {buy_condition.get('rebalance_frequency', 'N/A')}")
                print(f"  포지션 크기: {buy_condition.get('position_sizing', 'N/A')}")

                print(f"\n매도 조건:")
                if 'hold_days' in sell_condition:
                    hold_days = sell_condition['hold_days']
                    print(f"  최소 보유일: {hold_days.get('min_hold_days', 'N/A')}")
                    print(f"  최대 보유일: {hold_days.get('max_hold_days', 'N/A')}")

            # 13번이 의미하는 것 추측
            print(f"\n" + "=" * 80)
            print(f"분석")
            print(f"=" * 80)
            print(f"""
13번 중복 거래 기록의 가능한 원인:

1. 포트폴리오 분할 (13개 섹션으로 분할)?
2. 루프가 13번 실행되는 버그?
3. DB INSERT가 13번 반복되는 버그?
4. executions 리스트에 13번 추가되는 버그?

2024-11-18은 첫 매수일이므로, 이날부터 문제가 시작되었을 가능성이 높습니다.
            """)

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "7d775ce4-2a8f-409a-bceb-1ff5dfb4a166"
    asyncio.run(check_positions(session_id))
