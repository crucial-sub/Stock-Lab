# Stock Lab Backend - Backtest System Documentation

## Overview

This directory contains comprehensive documentation for the Stock Lab backend's backtesting system implementation. The backtest engine is a sophisticated quantitative trading simulator that validates portfolio strategies based on historical market data.

**Project**: PROJ-40-Back-Test-고도화  
**Location**: `/Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end`  
**Implementation Size**: ~3,850 lines of core code  
**Database**: PostgreSQL with 10+ simulation tables

---

## Documentation Files

### 1. BACKTEST_ANALYSIS.md (22 KB - 770 lines)
**Comprehensive Technical Guide**

The main reference document covering all aspects of the backtest implementation:

- **Architecture Overview** - File structure, technology stack, design patterns
- **Database Schema** - 10 main tables with relationships and constraints
- **Request Processing** - How user requests are validated and transformed
- **Advanced Backtest Engine** - QuantBacktestEngine class design and methods
- **Factor Calculation** - 20+ supported factors with formulas and normalization
- **Stock Selection** - Screening, scoring, and ranking algorithms
- **Portfolio Rebalancing** - Frequency triggers and rebalancing logic
- **Trading Mechanics** - Buy/sell execution with costs and P&L calculations
- **Daily Valuation** - Portfolio mark-to-market and return calculations
- **Statistical Calculations** - Risk metrics (volatility, Sharpe, MDD)
- **REST API Endpoints** - All 8 endpoints with request/response formats
- **Implementation Details** - Universe selection, condition parsing, status management
- **Data Flow Diagram** - Visual representation of execution flow
- **Performance Considerations** - Optimizations and bottlenecks
- **Enhancement Opportunities** - Future improvements and extensions

**Use this document when**: You need detailed explanations of how specific parts work, want to understand the mathematical formulas, or need to debug issues.

---

### 2. BACKTEST_QUICK_REFERENCE.md (10 KB - 320 lines)
**Developer Quick Reference**

A condensed reference guide for developers implementing or modifying the system:

- **File Locations & LOC** - Quick lookup of key files and their sizes
- **Database Tables** - List of 10 main simulation tables
- **API Endpoints** - All endpoints with brief descriptions
- **QuantBacktestEngine Methods** - Method hierarchy and call tree
- **Key Algorithms** - Pseudocode for major processes
- **Data Types & Precision** - Decimal handling and type conversions
- **Costs & Rates** - Commission, tax, and risk-free rate constants
- **Factor Categories** - Fundamental, technical, and custom factors
- **Rebalance Triggers** - When rebalancing occurs
- **Position Sizing** - EQUAL_WEIGHT, MARKET_CAP, RISK_PARITY
- **Execution Flow Timeline** - Step-by-step execution with time estimates
- **Common Queries** - Frequently used SQL patterns
- **Performance Notes** - Current limitations and optimization tips
- **Testing Checklist** - Critical areas to test
- **Common Issues & Fixes** - Troubleshooting table

**Use this document when**: You need quick lookups, want to find method signatures, or need a refresher on how something works.

---

### 3. BACKTEST_SUMMARY.txt (14 KB - 345 lines)
**Executive Summary**

High-level overview for stakeholders and team members:

- **Executive Summary** - What the system does and its key features
- **Key Findings** - 6 major aspects of the architecture
- **Critical Implementation Details** - Factor formulas, portfolio valuation, statistics, costs, position sizing
- **API Endpoints** - Quick list of 8 main endpoints
- **Execution Flow** - 4-step process from request to results
- **Database Schema** - 10 main tables at a glance
- **Key Algorithms** - Pseudocode for major processes
- **Performance Characteristics** - Runtime, memory, bottlenecks
- **Testing & Validation** - What to test and known edge cases
- **Recommendations** - Short/medium/long-term enhancements
- **Conclusion** - System strengths and readiness

**Use this document when**: You need to brief someone on the system, want an executive overview, or need to justify architectural decisions.

---

## Quick Start: Understanding the Codebase

### For New Developers:
1. Start with **BACKTEST_SUMMARY.txt** (5 min read)
2. Review **BACKTEST_QUICK_REFERENCE.md** - Methods section (10 min)
3. Dive into **BACKTEST_ANALYSIS.md** - Section 4 (QuantBacktestEngine)
4. Read the actual code: `app/services/advanced_backtest.py`

### For Implementing Features:
1. Check **BACKTEST_QUICK_REFERENCE.md** - Methods section
2. Find relevant section in **BACKTEST_ANALYSIS.md**
3. Locate the method in source code
4. Review inline comments and docstrings

### For Debugging Issues:
1. Check **BACKTEST_QUICK_REFERENCE.md** - Common Issues section
2. Review **BACKTEST_ANALYSIS.md** - Error Handling section
3. Enable DEBUG logging in the code
4. Use provided query examples

---

## File Structure Reference

```
SL-Back-end/
├── app/
│   ├── api/routes/
│   │   └── backtest.py                 # REST API endpoints (780 lines)
│   │       - POST /backtest/run
│   │       - GET /backtest/{id}/status
│   │       - GET /backtest/{id}/result
│   │       - GET /backtest/{id}/trades
│   │       - GET /factors/list
│   │
│   ├── services/
│   │   └── advanced_backtest.py        # Core engine (2081 lines)
│   │       - QuantBacktestEngine class
│   │       - Daily trading loop
│   │       - Factor calculations
│   │       - Portfolio rebalancing
│   │       - Statistics computation
│   │
│   ├── models/
│   │   └── simulation.py               # ORM models (394 lines)
│   │       - SimulationSession
│   │       - SimulationStatistics
│   │       - SimulationDailyValue
│   │       - SimulationTrade
│   │       - PortfolioStrategy
│   │       - StrategyFactor
│   │       - TradingRule
│   │
│   ├── schemas/
│   │   ├── simulation.py               # Pydantic schemas (316 lines)
│   │   │   - BacktestRequest
│   │   │   - BacktestResponse
│   │   │   - BacktestResultResponse
│   │   │
│   │   └── factor.py                   # Factor schemas (277 lines)
│   │       - FactorValue, FactorResponse
│   │       - Individual factor DTOs
│   │
│   └── core/
│       └── database.py                 # SQLAlchemy setup
│
├── check_backtest.py                   # Verification utility
├── create_tables.py                    # Schema creation
└── requirements.txt                    # Dependencies
```

---

## Key Components Summary

### Database (10 Tables)
1. **factor_categories** - Factor groupings
2. **factors** - Individual factor definitions
3. **portfolio_strategies** - Strategy configs
4. **strategy_factors** - Factor assignments
5. **trading_rules** - Buy/sell/rebalance rules
6. **simulation_sessions** - Backtest runs
7. **simulation_statistics** - Results aggregates
8. **simulation_daily_values** - Daily snapshots
9. **simulation_trades** - Individual trades
10. **simulation_positions** - Position snapshots

### REST API (8 Endpoints)
- `POST /backtest/run` - Start backtest
- `GET /backtest/{id}/status` - Check progress
- `GET /backtest/{id}/result` - Get results
- `GET /backtest/{id}/trades` - Get trades (paginated)
- `GET /backtest/list` - List backtests
- `GET /factors/list` - Available factors
- `GET /sub-factors/list` - Operators & functions
- `GET /themes/list` - Korean industry sectors

### Core Classes
- **QuantBacktestEngine** - Main simulation engine (2081 lines)
- **BacktestRequest** - Input validation schema
- **BacktestResultResponse** - Output format
- **SimulationSession, Trade, DailyValue** - Data models

### Supported Features
- **20+ Factors**: PER, PBR, ROE, ROA, DIV_YIELD, Momentum, Volatility, etc.
- **Rebalance Frequencies**: DAILY, WEEKLY, MONTHLY, QUARTERLY
- **Position Sizing**: EQUAL_WEIGHT, MARKET_CAP, RISK_PARITY
- **Risk Controls**: Stop-loss, Take-profit, Max positions
- **Real Costs**: 0.015% commission, 0.23% Korean tax
- **Statistics**: Total return, volatility, Sharpe ratio, Max drawdown

---

## Key Formulas

### Factor Calculations
```
PER = Price / (Net Income / Shares Outstanding)
PBR = Price / (Total Equity / Shares Outstanding)
ROE = Net Income / Total Equity × 100%
DIV_YIELD = Annual Dividend / Price × 100%
Momentum = (Current Price - Price N days ago) / Price N days ago × 100%
Volatility = std(daily returns) × √252 × 100% (annualized)
```

### Portfolio Valuation
```
Portfolio Value = Cash + Position Value
Position Value = Σ(current_price × quantity)
Daily Return = ((V_t - V_t-1) / V_t-1) × 100%
Cumulative Return = ((V_final - V_initial) / V_initial) × 100%
```

### Risk Metrics
```
Total Return = ((final - initial) / initial) × 100%
Volatility = daily_returns.std() × √252 × 100% (annualized)
Max Drawdown = minimum((value - cummax) / cummax) × 100%
Sharpe Ratio = (mean(excess_return) / std(daily_return)) × √252
  where excess_return = daily_return - 2%/252 (risk-free rate)
```

---

## Technology Stack

- **Framework**: FastAPI (async/await, OpenAPI)
- **ORM**: SQLAlchemy (async & sync modes)
- **Database**: PostgreSQL
- **Data Processing**: Polars (fast), Pandas (stats), NumPy (vectorization)
- **Precision**: Decimal type (no floating-point errors)
- **Async**: ThreadPoolExecutor for background backtests

---

## Performance Characteristics

### Typical Backtest
- Duration: 250 trading days
- Universe: 100-500 stocks
- Holdings: 10-20 positions
- Rebalance: Monthly

### Runtime & Resources
- Time: 30 seconds to 5 minutes
- Memory: 100-200 MB
- Database: 5,000-10,000 records

### Bottlenecks
1. Factor calculation: O(stocks × factors)
2. SQL queries: Multiple per position
3. Daily commits: Durable writes
4. Polars operations: Linear in stock count

---

## Testing & Validation

### Critical Test Areas
- Buy condition parsing (Korean/English factor names)
- Theme/industry filtering accuracy
- Stop-loss & take-profit triggers
- Position sizing calculations
- Statistics accuracy (verify manually)
- Trade matching (FIFO correctness)
- Database integrity (constraints, cascades)

### Known Edge Cases
- Missing price data → Skip operation (log as DEBUG)
- Insufficient cash → Reduce position size automatically
- Dividend table missing → DIV_YIELD returns 0
- Outlier factors → Z-score normalization handles

---

## Enhancement Opportunities

### Short-term (High Priority)
- [ ] Price caching to reduce SQL queries
- [ ] Multi-factor UI for condition building
- [ ] Actual benchmark returns comparison

### Medium-term (Medium Priority)
- [ ] Batch SQL queries for factors
- [ ] Custom formula parser
- [ ] Sector concentration limits
- [ ] Parallel factor calculations

### Long-term (Nice to Have)
- [ ] RSI, MACD, Bollinger Bands indicators
- [ ] Correlation-based position limits
- [ ] Alpha/beta calculation
- [ ] Monte Carlo out-of-sample testing
- [ ] Auto-tuning factor weights

---

## References & Resources

### Source Files
- Main engine: `app/services/advanced_backtest.py`
- API layer: `app/api/routes/backtest.py`
- Data models: `app/models/simulation.py`
- Schemas: `app/schemas/{simulation,factor}.py`

### Related Documentation
- Quant simulation design document (in docs/)
- Database schema definition (create_tables.py)
- Verification script (check_backtest.py)

### External Resources
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/
- Polars: https://www.pola-rs.com/

---

## Support & Questions

For questions about:
- **Algorithm details** → See BACKTEST_ANALYSIS.md
- **Code locations** → See BACKTEST_QUICK_REFERENCE.md
- **System overview** → See BACKTEST_SUMMARY.txt
- **Specific methods** → Check inline comments in source code

---

## Document Versions

| Document | Version | Lines | Updated |
|----------|---------|-------|---------|
| BACKTEST_ANALYSIS.md | v1.0 | 770 | 2024-11-09 |
| BACKTEST_QUICK_REFERENCE.md | v1.0 | 320 | 2024-11-09 |
| BACKTEST_SUMMARY.txt | v1.0 | 345 | 2024-11-09 |
| README_BACKTEST.md | v1.0 | 400 | 2024-11-09 |

---

**Last Updated**: 2024-11-09  
**Status**: Production Ready  
**Maintainer**: PROJ-40 Team
