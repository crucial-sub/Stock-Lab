"""
모든 데이터베이스 테이블 생성 스크립트
"""
import asyncio
from app.core.database import engine, Base

# 모든 모델 import (테이블 생성을 위해 필수)
print("모델 import 중...")

from app.models.user import User
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.financial_statement import FinancialStatement
from app.models.income_statement import IncomeStatement
from app.models.balance_sheet import BalanceSheet
from app.models.cashflow_statement import CashflowStatement
from app.models.disclosure import Disclosure
from app.models.dividend import DividendInfo
from app.models.user_favorite_stock import UserFavoriteStock
from app.models.user_recent_stock import UserRecentStock
from app.models.news import NewsArticle, ThemeSentiment

# Simulation 모델들
try:
    from app.models.simulation import (
        SimulationSession,
        PortfolioStrategy,
        StrategyFactor,
        TradingRule,
        SimulationStatistics,
        SimulationDailyValue,
        SimulationTrade,
        Factor,
        FactorCategory
    )
    print("OK - Simulation models imported")
except Exception as e:
    print(f"WARNING - Simulation models import failed: {e}")

# Auto-trading 모델들
try:
    from app.models.auto_trading import (
        AutoTradingStrategy,
        LivePosition,
        LiveTrade,
        LiveDailyPerformance,
        AutoTradingLog
    )
    print("OK - Auto-trading models imported")
except Exception as e:
    print(f"WARNING - Auto-trading models import failed: {e}")

print("OK - All models imported")


async def create_tables():
    """모든 테이블 생성"""
    print("\nCreating database tables...")

    async with engine.begin() as conn:
        # 모든 테이블 생성
        await conn.run_sync(Base.metadata.create_all)

    print("\nSUCCESS - Database tables created!")
    print(f"\nCreated tables ({len(Base.metadata.tables)}):")
    for table in sorted(Base.metadata.tables.keys()):
        print(f"  - {table}")


async def drop_all_tables():
    """모든 테이블 삭제 (주의!)"""
    print("\nWARNING: Dropping all tables!")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("SUCCESS - All tables dropped.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        # python create_all_tables.py --drop
        asyncio.run(drop_all_tables())
    else:
        # python create_all_tables.py
        asyncio.run(create_tables())
