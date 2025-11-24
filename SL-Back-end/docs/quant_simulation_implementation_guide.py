# 퀀트 투자 시뮬레이션 시스템 구현 가이드

## 1. 데이터베이스 연결 및 모델 정의

```python
# models/database.py
from sqlalchemy import create_engine, Column, String, Integer, Decimal, Date, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid

Base = declarative_base()

# 데이터베이스 연결
engine = create_engine('mysql+pymysql://user:password@localhost/quant_db')
Session = sessionmaker(bind=engine)

# 팩터 모델
class Factor(Base):
    __tablename__ = 'factors'
    
    factor_id = Column(String(30), primary_key=True)
    category_id = Column(String(20), ForeignKey('factor_categories.category_id'))
    factor_name = Column(String(100), nullable=False)
    calculation_type = Column(String(20))
    formula = Column(String(500))
    update_frequency = Column(String(20))
    
    # Relationships
    category = relationship("FactorCategory", back_populates="factors")
    strategy_factors = relationship("StrategyFactor", back_populates="factor")

# 전략 모델
class PortfolioStrategy(Base):
    __tablename__ = 'portfolio_strategies'
    
    strategy_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_name = Column(String(100), nullable=False)
    strategy_type = Column(String(30))
    backtest_start_date = Column(Date)
    backtest_end_date = Column(Date)
    initial_capital = Column(Decimal(15, 0))
    universe_type = Column(String(30))
    
    # Relationships
    factors = relationship("StrategyFactor", back_populates="strategy")
    trading_rules = relationship("TradingRule", back_populates="strategy")
    sessions = relationship("SimulationSession", back_populates="strategy")

# 시뮬레이션 세션 모델
class SimulationSession(Base):
    __tablename__ = 'simulation_sessions'
    
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(String(36), ForeignKey('portfolio_strategies.strategy_id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default='PENDING')
    progress = Column(Integer, default=0)
    
    # Relationships
    strategy = relationship("PortfolioStrategy", back_populates="sessions")
    statistics = relationship("SimulationStatistics", uselist=False, back_populates="session")
    trades = relationship("SimulationTrade", back_populates="session")
```

## 2. 팩터 계산 엔진

```python
# engines/factor_calculator.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class FactorCalculator:
    """팩터 계산 엔진"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.factor_cache = {}
        
    def calculate_factor(self, factor_id: str, date: datetime, stock_codes: List[str]) -> pd.DataFrame:
        """특정 팩터 계산"""
        factor = self.db_session.query(Factor).filter_by(factor_id=factor_id).first()
        
        if factor.calculation_type == 'FUNDAMENTAL':
            return self._calculate_fundamental_factor(factor, date, stock_codes)
        elif factor.calculation_type == 'TECHNICAL':
            return self._calculate_technical_factor(factor, date, stock_codes)
        elif factor.calculation_type == 'ALTERNATIVE':
            return self._calculate_alternative_factor(factor, date, stock_codes)
            
    def _calculate_fundamental_factor(self, factor, date, stock_codes):
        """재무 팩터 계산"""
        # 예시: PER 계산
        if factor.factor_id == 'PER':
            query = f"""
            SELECT 
                s.stock_code,
                s.close_price / f.eps as per
            FROM daily_prices s
            JOIN financial_items f ON s.stock_code = f.stock_code
            WHERE s.trade_date = %s 
                AND s.stock_code IN %s
                AND f.fiscal_period <= %s
            """
            df = pd.read_sql(query, self.db_session.bind, params=[date, stock_codes, date])
            return df
            
    def _calculate_technical_factor(self, factor, date, stock_codes):
        """기술적 팩터 계산"""
        # 예시: 1개월 모멘텀
        if factor.factor_id == 'MOM_1M':
            end_date = date
            start_date = date - timedelta(days=30)
            
            query = f"""
            SELECT 
                stock_code,
                (MAX(CASE WHEN trade_date = %s THEN close_price END) / 
                 MAX(CASE WHEN trade_date = %s THEN close_price END) - 1) * 100 as momentum_1m
            FROM daily_prices
            WHERE stock_code IN %s
                AND trade_date IN (%s, %s)
            GROUP BY stock_code
            """
            df = pd.read_sql(query, self.db_session.bind, 
                           params=[end_date, start_date, stock_codes, end_date, start_date])
            return df
    
    def calculate_composite_score(self, factors: Dict[str, float], date: datetime, 
                                stock_codes: List[str]) -> pd.DataFrame:
        """복합 팩터 스코어 계산"""
        scores = pd.DataFrame({'stock_code': stock_codes})
        
        for factor_id, weight in factors.items():
            factor_values = self.calculate_factor(factor_id, date, stock_codes)
            
            # Z-score 정규화
            factor_values['z_score'] = (factor_values.iloc[:, 1] - factor_values.iloc[:, 1].mean()) / factor_values.iloc[:, 1].std()
            
            # 가중치 적용
            factor_values['weighted_score'] = factor_values['z_score'] * weight
            
            scores = scores.merge(factor_values[['stock_code', 'weighted_score']], 
                                on='stock_code', how='left', suffixes=('', f'_{factor_id}'))
        
        # 종합 스코어 계산
        score_columns = [col for col in scores.columns if 'weighted_score' in col]
        scores['composite_score'] = scores[score_columns].sum(axis=1)
        
        return scores[['stock_code', 'composite_score']].sort_values('composite_score', ascending=False)
```

## 3. 백테스팅 엔진

```python
# engines/backtest_engine.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class BacktestConfig:
    """백테스트 설정"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100_000_000
    commission_rate: float = 0.00015
    tax_rate: float = 0.0023
    slippage: float = 0.0001
    rebalance_frequency: str = 'MONTHLY'
    max_positions: int = 20
    position_sizing: str = 'EQUAL_WEIGHT'

class BacktestEngine:
    """백테스팅 엔진"""
    
    def __init__(self, config: BacktestConfig, db_session):
        self.config = config
        self.db_session = db_session
        self.factor_calculator = FactorCalculator(db_session)
        self.portfolio = Portfolio(config.initial_capital)
        self.trades = []
        self.daily_values = []
        
    def run(self) -> Dict:
        """백테스트 실행"""
        # 세션 생성
        session = self._create_session()
        
        # 거래일 가져오기
        trading_days = self._get_trading_days()
        
        for i, date in enumerate(trading_days):
            # 진행률 업데이트
            progress = int((i / len(trading_days)) * 100)
            self._update_progress(session.session_id, progress)
            
            # 시장 데이터 로드
            market_data = self._load_market_data(date)
            
            # 리밸런싱 체크
            if self._should_rebalance(date):
                signals = self._generate_signals(date, market_data)
                self._rebalance_portfolio(date, signals, market_data)
            
            # 포트폴리오 평가
            self._evaluate_portfolio(date, market_data)
            
            # 일별 스냅샷 저장
            self._save_daily_snapshot(date)
        
        # 성과 계산
        performance = self._calculate_performance()
        
        # 결과 저장
        self._save_results(session.session_id, performance)
        
        return performance
    
    def _generate_signals(self, date: datetime, market_data: pd.DataFrame) -> pd.DataFrame:
        """시그널 생성"""
        # 전략 팩터 로드
        strategy_factors = self.db_session.query(StrategyFactor)\
            .filter_by(strategy_id=self.config.strategy_id).all()
        
        # 유니버스 필터링
        universe = self._filter_universe(date, market_data)
        
        # 팩터 스코어 계산
        factor_weights = {sf.factor_id: sf.weight for sf in strategy_factors}
        scores = self.factor_calculator.calculate_composite_score(
            factor_weights, date, universe['stock_code'].tolist()
        )
        
        # 상위 N개 종목 선택
        top_stocks = scores.head(self.config.max_positions)
        
        return top_stocks
    
    def _rebalance_portfolio(self, date: datetime, signals: pd.DataFrame, market_data: pd.DataFrame):
        """포트폴리오 리밸런싱"""
        current_positions = self.portfolio.get_positions()
        target_stocks = signals['stock_code'].tolist()
        
        # 매도: 시그널에 없는 종목
        for stock in current_positions:
            if stock not in target_stocks:
                self._execute_sell(date, stock, market_data)
        
        # 매수: 새로운 종목
        if self.config.position_sizing == 'EQUAL_WEIGHT':
            position_size = self.portfolio.total_value / len(target_stocks)
        
        for stock in target_stocks:
            if stock not in current_positions:
                price = self._get_stock_price(stock, date, market_data)
                quantity = int(position_size / price)
                if quantity > 0:
                    self._execute_buy(date, stock, quantity, price)
    
    def _execute_buy(self, date: datetime, stock_code: str, quantity: int, price: float):
        """매수 실행"""
        # 거래 비용 계산
        amount = quantity * price
        commission = amount * self.config.commission_rate
        slippage_cost = amount * self.config.slippage
        total_cost = amount + commission + slippage_cost
        
        # 포트폴리오 업데이트
        if self.portfolio.cash >= total_cost:
            self.portfolio.add_position(stock_code, quantity, price)
            
            # 거래 기록
            trade = {
                'trade_date': date,
                'stock_code': stock_code,
                'trade_type': 'BUY',
                'quantity': quantity,
                'price': price,
                'commission': commission,
                'slippage_cost': slippage_cost
            }
            self.trades.append(trade)
    
    def _execute_sell(self, date: datetime, stock_code: str, market_data: pd.DataFrame):
        """매도 실행"""
        position = self.portfolio.positions.get(stock_code)
        if not position:
            return
        
        price = self._get_stock_price(stock_code, date, market_data)
        quantity = position['quantity']
        amount = quantity * price
        
        # 거래 비용 계산
        commission = amount * self.config.commission_rate
        tax = amount * self.config.tax_rate
        slippage_cost = amount * self.config.slippage
        
        # 실현 손익 계산
        realized_pnl = (price - position['avg_price']) * quantity - commission - tax - slippage_cost
        realized_pnl_pct = (price / position['avg_price'] - 1) * 100
        
        # 포트폴리오 업데이트
        self.portfolio.remove_position(stock_code, quantity, price)
        
        # 거래 기록
        trade = {
            'trade_date': date,
            'stock_code': stock_code,
            'trade_type': 'SELL',
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'tax': tax,
            'slippage_cost': slippage_cost,
            'realized_pnl': realized_pnl,
            'realized_pnl_pct': realized_pnl_pct
        }
        self.trades.append(trade)
    
    def _calculate_performance(self) -> Dict:
        """성과 지표 계산"""
        daily_returns = pd.DataFrame(self.daily_values)['daily_return']
        
        # 기본 수익률 지표
        total_return = (self.portfolio.total_value / self.config.initial_capital - 1) * 100
        trading_days = len(daily_returns)
        years = trading_days / 252
        annualized_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # 리스크 지표
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annualized_return - 2) / volatility if volatility > 0 else 0  # Risk-free rate = 2%
        
        # 낙폭 분석
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 거래 통계
        trades_df = pd.DataFrame(self.trades)
        if len(trades_df) > 0:
            sell_trades = trades_df[trades_df['trade_type'] == 'SELL']
            winning_trades = sell_trades[sell_trades['realized_pnl'] > 0]
            losing_trades = sell_trades[sell_trades['realized_pnl'] < 0]
            
            win_rate = len(winning_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
            avg_win = winning_trades['realized_pnl_pct'].mean() if len(winning_trades) > 0 else 0
            avg_loss = abs(losing_trades['realized_pnl_pct'].mean()) if len(losing_trades) > 0 else 0
            profit_factor = winning_trades['realized_pnl'].sum() / abs(losing_trades['realized_pnl'].sum()) \
                          if len(losing_trades) > 0 and losing_trades['realized_pnl'].sum() != 0 else float('inf')
        else:
            win_rate = avg_win = avg_loss = profit_factor = 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }

class Portfolio:
    """포트폴리오 관리 클래스"""
    
    def __init__(self, initial_capital: float):
        self.cash = initial_capital
        self.positions = {}
        self.total_value = initial_capital
        
    def add_position(self, stock_code: str, quantity: int, price: float):
        """포지션 추가"""
        if stock_code in self.positions:
            old_qty = self.positions[stock_code]['quantity']
            old_price = self.positions[stock_code]['avg_price']
            new_qty = old_qty + quantity
            new_price = (old_qty * old_price + quantity * price) / new_qty
            
            self.positions[stock_code] = {
                'quantity': new_qty,
                'avg_price': new_price
            }
        else:
            self.positions[stock_code] = {
                'quantity': quantity,
                'avg_price': price
            }
        
        self.cash -= quantity * price
    
    def remove_position(self, stock_code: str, quantity: int, price: float):
        """포지션 제거"""
        if stock_code in self.positions:
            self.positions[stock_code]['quantity'] -= quantity
            if self.positions[stock_code]['quantity'] <= 0:
                del self.positions[stock_code]
            self.cash += quantity * price
    
    def get_positions(self) -> List[str]:
        """현재 보유 종목 리스트"""
        return list(self.positions.keys())
    
    def evaluate(self, market_prices: Dict[str, float]) -> float:
        """포트폴리오 평가"""
        positions_value = sum(
            pos['quantity'] * market_prices.get(stock, pos['avg_price'])
            for stock, pos in self.positions.items()
        )
        self.total_value = self.cash + positions_value
        return self.total_value
```

## 4. API 인터페이스

```python
# api/routes.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

app = FastAPI(title="Quant Simulation API", version="1.0.0")

# 의존성 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 전략 관리 API
@app.post("/strategies/")
async def create_strategy(strategy_data: Dict, db: Session = Depends(get_db)):
    """전략 생성"""
    strategy = PortfolioStrategy(**strategy_data)
    db.add(strategy)
    db.commit()
    return {"strategy_id": strategy.strategy_id, "message": "Strategy created successfully"}

@app.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """전략 조회"""
    strategy = db.query(PortfolioStrategy).filter_by(strategy_id=strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@app.put("/strategies/{strategy_id}/factors")
async def update_strategy_factors(strategy_id: str, factors: List[Dict], db: Session = Depends(get_db)):
    """전략 팩터 업데이트"""
    # 기존 팩터 삭제
    db.query(StrategyFactor).filter_by(strategy_id=strategy_id).delete()
    
    # 새 팩터 추가
    for factor_data in factors:
        factor = StrategyFactor(strategy_id=strategy_id, **factor_data)
        db.add(factor)
    
    db.commit()
    return {"message": "Factors updated successfully"}

# 백테스팅 API
@app.post("/backtest/start")
async def start_backtest(
    backtest_config: Dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """백테스트 시작"""
    # 세션 생성
    session = SimulationSession(
        strategy_id=backtest_config['strategy_id'],
        start_date=backtest_config['start_date'],
        end_date=backtest_config['end_date'],
        status='PENDING'
    )
    db.add(session)
    db.commit()
    
    # 백그라운드에서 백테스트 실행
    background_tasks.add_task(run_backtest_task, session.session_id, backtest_config)
    
    return {
        "session_id": session.session_id,
        "status": "STARTED",
        "message": "Backtest started in background"
    }

@app.get("/backtest/{session_id}/status")
async def get_backtest_status(session_id: str, db: Session = Depends(get_db)):
    """백테스트 상태 조회"""
    session = db.query(SimulationSession).filter_by(session_id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "status": session.status,
        "progress": session.progress,
        "started_at": session.started_at,
        "completed_at": session.completed_at
    }

@app.get("/backtest/{session_id}/results")
async def get_backtest_results(session_id: str, db: Session = Depends(get_db)):
    """백테스트 결과 조회"""
    # 통계 조회
    stats = db.query(SimulationStatistics).filter_by(session_id=session_id).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Results not found")
    
    # 일별 수익률 조회
    daily_values = db.query(SimulationDailyValues)\
        .filter_by(session_id=session_id)\
        .order_by(SimulationDailyValues.date).all()
    
    # 거래 내역 조회
    trades = db.query(SimulationTrade)\
        .filter_by(session_id=session_id)\
        .order_by(SimulationTrade.trade_date).all()
    
    return {
        "statistics": {
            "cagr": float(stats.annualized_return),
            "total_return": float(stats.total_return),
            "sharpe_ratio": float(stats.sharpe_ratio),
            "max_drawdown": float(stats.max_drawdown),
            "volatility": float(stats.volatility),
            "win_rate": float(stats.win_rate),
            "total_trades": stats.total_trades
        },
        "daily_performance": [
            {
                "date": dv.date.isoformat(),
                "portfolio_value": float(dv.portfolio_value),
                "daily_return": float(dv.daily_return),
                "cumulative_return": float(dv.cumulative_return)
            }
            for dv in daily_values
        ],
        "trades": [
            {
                "date": t.trade_date.isoformat(),
                "stock_code": t.stock_code,
                "type": t.trade_type,
                "quantity": t.quantity,
                "price": float(t.price),
                "pnl": float(t.realized_pnl) if t.realized_pnl else None
            }
            for t in trades
        ]
    }

# 분석 API
@app.get("/analysis/compare")
async def compare_strategies(
    strategy_ids: List[str],
    metric: str = "sharpe_ratio",
    db: Session = Depends(get_db)
):
    """전략 비교"""
    results = []
    
    for strategy_id in strategy_ids:
        stats = db.query(SimulationStatistics)\
            .join(SimulationSession)\
            .filter(SimulationSession.strategy_id == strategy_id)\
            .order_by(SimulationSession.created_at.desc())\
            .first()
        
        if stats:
            strategy = db.query(PortfolioStrategy).filter_by(strategy_id=strategy_id).first()
            results.append({
                "strategy_name": strategy.strategy_name,
                "strategy_id": strategy_id,
                metric: getattr(stats, metric)
            })
    
    # 메트릭 기준 정렬
    results.sort(key=lambda x: x[metric], reverse=True)
    
    return results

@app.get("/analysis/factor-performance")
async def analyze_factor_performance(
    factor_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """팩터 성과 분석"""
    # 팩터를 사용한 전략들의 성과 조회
    query = """
    SELECT 
        f.factor_id,
        AVG(ss.annualized_return) as avg_return,
        AVG(ss.sharpe_ratio) as avg_sharpe,
        COUNT(DISTINCT s.strategy_id) as strategy_count
    FROM strategy_factors sf
    JOIN portfolio_strategies s ON sf.strategy_id = s.strategy_id
    JOIN simulation_sessions ses ON s.strategy_id = ses.strategy_id
    JOIN simulation_statistics ss ON ses.session_id = ss.session_id
    WHERE sf.factor_id = :factor_id
        AND ses.start_date >= :start_date
        AND ses.end_date <= :end_date
        AND ses.status = 'COMPLETED'
    GROUP BY sf.factor_id
    """
    
    result = db.execute(query, {
        'factor_id': factor_id,
        'start_date': start_date,
        'end_date': end_date
    }).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="No data found for this factor")
    
    return {
        "factor_id": factor_id,
        "average_return": float(result.avg_return),
        "average_sharpe": float(result.avg_sharpe),
        "strategy_count": result.strategy_count
    }

# WebSocket for real-time updates
from fastapi import WebSocket
import json

@app.websocket("/ws/backtest/{session_id}")
async def websocket_backtest_progress(websocket: WebSocket, session_id: str):
    """백테스트 진행상황 실시간 전송"""
    await websocket.accept()
    
    db = SessionLocal()
    try:
        while True:
            # 세션 상태 조회
            session = db.query(SimulationSession).filter_by(session_id=session_id).first()
            
            if session:
                data = {
                    "session_id": session_id,
                    "status": session.status,
                    "progress": session.progress
                }
                
                await websocket.send_json(data)
                
                # 완료되면 종료
                if session.status in ['COMPLETED', 'FAILED']:
                    break
            
            await asyncio.sleep(1)  # 1초마다 업데이트
            
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        db.close()
        await websocket.close()

# 백그라운드 태스크
async def run_backtest_task(session_id: str, config: Dict):
    """백테스트 실행 태스크"""
    db = SessionLocal()
    
    try:
        # 세션 상태 업데이트
        session = db.query(SimulationSession).filter_by(session_id=session_id).first()
        session.status = 'RUNNING'
        session.started_at = datetime.now()
        db.commit()
        
        # 백테스트 실행
        backtest_config = BacktestConfig(**config)
        engine = BacktestEngine(backtest_config, db)
        results = engine.run()
        
        # 결과 저장
        statistics = SimulationStatistics(
            session_id=session_id,
            **results
        )
        db.add(statistics)
        
        # 세션 완료 처리
        session.status = 'COMPLETED'
        session.completed_at = datetime.now()
        session.progress = 100
        db.commit()
        
    except Exception as e:
        # 에러 처리
        session = db.query(SimulationSession).filter_by(session_id=session_id).first()
        session.status = 'FAILED'
        session.error_message = str(e)
        db.commit()
        
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 5. 프론트엔드 연동 예시

```javascript
// frontend/services/backtest.js

class BacktestService {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }
    
    // 백테스트 시작
    async startBacktest(config) {
        const response = await fetch(`${this.apiUrl}/backtest/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        return response.json();
    }
    
    // 실시간 진행상황 모니터링
    monitorProgress(sessionId, onProgress) {
        const ws = new WebSocket(`ws://localhost:8000/ws/backtest/${sessionId}`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onProgress(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        return ws;
    }
    
    // 결과 조회
    async getResults(sessionId) {
        const response = await fetch(`${this.apiUrl}/backtest/${sessionId}/results`);
        return response.json();
    }
    
    // 차트 데이터 포맷팅
    formatChartData(results) {
        return {
            labels: results.daily_performance.map(d => d.date),
            datasets: [{
                label: 'Portfolio Value',
                data: results.daily_performance.map(d => d.portfolio_value),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        };
    }
}

// 사용 예시
const backtestService = new BacktestService('http://localhost:8000');

// 백테스트 실행
async function runBacktest() {
    // 1. 백테스트 시작
    const config = {
        strategy_id: 'abc123',
        start_date: '2020-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000000
    };
    
    const {session_id} = await backtestService.startBacktest(config);
    
    // 2. 진행상황 모니터링
    const ws = backtestService.monitorProgress(session_id, (data) => {
        console.log(`Progress: ${data.progress}%`);
        updateProgressBar(data.progress);
        
        if (data.status === 'COMPLETED') {
            // 3. 결과 조회 및 표시
            loadResults(session_id);
        }
    });
}

async function loadResults(sessionId) {
    const results = await backtestService.getResults(sessionId);
    
    // 통계 표시
    document.getElementById('cagr').textContent = `${results.statistics.cagr.toFixed(2)}%`;
    document.getElementById('sharpe').textContent = results.statistics.sharpe_ratio.toFixed(2);
    document.getElementById('mdd').textContent = `${results.statistics.max_drawdown.toFixed(2)}%`;
    
    // 차트 그리기
    const chartData = backtestService.formatChartData(results);
    drawChart(chartData);
}
```
