"""
현금흐름표 테이블 모델
"""
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class CashflowStatement(Base):
    """
    현금흐름표 테이블
    - 일정 기간의 현금 유입/유출 정보
    - 영업/투자/재무 활동 현금흐름
    """
    __tablename__ = "cashflow_statements"

    # Primary Key
    cf_id = Column(BigInteger, primary_key=True, autoincrement=True, comment="현금흐름표 항목 고유 ID")

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
    thstrm_nm = Column(String(50), nullable=True, comment="당기명")
    thstrm_dt = Column(String(8), nullable=True, comment="당기 결산일 (YYYYMMDD)")
    thstrm_amount = Column(BigInteger, nullable=True, comment="당기 금액 (원) - 양수:유입, 음수:유출")

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
    financial_statement = relationship("FinancialStatement", back_populates="cashflow_statements")

    # Indexes
    __table_args__ = (
        # 재무제표별 계정과목 조회 최적화
        Index('idx_cashflow_statements_stmt_account', 'stmt_id', 'account_nm'),

        # 정렬 순서 조회
        Index('idx_cashflow_statements_stmt_ord', 'stmt_id', 'ord'),

        {"comment": "현금흐름표 테이블 - 영업/투자/재무 현금흐름"}
    )

    def __repr__(self):
        return f"<CashflowStatement(id={self.cf_id}, stmt_id={self.stmt_id}, account={self.account_nm})>"
