import asyncio
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

# 동기 엔진 생성
engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
    echo=False
)

session_id = "340710a9-66ea-4670-a490-e77be54c5088"

with engine.connect() as conn:
    # 1. 세션 정보 확인
    print("=" * 80)
    print("1. 세션 정보:")
    result = conn.execute(text("""
        SELECT session_id, status, initial_capital, final_value, total_return
        FROM simulation_sessions
        WHERE session_id = :session_id
    """), {"session_id": session_id})
    row = result.fetchone()
    if row:
        print(f"  session_id: {row[0]}")
        print(f"  status: {row[1]}")
        print(f"  initial_capital: {row[2]}")
        print(f"  final_value: {row[3]}")
        print(f"  total_return: {row[4]}")
    else:
        print("  세션을 찾을 수 없습니다!")

    # 2. 통계 정보 확인
    print("\n" + "=" * 80)
    print("2. 통계 정보:")
    result = conn.execute(text("""
        SELECT total_return, final_capital, total_trades, winning_trades, losing_trades
        FROM simulation_statistics
        WHERE session_id = :session_id
    """), {"session_id": session_id})
    row = result.fetchone()
    if row:
        print(f"  total_return: {row[0]}")
        print(f"  final_capital: {row[1]}")
        print(f"  total_trades: {row[2]}")
        print(f"  winning_trades: {row[3]}")
        print(f"  losing_trades: {row[4]}")
    else:
        print("  통계를 찾을 수 없습니다!")

    # 3. 일별 가치 데이터 확인 (처음 5개, 마지막 5개)
    print("\n" + "=" * 80)
    print("3. 일별 가치 데이터 (처음 5개):")
    result = conn.execute(text("""
        SELECT date, portfolio_value, cash, position_value, daily_return, cumulative_return
        FROM simulation_daily_values
        WHERE session_id = :session_id
        ORDER BY date
        LIMIT 5
    """), {"session_id": session_id})
    for row in result:
        print(f"  {row[0]}: portfolio={row[1]}, cash={row[2]}, position={row[3]}, daily_ret={row[4]}, cum_ret={row[5]}")

    print("\n일별 가치 데이터 (마지막 5개):")
    result = conn.execute(text("""
        SELECT date, portfolio_value, cash, position_value, daily_return, cumulative_return
        FROM simulation_daily_values
        WHERE session_id = :session_id
        ORDER BY date DESC
        LIMIT 5
    """), {"session_id": session_id})
    for row in result:
        print(f"  {row[0]}: portfolio={row[1]}, cash={row[2]}, position={row[3]}, daily_ret={row[4]}, cum_ret={row[5]}")

    # 4. 거래 내역 확인 (SELL 거래만)
    print("\n" + "=" * 80)
    print("4. 매도 거래 내역 (처음 10개):")
    result = conn.execute(text("""
        SELECT trade_date, stock_code, trade_type, price, quantity, realized_pnl, return_pct
        FROM simulation_trades
        WHERE session_id = :session_id AND trade_type = 'SELL'
        ORDER BY trade_date DESC
        LIMIT 10
    """), {"session_id": session_id})
    count = 0
    for row in result:
        print(f"  {row[0]}: {row[1]} {row[2]} @ {row[3]}원, 수량={row[4]}, PnL={row[5]}, 수익률={row[6]}%")
        count += 1
    print(f"\n  총 매도 거래 수: {count}")

    # 5. 전체 거래 수 확인
    result = conn.execute(text("""
        SELECT trade_type, COUNT(*)
        FROM simulation_trades
        WHERE session_id = :session_id
        GROUP BY trade_type
    """), {"session_id": session_id})
    print("\n전체 거래 수:")
    for row in result:
        print(f"  {row[0]}: {row[1]}건")

print("\n" + "=" * 80)
