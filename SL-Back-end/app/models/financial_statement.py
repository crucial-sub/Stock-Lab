"""
재무제표 메타 테이블 모델
"""
from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class FinancialStatement(Base):
    """
    재무제표 메타 정보 테이블
    - 재무제표의 기본 정보 (연도, 분기, 구분)
    - balance_sheets, income_statements, cashflow_statements의 허브
    """
    __tablename__ = "financial_statements"

    # Primary Key
    stmt_id = Column(Integer, primary_key=True, autoincrement=True, comment="재무제표 고유 ID")

    # Foreign Key
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기업 참조 ID"
    )

    # 재무제표 기본 정보
    bsns_year = Column(String(4), nullable=False, comment="사업연도 (YYYY)")
    reprt_code = Column(
        String(5),
        nullable=False,
        comment="보고서 코드 (11011:사업보고서, 11012:반기, 11013:1분기, 11014:3분기)"
    )
    fs_div = Column(String(3), nullable=True, comment="재무제표 구분 (CFS:연결, OFS:개별)")

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")

    # Relationships
    company = relationship("Company", back_populates="financial_statements")
    balance_sheets = relationship("BalanceSheet", back_populates="financial_statement", lazy="selectin")
    income_statements = relationship("IncomeStatement", back_populates="financial_statement", lazy="selectin")
    cashflow_statements = relationship("CashflowStatement", back_populates="financial_statement", lazy="selectin")

    # Indexes
    __table_args__ = (
        # 유니크 제약: 같은 기업의 같은 연도/분기/구분은 1개만
        UniqueConstraint(
            'company_id', 'bsns_year', 'reprt_code', 'fs_div',
            name='uq_financial_statements_composite'
        ),

        # 기업별 연도 조회 최적화
        Index('idx_financial_statements_company_year', 'company_id', 'bsns_year'),

        # 보고서 코드별 조회
        Index('idx_financial_statements_reprt_code', 'reprt_code'),

        {"comment": "재무제표 메타 정보 테이블"}
    )

    def __repr__(self):
        return f"<FinancialStatement(id={self.stmt_id}, company_id={self.company_id}, year={self.bsns_year}, report={self.reprt_code})>"
