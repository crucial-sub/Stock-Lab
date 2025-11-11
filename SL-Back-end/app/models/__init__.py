"""
데이터베이스 모델
ERD_GUIDE.md 기반으로 구성된 테이블 모델
"""
from app.models.company import Company
from app.models.stock_price import StockPrice
from app.models.disclosure import Disclosure
from app.models.financial_statement import FinancialStatement
from app.models.balance_sheet import BalanceSheet
from app.models.income_statement import IncomeStatement
from app.models.cashflow_statement import CashflowStatement
from app.models.user import User

# 백테스팅 시뮬레이션 모델
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
    SimulationPosition,
)

# 백테스트 결과 저장 모델
from app.models.backtest import (
    BacktestSession,
    BacktestCondition,
    BacktestStatistics,
    BacktestDailySnapshot,
    BacktestTrade,
    BacktestHolding,
)

__all__ = [
    # 기본 데이터 모델
    "Company",
    "StockPrice",
    "Disclosure",
    "FinancialStatement",
    "BalanceSheet",
    "IncomeStatement",
    "CashflowStatement",
    "User",
    # 시뮬레이션 모델
    "FactorCategory",
    "Factor",
    "PortfolioStrategy",
    "StrategyFactor",
    "TradingRule",
    "SimulationSession",
    "SimulationStatistics",
    "SimulationDailyValue",
    "SimulationTrade",
    "SimulationPosition",
]
