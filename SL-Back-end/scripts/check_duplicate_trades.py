"""
중복 거래 기록을 확인하는 스크립트
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def check_duplicates(session_id: str):
    """중복 거래 기록 확인"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. 같은 날짜, 같은 종목, 같은 거래 유형에 대한 중복 확인
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    stock_code,
                    stock_name,
                    trade_type,
                    COUNT(*) as count,
                    SUM(quantity) as total_quantity,
                    AVG(price) as avg_price,
                    STRING_AGG(DISTINCT reason, ', ') as reasons
                FROM simulation_trades
                WHERE session_id = :session_id
                GROUP BY trade_date, stock_code, stock_name, trade_type
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC, trade_date
                LIMIT 20
            """), {"session_id": session_id})

            duplicates = result.fetchall()

            if not duplicates:
                print("✅ 중복 거래 기록이 없습니다!")
                return

            print(f"\n⚠️  중복 거래 기록 발견: {len(duplicates)}건\n")
            print(f"{'날짜':<12} {'종목코드':<10} {'종목명':<20} {'유형':<6} {'횟수':<6} {'총수량':<10} {'평균가':<12} {'사유':<30}")
            print("=" * 130)

            for row in duplicates:
                trade_date = str(row[0])
                stock_code = row[1]
                stock_name = row[2][:18] if row[2] else 'N/A'
                trade_type = row[3]
                count = row[4]
                total_qty = row[5]
                avg_price = float(row[6]) if row[6] else 0
                reasons = row[7] or 'N/A'

                print(f"{trade_date:<12} {stock_code:<10} {stock_name:<20} {trade_type:<6} {count:<6} {total_qty:<10} {avg_price:<12,.0f} {reasons:<30}")

            # 2. 특정 날짜의 상세 거래 내역 확인 (2024-11-25)
            print(f"\n{'='*130}")
            print(f"📅 2024-11-25 상세 거래 내역 (045340 - 토탈소프트)")
            print(f"{'='*130}\n")

            result = await session.execute(text("""
                SELECT
                    trade_type,
                    quantity,
                    price,
                    amount,
                    reason,
                    holding_days
                FROM simulation_trades
                WHERE session_id = :session_id
                    AND trade_date = '2024-11-25'
                    AND stock_code = '045340'
                ORDER BY trade_type DESC
            """), {"session_id": session_id})

            trades = result.fetchall()

            buy_count = 0
            sell_count = 0
            buy_total_qty = 0
            sell_total_qty = 0

            for trade in trades:
                trade_type = trade[0]
                qty = trade[1]
                price = float(trade[2])
                amount = float(trade[3]) if trade[3] else 0
                reason = trade[4] or 'N/A'
                hold_days = trade[5] or 'N/A'

                if trade_type == 'BUY':
                    buy_count += 1
                    buy_total_qty += qty
                else:
                    sell_count += 1
                    sell_total_qty += qty

                print(f"{trade_type:<6} {qty:>8}주 @ {price:>10,.0f}원 = {amount:>15,.0f}원 [사유: {reason}, 보유: {hold_days}일]")

            print(f"\n매수: {buy_count}건, 총 {buy_total_qty:,}주")
            print(f"매도: {sell_count}건, 총 {sell_total_qty:,}주")

            if buy_count > 1:
                print(f"\n⚠️  매수가 {buy_count}번 기록되었습니다!")
                print(f"   이는 버그일 가능성이 높습니다.")
                print(f"   정상적으로는 1번의 매수 기록만 있어야 합니다.")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "7d775ce4-2a8f-409a-bceb-1ff5dfb4a166"
    asyncio.run(check_duplicates(session_id))
