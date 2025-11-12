"""
백테스트 결과 저장 모델
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, TIMESTAMP, ForeignKey, Index, UniqueConstraint, BigInteger, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from uuid import uuid4


class BacktestSession(Base):
    """
    백테스트 세션 메타 정보
    """
    __tablename__ = "backtest_sessions"

    # Primary Key
    backtest_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="백테스트 고유 ID")

    # 백테스트 기본 정보
    backtest_name = Column(String(200), nullable=False, comment="백테스트 이름")
    status = Column(String(20), nullable=False, comment="상태 (RUNNING/COMPLETED/FAILED)")

    # 백테스트 설정
    start_date = Column(Date, nullable=False, comment="백테스트 시작일")
    end_date = Column(Date, nullable=False, comment="백테스트 종료일")
    initial_capital = Column(Numeric(20, 2), nullable=False, comment="초기 자본금")

    rebalance_frequency = Column(String(20), nullable=False, comment="리밸런싱 주기")
    max_positions = Column(Integer, nullable=False, comment="최대 보유 종목 수")
    position_sizing = Column(String(20), nullable=False, comment="포지션 사이징 방법")
    benchmark = Column(String(20), nullable=False, comment="벤치마크")

    commission_rate = Column(Numeric(10, 6), nullable=False, comment="수수료율")
    tax_rate = Column(Numeric(10, 6), nullable=False, comment="거래세율")
    slippage = Column(Numeric(10, 6), nullable=False, comment="슬리피지")

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="생성일시")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="완료일시")

    # Relationships
    conditions = relationship("BacktestCondition", back_populates="session", cascade="all, delete-orphan")
    statistics = relationship("BacktestStatistics", back_populates="session", cascade="all, delete-orphan", uselist=False)
    daily_snapshots = relationship("BacktestDailySnapshot", back_populates="session", cascade="all, delete-orphan")
    trades = relationship("BacktestTrade", back_populates="session", cascade="all, delete-orphan")
    holdings = relationship("BacktestHolding", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_sessions_created_at', 'created_at'),
        Index('idx_backtest_sessions_status', 'status'),
        {"comment": "백테스트 세션 정보"}
    )

    def __repr__(self):
        return f"<BacktestSession(id={self.backtest_id}, name={self.backtest_name}, status={self.status})>"


class BacktestCondition(Base):
    """
    백테스트 조건 (매수/매도)
    """
    __tablename__ = "backtest_conditions"

    # Primary Key
    condition_id = Column(Integer, primary_key=True, autoincrement=True, comment="조건 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 조건 정보
    condition_type = Column(String(10), nullable=False, comment="조건 유형 (BUY/SELL)")
    factor = Column(String(50), nullable=False, comment="팩터 코드")
    operator = Column(String(10), nullable=False, comment="연산자 (>, <, >=, <=)")
    value = Column(Numeric(20, 4), nullable=False, comment="기준값")
    description = Column(String(500), nullable=True, comment="조건 설명")

    # Relationship
    session = relationship("BacktestSession", back_populates="conditions")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_conditions_backtest', 'backtest_id'),
        {"comment": "백테스트 매수/매도 조건"}
    )

    def __repr__(self):
        return f"<BacktestCondition(backtest_id={self.backtest_id}, type={self.condition_type}, factor={self.factor})>"


class BacktestStatistics(Base):
    """
    백테스트 통계 (요약)
    """
    __tablename__ = "backtest_statistics"

    # Primary Key & Foreign Key (1:1)
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions.backtest_id", ondelete="CASCADE"),
        primary_key=True,
        comment="백테스트 참조 ID"
    )

    # 수익률 지표
    total_return = Column(Numeric(10, 4), nullable=False, comment="총 수익률 (%)")
    annualized_return = Column(Numeric(10, 4), nullable=False, comment="연환산 수익률 (CAGR) (%)")
    benchmark_return = Column(Numeric(10, 4), nullable=True, comment="벤치마크 수익률 (%)")
    excess_return = Column(Numeric(10, 4), nullable=True, comment="초과 수익률 (%)")

    # 리스크 지표
    max_drawdown = Column(Numeric(10, 4), nullable=False, comment="최대 낙폭 (MDD) (%)")
    volatility = Column(Numeric(10, 4), nullable=False, comment="변동성 (%)")
    downside_volatility = Column(Numeric(10, 4), nullable=False, comment="하방 변동성 (%)")

    # 리스크 조정 수익률
    sharpe_ratio = Column(Numeric(10, 4), nullable=False, comment="샤프 비율")
    sortino_ratio = Column(Numeric(10, 4), nullable=False, comment="소르티노 비율")
    calmar_ratio = Column(Numeric(10, 4), nullable=False, comment="칼마 비율")

    # 거래 통계
    total_trades = Column(Integer, nullable=False, comment="총 거래 횟수")
    winning_trades = Column(Integer, nullable=False, comment="수익 거래 횟수")
    losing_trades = Column(Integer, nullable=False, comment="손실 거래 횟수")
    win_rate = Column(Numeric(10, 4), nullable=False, comment="승률 (%)")
    avg_win = Column(Numeric(10, 4), nullable=False, comment="평균 수익 (%)")
    avg_loss = Column(Numeric(10, 4), nullable=False, comment="평균 손실 (%)")
    profit_loss_ratio = Column(Numeric(10, 4), nullable=False, comment="손익비")

    # 자산 정보
    initial_capital = Column(Numeric(20, 2), nullable=False, comment="초기 자본금")
    final_capital = Column(Numeric(20, 2), nullable=False, comment="최종 자본금")
    peak_capital = Column(Numeric(20, 2), nullable=False, comment="최대 자본금")

    # 기간 정보
    start_date = Column(Date, nullable=False, comment="시작일")
    end_date = Column(Date, nullable=False, comment="종료일")
    trading_days = Column(Integer, nullable=False, comment="거래일수")

    # Relationship
    session = relationship("BacktestSession", back_populates="statistics")

    __table_args__ = (
        {"comment": "백테스트 통계 요약"}
    )

    def __repr__(self):
        return f"<BacktestStatistics(backtest_id={self.backtest_id}, return={self.total_return}%)>"


class BacktestDailySnapshot(Base):
    """
    백테스트 일별 스냅샷
    """
    __tablename__ = "backtest_daily_snapshots"

    # Primary Key
    snapshot_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="스냅샷 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 날짜
    snapshot_date = Column(Date, nullable=False, comment="스냅샷 날짜")

    # 포트폴리오 가치
    portfolio_value = Column(Numeric(20, 2), nullable=False, comment="포트폴리오 가치")
    cash_balance = Column(Numeric(20, 2), nullable=False, comment="현금 잔고")
    invested_amount = Column(Numeric(20, 2), nullable=False, comment="투자 금액")

    # 수익률
    daily_return = Column(Numeric(10, 4), nullable=False, comment="일 수익률 (%)")
    cumulative_return = Column(Numeric(10, 4), nullable=False, comment="누적 수익률 (%)")
    drawdown = Column(Numeric(10, 4), nullable=False, comment="낙폭 (%)")

    # 벤치마크
    benchmark_return = Column(Numeric(10, 4), nullable=True, comment="벤치마크 수익률 (%)")

    # 거래
    trade_count = Column(Integer, default=0, comment="당일 거래 횟수")

    # Relationship
    session = relationship("BacktestSession", back_populates="daily_snapshots")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_daily_snapshots_backtest_date', 'backtest_id', 'snapshot_date'),
        UniqueConstraint('backtest_id', 'snapshot_date', name='uq_backtest_daily_snapshots'),
        {"comment": "백테스트 일별 성과 스냅샷"}
    )

    def __repr__(self):
        return f"<BacktestDailySnapshot(backtest_id={self.backtest_id}, date={self.snapshot_date})>"


class BacktestTrade(Base):
    """
    백테스트 거래 내역
    """
    __tablename__ = "backtest_trades"

    # Primary Key
    trade_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="거래 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 거래 기본 정보
    trade_date = Column(Date, nullable=False, comment="거래일")
    trade_type = Column(String(10), nullable=False, comment="거래 유형 (BUY/SELL)")
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")

    # 거래 상세
    quantity = Column(Integer, nullable=False, comment="수량")
    price = Column(Numeric(20, 2), nullable=False, comment="거래가")
    amount = Column(Numeric(20, 2), nullable=False, comment="거래대금")
    commission = Column(Numeric(20, 2), nullable=False, comment="수수료")
    tax = Column(Numeric(20, 2), default=0, comment="세금")

    # 매도 시에만
    profit = Column(Numeric(20, 2), nullable=True, comment="실현 손익")
    profit_rate = Column(Numeric(10, 4), nullable=True, comment="수익률 (%)")
    hold_days = Column(Integer, nullable=True, comment="보유일수")

    # 거래 시점 팩터 정보
    factors = Column(JSONB, nullable=True, comment="거래 시점 팩터 값")
    selection_reason = Column(Text, nullable=True, comment="매매 사유")

    # Relationship
    session = relationship("BacktestSession", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_trades_backtest_date', 'backtest_id', 'trade_date'),
        Index('idx_backtest_trades_stock', 'stock_code'),
        {"comment": "백테스트 거래 내역"}
    )

    def __repr__(self):
        return f"<BacktestTrade(backtest_id={self.backtest_id}, date={self.trade_date}, type={self.trade_type}, stock={self.stock_code})>"


class BacktestHolding(Base):
    """
    백테스트 보유 종목 (최종 상태)
    """
    __tablename__ = "backtest_holdings"

    # Primary Key
    holding_id = Column(Integer, primary_key=True, autoincrement=True, comment="보유 종목 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 종목 정보
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")

    # 보유 정보
    quantity = Column(Integer, nullable=False, comment="보유 수량")
    avg_price = Column(Numeric(20, 2), nullable=False, comment="평균 매수가")
    current_price = Column(Numeric(20, 2), nullable=False, comment="현재가")
    value = Column(Numeric(20, 2), nullable=False, comment="평가금액")

    # 손익
    profit = Column(Numeric(20, 2), nullable=False, comment="손익")
    profit_rate = Column(Numeric(10, 4), nullable=False, comment="수익률 (%)")

    # 비중
    weight = Column(Numeric(10, 4), nullable=False, comment="포트폴리오 비중 (%)")

    # 보유 기간
    buy_date = Column(Date, nullable=False, comment="최초 매수일")
    hold_days = Column(Integer, nullable=False, comment="보유일수")

    # 팩터 정보
    factors = Column(JSONB, nullable=True, comment="현재 팩터 값")

    # Relationship
    session = relationship("BacktestSession", back_populates="holdings")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_holdings_backtest', 'backtest_id'),
        UniqueConstraint('backtest_id', 'stock_code', name='uq_backtest_holdings'),
        {"comment": "백테스트 보유 종목 (최종 상태)"}
    )

    def __repr__(self):
        return f"<BacktestHolding(backtest_id={self.backtest_id}, stock={self.stock_code}, qty={self.quantity})>"
