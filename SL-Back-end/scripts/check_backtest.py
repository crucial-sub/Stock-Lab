"""
백테스트 결과 조회 스크립트
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def check_backtest(session_id: str):
    """백테스트 결과 조회"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. 세션 정보 조회
            print(f"\n🔍 백테스트 세션 정보 (ID: {session_id})\n")
            result = await session.execute(text("""
                SELECT
                    session_id,
                    strategy_id,
                    start_date,
                    end_date,
                    status,
                    created_at
                FROM simulation_sessions
                WHERE session_id = :session_id
            """), {"session_id": session_id})

            session_row = result.fetchone()
            if not session_row:
                print(f"❌ 세션을 찾을 수 없습니다: {session_id}")
                return

            print(f"Strategy ID: {session_row[1]}")
            print(f"기간: {session_row[2]} ~ {session_row[3]}")
            print(f"상태: {session_row[4]}")
            print(f"생성일: {session_row[5]}")

            strategy_id = session_row[1]

            # 2. 매매 규칙 조회
            print(f"\n📋 매매 규칙 정보\n")
            result = await session.execute(text("""
                SELECT
                    buy_condition,
                    sell_condition
                FROM trading_rules
                WHERE strategy_id = :strategy_id
            """), {"strategy_id": strategy_id})

            rule_row = result.fetchone()
            if rule_row:
                buy_condition = rule_row[0]
                sell_condition = rule_row[1]

                # 보유기간 설정 확인
                if sell_condition and 'hold_days' in sell_condition:
                    hold_days = sell_condition['hold_days']
                    print(f"최소 보유일: {hold_days.get('min_hold_days', 'N/A')}")
                    print(f"최대 보유일: {hold_days.get('max_hold_days', 'N/A')}")

                # 리밸런싱 설정
                if buy_condition:
                    print(f"리밸런싱 주기: {buy_condition.get('rebalance_frequency', 'N/A')}")
                    print(f"최대 보유 종목: {buy_condition.get('max_holdings', 'N/A')}")

            # 3. 일별 거래 집계 (매수/매도 횟수)
            print(f"\n📊 일별 매수/매도 횟수 (상위 30일)\n")
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) as buy_count,
                    SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END) as sell_count,
                    COUNT(*) as total_count
                FROM simulation_trades
                WHERE session_id = :session_id
                GROUP BY trade_date
                HAVING SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) > 0
                    OR SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END) > 0
                ORDER BY trade_date
                LIMIT 30
            """), {"session_id": session_id})

            print(f"{'날짜':<12} {'매수':<8} {'매도':<8} {'총거래':<8}")
            print("-" * 45)

            identical_count = 0
            for row in result.fetchall():
                date_str = str(row[0])
                buy = row[1]
                sell = row[2]
                total = row[3]

                marker = "⚠️ " if buy == sell and buy > 0 else "   "
                print(f"{marker}{date_str:<12} {buy:<8} {sell:<8} {total:<8}")

                if buy == sell and buy > 0:
                    identical_count += 1

            print(f"\n⚠️  매수=매도 동일한 날: {identical_count}일")

            # 4. 매도 사유별 집계
            print(f"\n📈 매도 사유별 집계\n")
            result = await session.execute(text("""
                SELECT
                    reason,
                    COUNT(*) as count,
                    AVG(holding_days) as avg_hold_days
                FROM simulation_trades
                WHERE session_id = :session_id
                AND trade_type = 'SELL'
                AND reason IS NOT NULL
                GROUP BY reason
                ORDER BY count DESC
            """), {"session_id": session_id})

            print(f"{'매도 사유':<40} {'횟수':<10} {'평균 보유일':<12}")
            print("-" * 65)

            for row in result.fetchall():
                reason = row[0]
                count = row[1]
                avg_days = row[2] or 0
                print(f"{reason:<40} {count:<10} {avg_days:<12.1f}")

            # 5. 보유일수 분포 (매도된 종목)
            print(f"\n📊 보유일수 분포\n")
            result = await session.execute(text("""
                SELECT
                    holding_days,
                    COUNT(*) as count
                FROM simulation_trades
                WHERE session_id = :session_id
                AND trade_type = 'SELL'
                AND holding_days IS NOT NULL
                GROUP BY holding_days
                ORDER BY holding_days
                LIMIT 15
            """), {"session_id": session_id})

            print(f"{'보유일수':<10} {'거래 횟수':<10}")
            print("-" * 25)

            less_than_5 = 0
            for row in result.fetchall():
                days = row[0]
                count = row[1]
                marker = "⚠️ " if days < 5 else "   "
                print(f"{marker}{days:<10} {count:<10}")
                if days < 5:
                    less_than_5 += count

            if less_than_5 > 0:
                print(f"\n⚠️  최소 보유일(5일) 미달 거래: {less_than_5}건")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "4d121b86-a27f-45b5-9ddd-a407e1f55cf5"
    asyncio.run(check_backtest(session_id))
