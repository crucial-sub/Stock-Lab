"""
재무상태표 테이블 모델
"""
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class BalanceSheet(Base):
    """
    재무상태표 (대차대조표) 테이블
    - 특정 시점의 자산, 부채, 자본 정보
    """
    __tablename__ = "balance_sheets"

    # Primary Key
    bs_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="재무상태표 항목 고유 ID")

    # Foreign Key
    stmt_id = Column(
        Integer,
        ForeignKey("financial_statements.stmt_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="재무제표 참조 ID"
    )

    # 계정과목 정보
    account_id = Column(String(100), nullable=True, comment="계정과목 ID (DART API)")
    account_nm = Column(String(300), nullable=False, index=True, comment="계정과목명")
    account_detail = Column(String(500), nullable=True, comment="계정과목 상세")

    # 당기 (Current Period)
    thstrm_nm = Column(String(50), nullable=True, comment="당기명 (회계기수)")
    thstrm_dt = Column(String(8), nullable=True, comment="당기 결산일 (YYYYMMDD)")
    thstrm_amount = Column(BigInteger, nullable=True, comment="당기 금액 (원)")

    # 전기 (Previous Period)
    frmtrm_nm = Column(String(50), nullable=True, comment="전기명")
    frmtrm_dt = Column(String(8), nullable=True, comment="전기 결산일")
    frmtrm_amount = Column(BigInteger, nullable=True, comment="전기 금액 (원)")

    # 전전기 (Before Previous Period)
    bfefrmtrm_nm = Column(String(50), nullable=True, comment="전전기명")
    bfefrmtrm_dt = Column(String(8), nullable=True, comment="전전기 결산일")
    bfefrmtrm_amount = Column(BigInteger, nullable=True, comment="전전기 금액 (원)")

    # 정렬 순서
    ord = Column(Integer, nullable=True, comment="계정과목 표시 순서")

    # Relationships
    financial_statement = relationship("FinancialStatement", back_populates="balance_sheets")

    # Indexes
    __table_args__ = (
        # 재무제표별 계정과목 조회 최적화
        Index('idx_balance_sheets_stmt_account', 'stmt_id', 'account_nm'),

        # 정렬 순서 조회
        Index('idx_balance_sheets_stmt_ord', 'stmt_id', 'ord'),

        {"comment": "재무상태표 테이블 - 자산/부채/자본"}
    )

    def __repr__(self):
        return f"<BalanceSheet(id={self.bs_id}, stmt_id={self.stmt_id}, account={self.account_nm})>"
