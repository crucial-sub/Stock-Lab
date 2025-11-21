"""
자동매매 모델
- 모의투자 계좌 전용
"""
from sqlalchemy import Column, String, Boolean, Integer, DECIMAL, TIMESTAMP, ForeignKey, Text, Date, Time
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class AutoTradingStrategy(Base):
    """자동매매 전략 설정"""
    __tablename__ = "auto_trading_strategies"

    strategy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    simulation_session_id = Column(String, ForeignKey("simulation_sessions.session_id", ondelete="CASCADE"), nullable=False)

    # 활성화 상태
    is_active = Column(Boolean, default=False)

    # 매매 설정
    initial_capital = Column(DECIMAL(20, 2), default=50000000)
    current_capital = Column(DECIMAL(20, 2), default=50000000)
    cash_balance = Column(DECIMAL(20, 2), default=50000000)
    allocated_capital = Column(DECIMAL(20, 2), nullable=False)  # 전략에 할당된 자본금

    per_stock_ratio = Column(DECIMAL(5, 2), default=5.0)
    max_positions = Column(Integer, default=20)

    # 리밸런싱 주기
    rebalance_frequency = Column(String(20), default="DAILY")

    # 매수 조건 (백테스트와 동일)
    buy_conditions = Column(JSONB, nullable=True)  # 매수 조건식 리스트
    buy_logic = Column(String(500), nullable=True)  # 논리 조건식 (e.g., "A and B")
    priority_factor = Column(String(50), nullable=True)  # 우선순위 팩터
    priority_order = Column(String(10), default="desc")  # asc/desc
    max_buy_value = Column(DECIMAL(20, 2), nullable=True)  # 종목당 최대 매수 금액
    max_daily_stock = Column(Integer, nullable=True)  # 일일 최대 매수 종목 수
    buy_price_basis = Column(String(20), default="전일 종가")  # 매수 가격 기준
    buy_price_offset = Column(DECIMAL(10, 4), default=0)  # 매수 가격 조정 (%)

    # 매도 조건 - 목표가/손절가
    target_gain = Column(DECIMAL(10, 4), nullable=True)  # 목표가 (%)
    stop_loss = Column(DECIMAL(10, 4), nullable=True)  # 손절가 (%)

    # 매도 조건 - 보유 기간
    min_hold_days = Column(Integer, nullable=True)  # 최소 보유일
    max_hold_days = Column(Integer, nullable=True)  # 최대 보유일
    hold_days_sell_price_basis = Column(String(20), nullable=True)  # 보유기간 매도 가격 기준
    hold_days_sell_price_offset = Column(DECIMAL(10, 4), nullable=True)  # 보유기간 매도 가격 조정

    # 매도 조건 - 조건 매도
    sell_conditions = Column(JSONB, nullable=True)  # 매도 조건식 리스트
    sell_logic = Column(String(500), nullable=True)  # 매도 논리식
    condition_sell_price_basis = Column(String(20), nullable=True)  # 조건 매도 가격 기준
    condition_sell_price_offset = Column(DECIMAL(10, 4), nullable=True)  # 조건 매도 가격 조정

    # 수수료/슬리피지
    commission_rate = Column(DECIMAL(10, 6), default=0.00015)  # 수수료율
    slippage = Column(DECIMAL(10, 6), default=0.001)  # 슬리피지

    # 매매 대상
    trade_targets = Column(JSONB, nullable=True)  # 테마, 유니버스, 개별 종목

    # 타임스탬프
    created_at = Column(TIMESTAMP, default=datetime.now)
    activated_at = Column(TIMESTAMP, nullable=True)
    deactivated_at = Column(TIMESTAMP, nullable=True)
    last_executed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    user = relationship("User", back_populates="auto_trading_strategies")
    simulation_session = relationship("SimulationSession")
    positions = relationship("LivePosition", back_populates="strategy", cascade="all, delete-orphan")
    trades = relationship("LiveTrade", back_populates="strategy", cascade="all, delete-orphan")
    daily_performances = relationship("LiveDailyPerformance", back_populates="strategy", cascade="all, delete-orphan")
    logs = relationship("AutoTradingLog", back_populates="strategy", cascade="all, delete-orphan")


class LivePosition(Base):
    """실시간 보유 종목"""
    __tablename__ = "live_positions"

    position_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("auto_trading_strategies.strategy_id", ondelete="CASCADE"), nullable=False)

    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100))

    quantity = Column(Integer, nullable=False)
    avg_buy_price = Column(DECIMAL(20, 2), nullable=False)
    current_price = Column(DECIMAL(20, 2))

    buy_date = Column(Date, nullable=False)
    hold_days = Column(Integer, default=0)

    # 평가 손익
    unrealized_profit = Column(DECIMAL(20, 2))
    unrealized_profit_pct = Column(DECIMAL(10, 4))

    # 메타 정보
    buy_factors = Column(JSONB)
    selection_reason = Column(Text)

    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)

    # Relationships
    strategy = relationship("AutoTradingStrategy", back_populates="positions")


class LiveTrade(Base):
    """실시간 매매 내역"""
    __tablename__ = "live_trades"

    trade_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("auto_trading_strategies.strategy_id", ondelete="CASCADE"), nullable=False)

    trade_date = Column(Date, nullable=False)
    trade_time = Column(Time, default=datetime.now().time)
    trade_type = Column(String(10), nullable=False)  # BUY, SELL

    stock_code = Column(String(20), nullable=False)
    stock_name = Column(String(100))

    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(20, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)

    # 비용
    commission = Column(DECIMAL(20, 2), default=0)
    tax = Column(DECIMAL(20, 2), default=0)

    # 매도 시에만
    profit = Column(DECIMAL(20, 2))
    profit_rate = Column(DECIMAL(10, 4))
    hold_days = Column(Integer)

    # 매매 근거
    selection_reason = Column(Text)
    factors = Column(JSONB)

    # 키움 API 주문 정보
    order_number = Column(String(50))
    order_status = Column(String(20), default="PENDING")  # PENDING, FILLED, CANCELLED, FAILED

    created_at = Column(TIMESTAMP, default=datetime.now)

    # Relationships
    strategy = relationship("AutoTradingStrategy", back_populates="trades")


class LiveDailyPerformance(Base):
    """자동매매 일일 성과"""
    __tablename__ = "live_daily_performance"

    performance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("auto_trading_strategies.strategy_id", ondelete="CASCADE"), nullable=False)

    date = Column(Date, nullable=False)

    # 자산 현황
    cash_balance = Column(DECIMAL(20, 2), nullable=False)
    stock_value = Column(DECIMAL(20, 2), nullable=False)
    total_value = Column(DECIMAL(20, 2), nullable=False)

    # 수익률
    daily_return = Column(DECIMAL(10, 4))
    cumulative_return = Column(DECIMAL(10, 4))

    # 거래 통계
    buy_count = Column(Integer, default=0)
    sell_count = Column(Integer, default=0)
    trade_count = Column(Integer, default=0)

    # 보유 종목 수
    position_count = Column(Integer, default=0)

    created_at = Column(TIMESTAMP, default=datetime.now)

    # Relationships
    strategy = relationship("AutoTradingStrategy", back_populates="daily_performances")


class AutoTradingLog(Base):
    """자동매매 이벤트 로그"""
    __tablename__ = "auto_trading_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("auto_trading_strategies.strategy_id", ondelete="CASCADE"))

    event_type = Column(String(50), nullable=False)
    event_level = Column(String(20), default="INFO")

    message = Column(Text)
    details = Column(JSONB)

    created_at = Column(TIMESTAMP, default=datetime.now)

    # Relationships
    strategy = relationship("AutoTradingStrategy", back_populates="logs")
