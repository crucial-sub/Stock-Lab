"""실시간 진행 상황 컬럼 추가 스크립트"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def add_realtime_columns():
    DATABASE_URL = "postgresql+asyncpg://stocklabadmin:nmmteam05@sl-postgres-db.cl0gcamkufcq.ap-northeast-2.rds.amazonaws.com:5432/stock_lab_investment_db"

    engine = create_async_engine(DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            # 컬럼 하나씩 추가
            await conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_date DATE"))
            print("✅ current_date 컬럼 추가")

            await conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS buy_count INTEGER DEFAULT 0"))
            print("✅ buy_count 컬럼 추가")

            await conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS sell_count INTEGER DEFAULT 0"))
            print("✅ sell_count 컬럼 추가")

            await conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_return DECIMAL(10, 4)"))
            print("✅ current_return 컬럼 추가")

            await conn.execute(text("ALTER TABLE simulation_sessions ADD COLUMN IF NOT EXISTS current_capital DECIMAL(15, 2)"))
            print("✅ current_capital 컬럼 추가")

        print("\n✅ 모든 실시간 진행 컬럼 추가 완료!")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_realtime_columns())
