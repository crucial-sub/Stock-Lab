"""
Initialize database tables
"""
import asyncio
import sys
from app.core.database import engine, Base, init_db
from app.models.simulation import (
    FactorCategory,
    Factor,
    PortfolioStrategy,
    StrategyFactor,
    TradingRule,
    SimulationSession,
    SimulationStatistics,
    SimulationDailyValue,
    SimulationTrade,
    SimulationPosition
)
# Import only the models that exist
# from app.models.company import Company
# from app.models.stock_price import StockPrice
# from app.models.financial_statement import FinancialStatement
# from app.models.income_statement import IncomeStatement
# from app.models.balance_sheet import BalanceSheet
# from app.models.cashflow_statement import CashflowStatement
# from app.models.dividend import Dividend
# from app.models.disclosure import Disclosure
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables"""
    try:
        logger.info("Starting database initialization...")

        # Create tables
        async with engine.begin() as conn:
            # Drop existing tables (optional, only for development)
            # await conn.run_sync(Base.metadata.drop_all)

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ All tables created successfully")

        # Initialize factor categories
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # Check if data already exists
            from sqlalchemy import select
            result = await session.execute(select(FactorCategory))
            existing = result.scalars().first()

            if not existing:
                # Insert default factor categories
                categories = [
                    FactorCategory(
                        category_id="value",
                        category_name="가치",
                        description="가치 투자 관련 팩터",
                        display_order=1
                    ),
                    FactorCategory(
                        category_id="growth",
                        category_name="성장",
                        description="성장성 관련 팩터",
                        display_order=2
                    ),
                    FactorCategory(
                        category_id="profitability",
                        category_name="수익성",
                        description="수익성 관련 팩터",
                        display_order=3
                    ),
                    FactorCategory(
                        category_id="momentum",
                        category_name="모멘텀",
                        description="가격 모멘텀 관련 팩터",
                        display_order=4
                    ),
                    FactorCategory(
                        category_id="quality",
                        category_name="퀄리티",
                        description="기업 품질 관련 팩터",
                        display_order=5
                    ),
                    FactorCategory(
                        category_id="stability",
                        category_name="안정성",
                        description="재무 안정성 관련 팩터",
                        display_order=6
                    ),
                    FactorCategory(
                        category_id="liquidity",
                        category_name="유동성",
                        description="거래 유동성 관련 팩터",
                        display_order=7
                    ),
                    FactorCategory(
                        category_id="technical",
                        category_name="기술적",
                        description="기술적 분석 팩터",
                        display_order=8
                    ),
                    FactorCategory(
                        category_id="size",
                        category_name="규모",
                        description="기업 규모 관련 팩터",
                        display_order=9
                    ),
                    FactorCategory(
                        category_id="risk",
                        category_name="리스크",
                        description="리스크 관련 팩터",
                        display_order=10
                    )
                ]

                for category in categories:
                    session.add(category)

                # Insert default factors
                factors = [
                    # Value factors
                    Factor(factor_id="PER", category_id="value", factor_name="주가수익비율",
                          calculation_type="FUNDAMENTAL", description="Price to Earnings Ratio"),
                    Factor(factor_id="PBR", category_id="value", factor_name="주가순자산비율",
                          calculation_type="FUNDAMENTAL", description="Price to Book Ratio"),
                    Factor(factor_id="EV_EBITDA", category_id="value", factor_name="EV/EBITDA",
                          calculation_type="FUNDAMENTAL", description="Enterprise Value to EBITDA"),
                    Factor(factor_id="DIV_YIELD", category_id="value", factor_name="배당수익률",
                          calculation_type="FUNDAMENTAL", description="Dividend Yield"),

                    # Growth factors
                    Factor(factor_id="REVENUE_GROWTH", category_id="growth", factor_name="매출성장률",
                          calculation_type="FUNDAMENTAL", description="Revenue Growth Rate"),
                    Factor(factor_id="EARNINGS_GROWTH", category_id="growth", factor_name="이익성장률",
                          calculation_type="FUNDAMENTAL", description="Earnings Growth Rate"),

                    # Profitability factors
                    Factor(factor_id="ROE", category_id="profitability", factor_name="자기자본이익률",
                          calculation_type="FUNDAMENTAL", description="Return on Equity"),
                    Factor(factor_id="ROA", category_id="profitability", factor_name="총자산이익률",
                          calculation_type="FUNDAMENTAL", description="Return on Assets"),
                    Factor(factor_id="GP_A", category_id="quality", factor_name="매출총이익률",
                          calculation_type="FUNDAMENTAL", description="Gross Profitability"),

                    # Momentum factors
                    Factor(factor_id="MOMENTUM_1M", category_id="momentum", factor_name="1개월 모멘텀",
                          calculation_type="TECHNICAL", description="1 Month Price Momentum"),
                    Factor(factor_id="MOMENTUM_3M", category_id="momentum", factor_name="3개월 모멘텀",
                          calculation_type="TECHNICAL", description="3 Month Price Momentum"),
                    Factor(factor_id="MOMENTUM_6M", category_id="momentum", factor_name="6개월 모멘텀",
                          calculation_type="TECHNICAL", description="6 Month Price Momentum"),
                    Factor(factor_id="MOMENTUM_12M", category_id="momentum", factor_name="12개월 모멘텀",
                          calculation_type="TECHNICAL", description="12 Month Price Momentum"),

                    # Stability factors
                    Factor(factor_id="DEBT_RATIO", category_id="stability", factor_name="부채비율",
                          calculation_type="FUNDAMENTAL", description="Debt to Equity Ratio"),
                    Factor(factor_id="CURRENT_RATIO", category_id="stability", factor_name="유동비율",
                          calculation_type="FUNDAMENTAL", description="Current Ratio"),

                    # Risk factors
                    Factor(factor_id="VOLATILITY", category_id="risk", factor_name="변동성",
                          calculation_type="TECHNICAL", description="Price Volatility"),
                    Factor(factor_id="BETA", category_id="risk", factor_name="베타",
                          calculation_type="TECHNICAL", description="Market Beta"),

                    # Liquidity factors
                    Factor(factor_id="TRADING_VOLUME", category_id="liquidity", factor_name="거래량",
                          calculation_type="TECHNICAL", description="Trading Volume"),

                    # Size factors
                    Factor(factor_id="MARKET_CAP", category_id="size", factor_name="시가총액",
                          calculation_type="FUNDAMENTAL", description="Market Capitalization"),

                    # Technical factors
                    Factor(factor_id="RSI", category_id="technical", factor_name="RSI",
                          calculation_type="TECHNICAL", description="Relative Strength Index")
                ]

                for factor in factors:
                    session.add(factor)

                await session.commit()
                logger.info("✅ Default factor categories and factors inserted")
            else:
                logger.info("ℹ️ Factor categories already exist, skipping initialization")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())