"""
가상매매 전략 테이블에 백테스트 조건 컬럼 추가
- 매수/매도 조건을 백테스트와 완전히 동기화
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# DATABASE_URL 설정
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://postgres:postgres123@localhost:5433/stock_lab_investment_db'
)


async def add_auto_trading_conditions():
    """가상매매 전략 테이블에 백테스트 조건 컬럼 추가"""

    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            print("\n🚀 가상매매 전략 테이블 마이그레이션 시작...\n")

            # 매수 조건 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS buy_conditions JSONB,
                ADD COLUMN IF NOT EXISTS buy_logic VARCHAR(500),
                ADD COLUMN IF NOT EXISTS priority_factor VARCHAR(50),
                ADD COLUMN IF NOT EXISTS priority_order VARCHAR(10) DEFAULT 'desc',
                ADD COLUMN IF NOT EXISTS max_buy_value DECIMAL(20, 2),
                ADD COLUMN IF NOT EXISTS max_daily_stock INTEGER,
                ADD COLUMN IF NOT EXISTS buy_price_basis VARCHAR(20) DEFAULT '전일 종가',
                ADD COLUMN IF NOT EXISTS buy_price_offset DECIMAL(10, 4) DEFAULT 0
            """))
            print("✅ 매수 조건 컬럼 추가 완료")

            # 매도 조건 - 목표가/손절가 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS target_gain DECIMAL(10, 4),
                ADD COLUMN IF NOT EXISTS stop_loss DECIMAL(10, 4)
            """))
            print("✅ 목표가/손절가 컬럼 추가 완료")

            # 매도 조건 - 보유 기간 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS min_hold_days INTEGER,
                ADD COLUMN IF NOT EXISTS max_hold_days INTEGER,
                ADD COLUMN IF NOT EXISTS hold_days_sell_price_basis VARCHAR(20),
                ADD COLUMN IF NOT EXISTS hold_days_sell_price_offset DECIMAL(10, 4)
            """))
            print("✅ 보유 기간 컬럼 추가 완료")

            # 매도 조건 - 조건 매도 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS sell_conditions JSONB,
                ADD COLUMN IF NOT EXISTS sell_logic VARCHAR(500),
                ADD COLUMN IF NOT EXISTS condition_sell_price_basis VARCHAR(20),
                ADD COLUMN IF NOT EXISTS condition_sell_price_offset DECIMAL(10, 4)
            """))
            print("✅ 조건 매도 컬럼 추가 완료")

            # 수수료/슬리피지 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS commission_rate DECIMAL(10, 6) DEFAULT 0.00015,
                ADD COLUMN IF NOT EXISTS slippage DECIMAL(10, 6) DEFAULT 0.001
            """))
            print("✅ 수수료/슬리피지 컬럼 추가 완료")

            # 매매 대상 컬럼 추가
            await session.execute(text("""
                ALTER TABLE auto_trading_strategies
                ADD COLUMN IF NOT EXISTS trade_targets JSONB
            """))
            print("✅ 매매 대상 컬럼 추가 완료")

            await session.commit()
            print("\n✅ 마이그레이션 완료!\n")

        except Exception as e:
            print(f"\n❌ 마이그레이션 실패: {e}\n")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(add_auto_trading_conditions())
