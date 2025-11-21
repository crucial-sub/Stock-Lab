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
from app.models.news import NewsArticle, ThemeSentiment
from app.models.theme import Theme
from app.models.user import User
from app.models.auto_trading import (
    AutoTradingStrategy,
    LivePosition,
    LiveTrade,
    LiveDailyPerformance,
    AutoTradingLog,
)

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

# 커뮤니티 모델
from app.models.community import (
    CommunityPost,
    CommunityComment,
    CommunityLike,
    CommunityCommentLike,
)

# 투자 전략 모델
from app.models.investment_strategy import InvestmentStrategy

__all__ = [
    # 기본 데이터 모델
    "Company",
    "StockPrice",
    "Disclosure",
    "FinancialStatement",
    "BalanceSheet",
    "IncomeStatement",
    "CashflowStatement",
    # 뉴스 모델
    "NewsArticle",
    "ThemeSentiment",
    "Theme",
    # 사용자 모델
    "User",
    # 자동매매 모델
    "AutoTradingStrategy",
    "LivePosition",
    "LiveTrade",
    "LiveDailyPerformance",
    "AutoTradingLog",
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
    # 백테스트 모델
    "BacktestSession",
    "BacktestCondition",
    "BacktestStatistics",
    "BacktestDailySnapshot",
    "BacktestTrade",
    "BacktestHolding",
    # 커뮤니티 모델
    "CommunityPost",
    "CommunityComment",
    "CommunityLike",
    "CommunityCommentLike",
    # 투자 전략 모델
    "InvestmentStrategy",
]
