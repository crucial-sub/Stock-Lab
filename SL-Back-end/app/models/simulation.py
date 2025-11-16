"""
백테스팅 시뮬레이션 관련 테이블 모델
quant_simulation_design_document.md 기반
"""
from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, DECIMAL, Boolean, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


def generate_uuid():
    """UUID 생성 함수"""
    return str(uuid.uuid4())


class FactorCategory(Base):
    """팩터 카테고리 테이블"""
    __tablename__ = "factor_categories"

    category_id = Column(String(50), primary_key=True, comment="카테고리 ID")
    category_name = Column(String(100), nullable=False, comment="카테고리명")
    description = Column(Text, nullable=True, comment="설명")
    display_order = Column(Integer, default=0, comment="표시 순서")

    # Relationships
    factors = relationship("Factor", back_populates="category")

    __table_args__ = (
        {"comment": "팩터 카테고리 테이블 (가치, 성장, 퀄리티, 모멘텀, 규모)"}
    )


class Factor(Base):
    """팩터 정의 테이블"""
    __tablename__ = "factors"

    factor_id = Column(String(50), primary_key=True, comment="팩터 ID")
    category_id = Column(
        String(50),
        ForeignKey("factor_categories.category_id"),
        nullable=False,
        index=True,
        comment="카테고리 참조 ID"
    )
    factor_name = Column(String(200), nullable=False, comment="팩터명")
    calculation_type = Column(String(50), nullable=False, comment="계산 유형 (FUNDAMENTAL/TECHNICAL/CUSTOM)")
    formula = Column(Text, nullable=True, comment="계산 공식")
    description = Column(Text, nullable=True, comment="팩터 설명")
    update_frequency = Column(String(20), nullable=True, comment="업데이트 주기 (DAILY/QUARTERLY)")
    is_active = Column(Boolean, default=True, comment="활성화 여부")

    # Relationships
    category = relationship("FactorCategory", back_populates="factors")
    strategy_factors = relationship("StrategyFactor", back_populates="factor")

    __table_args__ = (
        Index('idx_factors_category', 'category_id', 'is_active'),
        {"comment": "팩터 정의 테이블"}
    )


class PortfolioStrategy(Base):
    """포트폴리오 전략 테이블"""
    __tablename__ = "portfolio_strategies"

    strategy_id = Column(String(36), primary_key=True, default=generate_uuid, comment="전략 고유 ID (UUID)")
    strategy_name = Column(String(200), nullable=False, comment="전략명")
    strategy_type = Column(String(50), nullable=True, comment="전략 유형 (VALUE/GROWTH/MOMENTUM/MULTI)")
    description = Column(Text, nullable=True, comment="전략 설명")

    # 소유자 정보
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True, comment="전략 생성자 ID (UUID)")

    # 공개 설정
    is_public = Column(Boolean, default=False, nullable=False, comment="공개 여부 (랭킹 집계)")
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")
    hide_strategy_details = Column(Boolean, default=False, nullable=False, comment="전략 내용 숨김 여부")

    # 백테스팅 기간
    backtest_start_date = Column(Date, nullable=True, comment="백테스팅 시작일")
    backtest_end_date = Column(Date, nullable=True, comment="백테스팅 종료일")

    # 유니버스 설정
    universe_type = Column(String(50), nullable=True, comment="유니버스 (KOSPI/KOSDAQ/KOSPI200/ALL)")
    market_cap_filter = Column(String(50), nullable=True, comment="시가총액 필터 (LARGE/MID/SMALL/ALL)")
    sector_filter = Column(JSON, nullable=True, comment="섹터 필터 (JSON)")

    # 초기 자본
    initial_capital = Column(DECIMAL(15, 2), nullable=True, comment="초기 자본금")

    # 메타데이터
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    strategy_factors = relationship("StrategyFactor", back_populates="strategy", cascade="all, delete-orphan")
    trading_rules = relationship("TradingRule", back_populates="strategy", cascade="all, delete-orphan")
    simulation_sessions = relationship("SimulationSession", back_populates="strategy")

    __table_args__ = (
        Index('idx_portfolio_strategies_type', 'strategy_type'),
        Index('idx_portfolio_strategies_user', 'user_id'),
        Index('idx_portfolio_strategies_public', 'is_public', 'user_id'),
        {"comment": "포트폴리오 전략 테이블"}
    )


class StrategyFactor(Base):
    """전략별 팩터 설정 테이블"""
    __tablename__ = "strategy_factors"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="고유 ID")
    strategy_id = Column(
        String(36),
        ForeignKey("portfolio_strategies.strategy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="전략 참조 ID"
    )
    factor_id = Column(
        String(50),
        ForeignKey("factors.factor_id"),
        nullable=False,
        index=True,
        comment="팩터 참조 ID"
    )

    # 팩터 사용 방식
    usage_type = Column(String(20), nullable=False, comment="사용 유형 (SCREENING/RANKING/SCORING)")
    operator = Column(String(10), nullable=True, comment="연산자 (GT/LT/EQ/TOP_N/BOTTOM_N)")
    threshold_value = Column(DECIMAL(15, 4), nullable=True, comment="임계값")
    weight = Column(DECIMAL(5, 4), nullable=True, comment="가중치 (0~1)")
    direction = Column(String(10), nullable=True, comment="방향 (POSITIVE/NEGATIVE)")

    # Relationships
    strategy = relationship("PortfolioStrategy", back_populates="strategy_factors")
    factor = relationship("Factor", back_populates="strategy_factors")

    __table_args__ = (
        Index('idx_strategy_factors_strategy', 'strategy_id', 'usage_type'),
        {"comment": "전략별 팩터 설정 테이블"}
    )


class TradingRule(Base):
    """매매 규칙 테이블"""
    __tablename__ = "trading_rules"

    rule_id = Column(Integer, primary_key=True, autoincrement=True, comment="규칙 ID")
    strategy_id = Column(
        String(36),
        ForeignKey("portfolio_strategies.strategy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="전략 참조 ID"
    )

    # 매매 규칙
    rule_type = Column(String(50), nullable=False, comment="규칙 유형 (REBALANCE/STOP_LOSS/TAKE_PROFIT)")
    rebalance_frequency = Column(String(20), nullable=True, comment="리밸런싱 주기 (DAILY/WEEKLY/MONTHLY/QUARTERLY)")
    rebalance_day = Column(Integer, nullable=True, comment="리밸런싱 일 (월별: 1~31, 주별: 1~5)")

    # 포지션 관리
    position_sizing = Column(String(50), nullable=True, comment="포지션 크기 (EQUAL_WEIGHT/MARKET_CAP/RISK_PARITY)")
    max_positions = Column(Integer, nullable=True, comment="최대 보유 종목 수")
    min_position_weight = Column(DECIMAL(5, 4), nullable=True, comment="최소 종목 비중")
    max_position_weight = Column(DECIMAL(5, 4), nullable=True, comment="최대 종목 비중")

    # 리스크 관리
    stop_loss_pct = Column(DECIMAL(5, 2), nullable=True, comment="손절매 비율 (%)")
    take_profit_pct = Column(DECIMAL(5, 2), nullable=True, comment="익절매 비율 (%)")

    # 거래 비용
    commission_rate = Column(DECIMAL(6, 5), default=0.00015, comment="수수료율 (0.015%)")
    tax_rate = Column(DECIMAL(6, 5), default=0.0023, comment="세금률 (0.23%)")

    # 조건
    buy_condition = Column(JSON, nullable=True, comment="매수 조건 (JSON)")
    sell_condition = Column(JSON, nullable=True, comment="매도 조건 (JSON)")

    # Relationships
    strategy = relationship("PortfolioStrategy", back_populates="trading_rules")

    __table_args__ = (
        {"comment": "매매 규칙 테이블"}
    )


class SimulationSession(Base):
    """시뮬레이션 세션 테이블"""
    __tablename__ = "simulation_sessions"

    session_id = Column(String(36), primary_key=True, default=generate_uuid, comment="세션 ID (UUID)")
    strategy_id = Column(
        String(36),
        ForeignKey("portfolio_strategies.strategy_id"),
        nullable=False,
        index=True,
        comment="전략 참조 ID"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
        comment="사용자 참조 ID"
    )

    session_name = Column(String(200), nullable=True, comment="세션명")
    start_date = Column(Date, nullable=False, comment="시뮬레이션 시작일")
    end_date = Column(Date, nullable=False, comment="시뮬레이션 종료일")
    initial_capital = Column(DECIMAL(15, 2), nullable=False, comment="초기 자본금")

    # 벤치마크
    benchmark = Column(String(50), nullable=True, comment="벤치마크 (KOSPI/KOSDAQ/KOSPI200)")

    # 실행 상태
    status = Column(String(20), default='PENDING', comment="상태 (PENDING/RUNNING/COMPLETED/FAILED)")
    progress = Column(Integer, default=0, comment="진행률 (%)")
    error_message = Column(Text, nullable=True, comment="에러 메시지")

    # 실시간 진행 상황 (백테스트 실행 중에만 사용)
    current_date = Column("current_date", Date, nullable=True, comment="현재 처리 중인 날짜")
    buy_count = Column(Integer, default=0, comment="현재까지 매수 횟수")
    sell_count = Column(Integer, default=0, comment="현재까지 매도 횟수")
    current_return = Column(DECIMAL(10, 4), nullable=True, comment="현재 수익률 (%)")
    current_capital = Column(DECIMAL(15, 2), nullable=True, comment="현재 자본금")
    current_mdd = Column(DECIMAL(10, 4), nullable=True, comment="현재 MDD (%)")

    # 공유 설정
    is_public = Column(Boolean, default=False, comment="공개 여부 (랭킹 노출)")
    is_anonymous = Column(Boolean, default=False, comment="익명 공개 여부")
    show_strategy = Column(Boolean, default=False, comment="전략 상세 공개 여부")
    is_active = Column(Boolean, default=False, nullable=False, comment="활성화 여부 (계좌 연동)")
    description = Column(Text, nullable=True, comment="포트폴리오 설명")
    share_url = Column(String(100), nullable=True, unique=True, index=True, comment="공유 URL 슬러그")

    # 커뮤니티 기능
    view_count = Column(Integer, default=0, comment="조회수")
    like_count = Column(Integer, default=0, comment="좋아요 수")

    # 메타데이터
    started_at = Column(TIMESTAMP, nullable=True, comment="실행 시작 시간")
    completed_at = Column(TIMESTAMP, nullable=True, comment="실행 완료 시간")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False, comment="수정일시")

    # Relationships
    user = relationship("User", back_populates="simulation_sessions")
    strategy = relationship("PortfolioStrategy", back_populates="simulation_sessions")
    statistics = relationship("SimulationStatistics", back_populates="session", uselist=False, cascade="all, delete-orphan")
    daily_values = relationship("SimulationDailyValue", back_populates="session", cascade="all, delete-orphan")
    trades = relationship("SimulationTrade", back_populates="session", cascade="all, delete-orphan")
    positions = relationship("SimulationPosition", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_simulation_sessions_status', 'status'),
        Index('idx_simulation_sessions_strategy_date', 'strategy_id', 'start_date', 'end_date'),
        Index('idx_simulation_sessions_user_created', 'user_id', 'created_at'),  # 마이페이지용
        Index('idx_simulation_sessions_public_created', 'is_public', 'created_at'),  # 랭킹용
        Index('idx_simulation_sessions_share_url', 'share_url'),  # 공유 URL 조회
        {"comment": "시뮬레이션 세션 테이블"}
    )


class SimulationStatistics(Base):
    """시뮬레이션 통계 테이블"""
    __tablename__ = "simulation_statistics"

    stat_id = Column(Integer, primary_key=True, autoincrement=True, comment="통계 ID")
    session_id = Column(
        String(36),
        ForeignKey("simulation_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="세션 참조 ID"
    )

    # 수익률 지표
    total_return = Column(DECIMAL(10, 4), nullable=True, comment="총 수익률 (%)")
    annualized_return = Column(DECIMAL(10, 4), nullable=True, comment="연환산 수익률 (CAGR, %)")
    benchmark_return = Column(DECIMAL(10, 4), nullable=True, comment="벤치마크 수익률 (%)")
    excess_return = Column(DECIMAL(10, 4), nullable=True, comment="초과 수익률 (%)")

    # 리스크 지표
    volatility = Column(DECIMAL(10, 4), nullable=True, comment="변동성 (%)")
    max_drawdown = Column(DECIMAL(10, 4), nullable=True, comment="최대 낙폭 (MDD, %)")
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True, comment="샤프 비율")
    sortino_ratio = Column(DECIMAL(10, 4), nullable=True, comment="소르티노 비율")

    # 거래 통계
    total_trades = Column(Integer, default=0, comment="총 거래 횟수")
    winning_trades = Column(Integer, default=0, comment="수익 거래 횟수")
    losing_trades = Column(Integer, default=0, comment="손실 거래 횟수")
    win_rate = Column(DECIMAL(5, 2), nullable=True, comment="승률 (%)")
    avg_profit = Column(DECIMAL(15, 2), nullable=True, comment="평균 수익")
    avg_loss = Column(DECIMAL(15, 2), nullable=True, comment="평균 손실")
    profit_factor = Column(DECIMAL(10, 4), nullable=True, comment="손익비")
    avg_holding_period = Column(Integer, nullable=True, comment="평균 보유기간 (일)")

    # 최종 자본
    final_capital = Column(DECIMAL(15, 2), nullable=True, comment="최종 자본금")
    total_commission = Column(DECIMAL(15, 2), nullable=True, comment="총 수수료")
    total_tax = Column(DECIMAL(15, 2), nullable=True, comment="총 세금")

    # Relationships
    session = relationship("SimulationSession", back_populates="statistics")

    __table_args__ = (
        {"comment": "시뮬레이션 통계 테이블"}
    )


class SimulationDailyValue(Base):
    """시뮬레이션 일별 가치 테이블"""
    __tablename__ = "simulation_daily_values"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="고유 ID")
    session_id = Column(
        String(36),
        ForeignKey("simulation_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="세션 참조 ID"
    )
    date = Column(Date, nullable=False, index=True, comment="날짜")

    # 포트폴리오 가치
    portfolio_value = Column(DECIMAL(15, 2), nullable=False, comment="포트폴리오 가치")
    cash = Column(DECIMAL(15, 2), nullable=False, comment="현금")
    position_value = Column(DECIMAL(15, 2), nullable=False, comment="포지션 가치")

    # 수익률
    daily_return = Column(DECIMAL(10, 4), nullable=True, comment="일일 수익률 (%)")
    cumulative_return = Column(DECIMAL(10, 4), nullable=True, comment="누적 수익률 (%)")
    benchmark_return = Column(DECIMAL(10, 4), nullable=True, comment="벤치마크 일일 수익률 (%)")
    benchmark_cum_return = Column(DECIMAL(10, 4), nullable=True, comment="벤치마크 누적 수익률 (%)")

    # 리스크
    daily_drawdown = Column(DECIMAL(10, 4), nullable=True, comment="일일 낙폭 (%)")

    # Relationships
    session = relationship("SimulationSession", back_populates="daily_values")

    __table_args__ = (
        Index('idx_simulation_daily_values_session_date', 'session_id', 'date'),
        {"comment": "시뮬레이션 일별 가치 테이블"}
    )


class SimulationTrade(Base):
    """시뮬레이션 거래 기록 테이블"""
    __tablename__ = "simulation_trades"

    trade_id = Column(Integer, primary_key=True, autoincrement=True, comment="거래 ID")
    session_id = Column(
        String(36),
        ForeignKey("simulation_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="세션 참조 ID"
    )

    trade_date = Column(Date, nullable=False, index=True, comment="거래일")
    stock_code = Column(String(6), nullable=False, index=True, comment="종목코드")
    stock_name = Column(String(100), nullable=True, comment="종목명")

    # 거래 정보
    trade_type = Column(String(10), nullable=False, comment="거래 유형 (BUY/SELL)")
    quantity = Column(Integer, nullable=False, comment="수량")
    price = Column(DECIMAL(15, 2), nullable=False, comment="체결가")
    amount = Column(DECIMAL(15, 2), nullable=False, comment="거래금액")

    # 비용
    commission = Column(DECIMAL(15, 2), nullable=True, comment="수수료")
    tax = Column(DECIMAL(15, 2), nullable=True, comment="세금")

    # 손익 (매도시에만)
    realized_pnl = Column(DECIMAL(15, 2), nullable=True, comment="실현 손익")
    return_pct = Column(DECIMAL(10, 4), nullable=True, comment="수익률 (%)")
    holding_days = Column(Integer, nullable=True, comment="보유일수")

    # 사유
    reason = Column(String(200), nullable=True, comment="거래 사유")

    # Relationships
    session = relationship("SimulationSession", back_populates="trades")

    __table_args__ = (
        Index('idx_simulation_trades_session_date', 'session_id', 'trade_date'),
        Index('idx_simulation_trades_stock', 'stock_code', 'trade_date'),
        {"comment": "시뮬레이션 거래 기록 테이블"}
    )


class SimulationPosition(Base):
    """시뮬레이션 포지션 테이블"""
    __tablename__ = "simulation_positions"

    position_id = Column(Integer, primary_key=True, autoincrement=True, comment="포지션 ID")
    session_id = Column(
        String(36),
        ForeignKey("simulation_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="세션 참조 ID"
    )

    date = Column(Date, nullable=False, index=True, comment="날짜")
    stock_code = Column(String(6), nullable=False, index=True, comment="종목코드")
    stock_name = Column(String(100), nullable=True, comment="종목명")

    # 포지션 정보
    quantity = Column(Integer, nullable=False, comment="보유 수량")
    avg_buy_price = Column(DECIMAL(15, 2), nullable=False, comment="평균 매수가")
    current_price = Column(DECIMAL(15, 2), nullable=False, comment="현재가")
    market_value = Column(DECIMAL(15, 2), nullable=False, comment="평가금액")

    # 손익
    unrealized_pnl = Column(DECIMAL(15, 2), nullable=True, comment="미실현 손익")
    return_pct = Column(DECIMAL(10, 4), nullable=True, comment="수익률 (%)")

    # 비중
    weight = Column(DECIMAL(5, 4), nullable=True, comment="포트폴리오 비중 (0~1)")

    # Relationships
    session = relationship("SimulationSession", back_populates="positions")

    __table_args__ = (
        Index('idx_simulation_positions_session_date', 'session_id', 'date'),
        Index('idx_simulation_positions_stock_date', 'stock_code', 'date'),
        {"comment": "시뮬레이션 포지션 테이블"}
    )
