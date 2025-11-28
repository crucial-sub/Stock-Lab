import asyncio
import asyncpg
import os

async def main():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'sl-db.c5ms84tq4qp8.ap-northeast-2.rds.amazonaws.com'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'sluser'),
        password=os.getenv('DB_PASSWORD', 'nmmteam05'),
        database=os.getenv('DB_NAME', 'sldb')
    )

    rows = await conn.fetch('''
        SELECT trade_id, trade_date, trade_type, stock_code, stock_name, quantity, price, profit
        FROM live_trades
        WHERE strategy_id = 'a2e8e4cc-e88b-4cb6-b33d-246260073d7b'
        ORDER BY trade_date DESC, created_at DESC
        LIMIT 30
    ''')

    print(f"{'Trade ID':<36} | {'Date':<10} | {'Type':<4} | {'Code':<6} | {'Name':<12} | {'Qty':>4} | {'Price':>10} | {'Profit':>10}")
    print("-" * 120)
    for row in rows:
        print(f"{row['trade_id']} | {row['trade_date']} | {row['trade_type']:<4} | {row['stock_code']:<6} | {row['stock_name']:<12} | {row['quantity']:>4} | {row['price']:>10.0f} | {row['profit'] if row['profit'] else 0:>10.0f}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
