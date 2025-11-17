"""
같은 날 매수/매도가 같은 횟수로 발생하는지 분석하는 스크립트
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'


async def analyze_same_day(session_id: str):
    """같은 날 매수/매도 분석"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. 같은 날 매수/매도 횟수가 같은 날 찾기
            result = await session.execute(text("""
                SELECT
                    trade_date,
                    SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) as buy_count,
                    SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END) as sell_count
                FROM simulation_trades
                WHERE session_id = :session_id
                GROUP BY trade_date
                HAVING SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) =
                       SUM(CASE WHEN trade_type = 'SELL' THEN 1 ELSE 0 END)
                   AND SUM(CASE WHEN trade_type = 'BUY' THEN 1 ELSE 0 END) > 0
                ORDER BY trade_date
            """), {"session_id": session_id})

            same_count_days = result.fetchall()

            if not same_count_days:
                print("✅ 같은 날 매수/매도 횟수가 같은 날이 없습니다!")
                return

            print(f"\n⚠️  같은 날 매수/매도 횟수가 같은 날: {len(same_count_days)}일\n")

            # 2. 각 날짜별로 상세 분석 (처음 5일만)
            overlap_count = 0
            for row in same_count_days[:5]:
                trade_date = row[0]
                buy_count = row[1]
                sell_count = row[2]

                print(f"\n{'='*80}")
                print(f"📅 {trade_date} - 매수: {buy_count}개, 매도: {sell_count}개")
                print(f"{'='*80}")

                # 해당 날짜의 거래 조회
                trades_result = await session.execute(text("""
                    SELECT
                        trade_type,
                        stock_code,
                        stock_name,
                        quantity,
                        price,
                        reason,
                        holding_days
                    FROM simulation_trades
                    WHERE session_id = :session_id
                        AND trade_date = :trade_date
                    ORDER BY trade_type DESC, stock_code
                """), {"session_id": session_id, "trade_date": trade_date})

                trades = trades_result.fetchall()

                # 매수/매도 종목 분리
                buy_stocks = set()
                sell_stocks = set()
                sell_reasons = {}

                print("\n매수 종목:")
                for trade in trades:
                    if trade[0] == 'BUY':
                        buy_stocks.add(trade[1])
                        print(f"  - {trade[1]} ({trade[2]}): {trade[3]}주 @ {trade[4]:,.0f}원")

                print("\n매도 종목:")
                for trade in trades:
                    if trade[0] == 'SELL':
                        sell_stocks.add(trade[1])
                        reason = trade[5] or 'UNKNOWN'
                        hold_days = trade[6] or 'N/A'
                        sell_reasons[reason] = sell_reasons.get(reason, 0) + 1
                        print(f"  - {trade[1]} ({trade[2]}): {trade[3]}주 @ {trade[4]:,.0f}원 [사유: {reason}, 보유: {hold_days}일]")

                # 겹치는 종목 확인
                overlap_stocks = buy_stocks & sell_stocks

                print(f"\n매도 사유 분포: {sell_reasons}")

                if overlap_stocks:
                    overlap_count += 1
                    print(f"\n❌ 같은 종목이 같은 날 매수/매도됨!")
                    print(f"🚨 겹치는 종목: {overlap_stocks}")
                    print("   → 이는 최소 보유기간 정책 위반입니다!")
                else:
                    print(f"\n✅ 매수/매도 종목이 서로 다릅니다.")
                    print(f"   매수 종목 {len(buy_stocks)}개 vs 매도 종목 {len(sell_stocks)}개")

            # 3. 요약
            print(f"\n{'='*80}")
            print(f"📊 분석 요약")
            print(f"{'='*80}")
            print(f"같은 날 매수/매도 횟수가 같은 날: {len(same_count_days)}일")
            print(f"그 중 같은 종목을 매수/매도한 날: {overlap_count}일 (분석한 {min(5, len(same_count_days))}일 중)")

            if overlap_count > 0:
                print(f"\n⚠️  {overlap_count}일에 같은 종목이 같은 날 매수/매도되었습니다!")
                print(f"   이는 최소 보유기간 정책을 위반한 것입니다.")
            else:
                print(f"\n✅ 분석한 날짜에서 매수/매도는 서로 다른 종목입니다.")
                print(f"   이는 리밸런싱 로직이 정상 작동하는 것입니다:")
                print(f"   - 조건 불만족 종목을 매도")
                print(f"   - 조건 만족하는 신규 종목을 매수")
                print(f"\n하지만 같은 날에 같은 횟수로 매수/매도가 발생하는 것은")
                print(f"다른 플랫폼과 다른 동작입니다.")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "7d775ce4-2a8f-409a-bceb-1ff5dfb4a166"
    asyncio.run(analyze_same_day(session_id))
