"""
GenPort 백테스트 확장 모델 - 논리식, 주문/체결, 상세 통계 저장
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, TIMESTAMP, ForeignKey, Index, UniqueConstraint, BigInteger, Numeric, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from uuid import uuid4


# ===== 기존 모델 확장 =====

class BacktestSessionExtended(Base):
    """
    백테스트 세션 메타 정보 (확장)
    """
    __tablename__ = "backtest_sessions_extended"

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

    # 논리식 조건 저장 (NEW)
    buy_expression = Column(Text, nullable=True, comment="매수 논리식 (A and B) or C")
    buy_conditions_json = Column(JSONB, nullable=True, comment="매수 조건 상세 JSON")
    sell_conditions_json = Column(JSONB, nullable=True, comment="매도 조건 상세 JSON")
    factor_weights = Column(JSONB, nullable=True, comment="팩터 가중치")

    commission_rate = Column(Numeric(10, 6), nullable=False, comment="수수료율")
    tax_rate = Column(Numeric(10, 6), nullable=False, comment="거래세율")
    slippage = Column(Numeric(10, 6), nullable=False, comment="슬리피지")

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="생성일시")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="완료일시")

    # Relationships
    orders = relationship("BacktestOrder", back_populates="session", cascade="all, delete-orphan")
    executions = relationship("BacktestExecution", back_populates="session", cascade="all, delete-orphan")
    positions = relationship("BacktestPosition", back_populates="session", cascade="all, delete-orphan")
    position_history = relationship("BacktestPositionHistory", back_populates="session", cascade="all, delete-orphan")
    monthly_stats = relationship("BacktestMonthlyStats", back_populates="session", cascade="all, delete-orphan")
    yearly_stats = relationship("BacktestYearlyStats", back_populates="session", cascade="all, delete-orphan")
    drawdown_periods = relationship("BacktestDrawdownPeriod", back_populates="session", cascade="all, delete-orphan")
    factor_contributions = relationship("BacktestFactorContribution", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_backtest_sessions_ext_created_at', 'created_at'),
        Index('idx_backtest_sessions_ext_status', 'status'),
        {"comment": "백테스트 세션 정보 (확장)"}
    )


# ===== 새로운 테이블 추가 =====

class BacktestOrder(Base):
    """
    백테스트 주문 내역
    """
    __tablename__ = "backtest_orders"

    # Primary Key
    order_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="주문 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 주문 정보
    order_date = Column(DateTime, nullable=False, comment="주문 일시")
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")
    order_side = Column(String(10), nullable=False, comment="매매구분 (BUY/SELL)")
    order_type = Column(String(20), default="MARKET", comment="주문 유형 (MARKET/LIMIT)")

    # 수량 및 가격
    quantity = Column(Integer, nullable=False, comment="주문 수량")
    order_price = Column(Numeric(20, 2), nullable=True, comment="주문가격 (지정가일 경우)")

    # 상태
    status = Column(String(20), nullable=False, comment="주문 상태 (PENDING/FILLED/CANCELLED)")
    filled_quantity = Column(Integer, default=0, comment="체결된 수량")

    # 메타 정보
    reason = Column(Text, nullable=True, comment="주문 사유")
    factor_scores = Column(JSONB, nullable=True, comment="주문 시점 팩터 값")
    condition_results = Column(JSONB, nullable=True, comment="조건 평가 결과")

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="orders")
    executions = relationship("BacktestExecution", back_populates="order")

    __table_args__ = (
        Index('idx_backtest_orders_backtest_date', 'backtest_id', 'order_date'),
        Index('idx_backtest_orders_stock', 'stock_code'),
        {"comment": "백테스트 주문 내역"}
    )


class BacktestExecution(Base):
    """
    백테스트 체결 내역
    """
    __tablename__ = "backtest_executions"

    # Primary Key
    execution_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="체결 고유 ID")

    # Foreign Keys
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="주문 참조 ID"
    )

    # 체결 정보
    execution_date = Column(DateTime, nullable=False, comment="체결 일시")
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")
    execution_side = Column(String(10), nullable=False, comment="매매구분 (BUY/SELL)")

    # 수량 및 가격
    quantity = Column(Integer, nullable=False, comment="체결 수량")
    price = Column(Numeric(20, 2), nullable=False, comment="체결 가격")
    amount = Column(Numeric(20, 2), nullable=False, comment="체결 금액")

    # 비용
    commission = Column(Numeric(20, 2), nullable=False, comment="수수료")
    tax = Column(Numeric(20, 2), default=0, comment="거래세")
    slippage_cost = Column(Numeric(20, 2), default=0, comment="슬리피지 비용")
    total_cost = Column(Numeric(20, 2), nullable=False, comment="총 비용")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="executions")
    order = relationship("BacktestOrder", back_populates="executions")

    __table_args__ = (
        Index('idx_backtest_executions_backtest_date', 'backtest_id', 'execution_date'),
        Index('idx_backtest_executions_order', 'order_id'),
        {"comment": "백테스트 체결 내역"}
    )


class BacktestPosition(Base):
    """
    백테스트 포지션 (현재 보유)
    """
    __tablename__ = "backtest_positions"

    # Primary Key
    position_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="포지션 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 포지션 정보
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")

    # 수량 및 가격
    quantity = Column(Integer, nullable=False, comment="보유 수량")
    avg_price = Column(Numeric(20, 2), nullable=False, comment="평균 단가")
    current_price = Column(Numeric(20, 2), nullable=False, comment="현재가")
    market_value = Column(Numeric(20, 2), nullable=False, comment="평가금액")

    # 손익
    unrealized_pnl = Column(Numeric(20, 2), nullable=False, comment="미실현 손익")
    unrealized_pnl_pct = Column(Numeric(10, 4), nullable=False, comment="미실현 수익률 (%)")
    realized_pnl = Column(Numeric(20, 2), default=0, comment="실현 손익")

    # 포지션 정보
    entry_date = Column(Date, nullable=False, comment="최초 진입일")
    last_update = Column(Date, nullable=False, comment="최종 업데이트일")
    hold_days = Column(Integer, nullable=False, comment="보유일수")

    # 상태
    is_active = Column(Boolean, default=True, comment="활성 포지션 여부")
    exit_date = Column(Date, nullable=True, comment="청산일")
    exit_reason = Column(String(100), nullable=True, comment="청산 사유")

    # 팩터 정보
    entry_factors = Column(JSONB, nullable=True, comment="진입 시점 팩터")
    current_factors = Column(JSONB, nullable=True, comment="현재 팩터")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="positions")

    __table_args__ = (
        Index('idx_backtest_positions_backtest_active', 'backtest_id', 'is_active'),
        UniqueConstraint('backtest_id', 'stock_code', 'is_active', name='uq_active_position'),
        {"comment": "백테스트 포지션"}
    )


class BacktestPositionHistory(Base):
    """
    백테스트 포지션 히스토리 (일별 스냅샷)
    """
    __tablename__ = "backtest_position_history"

    # Primary Key
    history_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="히스토리 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 스냅샷 정보
    snapshot_date = Column(Date, nullable=False, comment="스냅샷 날짜")
    stock_code = Column(String(6), nullable=False, comment="종목 코드")
    stock_name = Column(String(200), nullable=False, comment="종목명")

    # 포지션 정보
    quantity = Column(Integer, nullable=False, comment="보유 수량")
    avg_price = Column(Numeric(20, 2), nullable=False, comment="평균 단가")
    close_price = Column(Numeric(20, 2), nullable=False, comment="종가")
    market_value = Column(Numeric(20, 2), nullable=False, comment="평가금액")

    # 손익
    daily_pnl = Column(Numeric(20, 2), nullable=False, comment="일일 손익")
    cumulative_pnl = Column(Numeric(20, 2), nullable=False, comment="누적 손익")
    pnl_pct = Column(Numeric(10, 4), nullable=False, comment="수익률 (%)")

    # 추가 정보
    weight = Column(Numeric(10, 4), nullable=False, comment="포트폴리오 비중 (%)")
    max_profit = Column(Numeric(20, 2), nullable=True, comment="최대 이익")
    max_loss = Column(Numeric(20, 2), nullable=True, comment="최대 손실")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="position_history")

    __table_args__ = (
        Index('idx_position_history_backtest_date', 'backtest_id', 'snapshot_date'),
        Index('idx_position_history_stock', 'stock_code'),
        UniqueConstraint('backtest_id', 'snapshot_date', 'stock_code', name='uq_position_history'),
        {"comment": "백테스트 포지션 히스토리"}
    )


class BacktestMonthlyStats(Base):
    """
    백테스트 월별 통계
    """
    __tablename__ = "backtest_monthly_stats"

    # Primary Key
    stat_id = Column(Integer, primary_key=True, autoincrement=True, comment="통계 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 기간 정보
    year = Column(Integer, nullable=False, comment="년도")
    month = Column(Integer, nullable=False, comment="월")

    # 수익률 지표
    monthly_return = Column(Numeric(10, 4), nullable=False, comment="월 수익률 (%)")
    cumulative_return = Column(Numeric(10, 4), nullable=False, comment="누적 수익률 (%)")

    # 리스크 지표
    monthly_volatility = Column(Numeric(10, 4), nullable=False, comment="월 변동성 (%)")
    max_drawdown = Column(Numeric(10, 4), nullable=False, comment="월 최대 낙폭 (%)")

    # 거래 통계
    total_trades = Column(Integer, nullable=False, comment="거래 횟수")
    winning_trades = Column(Integer, nullable=False, comment="수익 거래")
    losing_trades = Column(Integer, nullable=False, comment="손실 거래")
    win_rate = Column(Numeric(10, 4), nullable=False, comment="승률 (%)")

    # 포지션 정보
    avg_positions = Column(Numeric(10, 2), nullable=False, comment="평균 포지션 수")
    turnover_rate = Column(Numeric(10, 4), nullable=False, comment="회전율 (%)")

    # 자산 정보
    start_capital = Column(Numeric(20, 2), nullable=False, comment="월초 자산")
    end_capital = Column(Numeric(20, 2), nullable=False, comment="월말 자산")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="monthly_stats")

    __table_args__ = (
        Index('idx_monthly_stats_backtest_period', 'backtest_id', 'year', 'month'),
        UniqueConstraint('backtest_id', 'year', 'month', name='uq_monthly_stats'),
        {"comment": "백테스트 월별 통계"}
    )


class BacktestYearlyStats(Base):
    """
    백테스트 연도별 통계
    """
    __tablename__ = "backtest_yearly_stats"

    # Primary Key
    stat_id = Column(Integer, primary_key=True, autoincrement=True, comment="통계 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 기간 정보
    year = Column(Integer, nullable=False, comment="년도")

    # 수익률 지표
    yearly_return = Column(Numeric(10, 4), nullable=False, comment="연간 수익률 (%)")
    cumulative_return = Column(Numeric(10, 4), nullable=False, comment="누적 수익률 (%)")

    # 리스크 지표
    yearly_volatility = Column(Numeric(10, 4), nullable=False, comment="연간 변동성 (%)")
    sharpe_ratio = Column(Numeric(10, 4), nullable=False, comment="샤프 비율")
    sortino_ratio = Column(Numeric(10, 4), nullable=False, comment="소르티노 비율")
    max_drawdown = Column(Numeric(10, 4), nullable=False, comment="연간 최대 낙폭 (%)")

    # 거래 통계
    total_trades = Column(Integer, nullable=False, comment="거래 횟수")
    win_rate = Column(Numeric(10, 4), nullable=False, comment="승률 (%)")
    profit_factor = Column(Numeric(10, 4), nullable=False, comment="손익 비율")

    # 자산 정보
    start_capital = Column(Numeric(20, 2), nullable=False, comment="연초 자산")
    end_capital = Column(Numeric(20, 2), nullable=False, comment="연말 자산")
    peak_capital = Column(Numeric(20, 2), nullable=False, comment="최대 자산")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="yearly_stats")

    __table_args__ = (
        Index('idx_yearly_stats_backtest_year', 'backtest_id', 'year'),
        UniqueConstraint('backtest_id', 'year', name='uq_yearly_stats'),
        {"comment": "백테스트 연도별 통계"}
    )


class BacktestDrawdownPeriod(Base):
    """
    백테스트 낙폭 기간 분석
    """
    __tablename__ = "backtest_drawdown_periods"

    # Primary Key
    period_id = Column(Integer, primary_key=True, autoincrement=True, comment="기간 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 기간 정보
    start_date = Column(Date, nullable=False, comment="낙폭 시작일")
    end_date = Column(Date, nullable=True, comment="낙폭 종료일 (회복일)")
    duration_days = Column(Integer, nullable=False, comment="지속 기간 (일)")

    # 낙폭 정보
    peak_value = Column(Numeric(20, 2), nullable=False, comment="고점 가치")
    trough_value = Column(Numeric(20, 2), nullable=False, comment="저점 가치")
    drawdown_amount = Column(Numeric(20, 2), nullable=False, comment="낙폭 금액")
    drawdown_pct = Column(Numeric(10, 4), nullable=False, comment="낙폭률 (%)")

    # 회복 정보
    is_recovered = Column(Boolean, default=False, comment="회복 여부")
    recovery_days = Column(Integer, nullable=True, comment="회복 기간 (일)")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="drawdown_periods")

    __table_args__ = (
        Index('idx_drawdown_periods_backtest', 'backtest_id'),
        Index('idx_drawdown_periods_dates', 'start_date', 'end_date'),
        {"comment": "백테스트 낙폭 기간 분석"}
    )


class BacktestFactorContribution(Base):
    """
    백테스트 팩터 기여도 분석
    """
    __tablename__ = "backtest_factor_contributions"

    # Primary Key
    contribution_id = Column(Integer, primary_key=True, autoincrement=True, comment="기여도 고유 ID")

    # Foreign Key
    backtest_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("backtest_sessions_extended.backtest_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="백테스트 참조 ID"
    )

    # 팩터 정보
    factor_name = Column(String(50), nullable=False, comment="팩터명")
    factor_category = Column(String(50), nullable=False, comment="팩터 카테고리")

    # 기여도 분석
    total_trades = Column(Integer, nullable=False, comment="해당 팩터 관련 거래수")
    winning_trades = Column(Integer, nullable=False, comment="수익 거래수")
    win_rate = Column(Numeric(10, 4), nullable=False, comment="승률 (%)")

    # 수익 기여도
    total_return = Column(Numeric(20, 2), nullable=False, comment="총 수익")
    avg_return = Column(Numeric(10, 4), nullable=False, comment="평균 수익률 (%)")
    contribution_score = Column(Numeric(10, 4), nullable=False, comment="기여도 점수")

    # 중요도
    importance_rank = Column(Integer, nullable=False, comment="중요도 순위")
    correlation_with_return = Column(Numeric(10, 4), nullable=True, comment="수익률과의 상관계수")

    # Relationship
    session = relationship("BacktestSessionExtended", back_populates="factor_contributions")

    __table_args__ = (
        Index('idx_factor_contributions_backtest', 'backtest_id'),
        UniqueConstraint('backtest_id', 'factor_name', name='uq_factor_contribution'),
        {"comment": "백테스트 팩터 기여도 분석"}
    )