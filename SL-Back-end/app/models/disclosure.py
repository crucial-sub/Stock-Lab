"""
공시 정보 테이블 모델
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Disclosure(Base):
    """
    공시 정보 테이블
    - DART 전자공시 데이터
    """
    __tablename__ = "disclosures"

    # Primary Key
    disclosure_id = Column(Integer, primary_key=True, autoincrement=True, comment="공시 고유 ID")

    # Foreign Key
    company_id = Column(
        Integer,
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="기업 참조 ID"
    )

    # 공시 정보
    rcept_no = Column(String(20), unique=True, nullable=False, index=True, comment="접수번호 (DART 고유번호)")
    corp_cls = Column(String(1), nullable=True, comment="법인 구분 (Y:유가증권, K:코스닥, N:코넥스, E:기타)")
    report_nm = Column(String(300), nullable=True, comment="보고서명")
    flr_nm = Column(String(200), nullable=True, comment="공시제출인명")
    rcept_dt = Column(String(8), nullable=True, index=True, comment="접수일자 (YYYYMMDD)")
    rm = Column(Text, nullable=True, comment="비고")

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="생성일시")

    # Relationships
    company = relationship("Company", back_populates="disclosures")

    # Indexes
    __table_args__ = (
        # 기업별 공시 날짜 조회 최적화
        Index('idx_disclosures_company_rcept_dt', 'company_id', 'rcept_dt'),

        # 보고서 유형별 조회
        Index('idx_disclosures_report_nm', 'report_nm'),

        {"comment": "공시 정보 테이블 - DART 전자공시"}
    )

    def __repr__(self):
        return f"<Disclosure(id={self.disclosure_id}, rcept_no={self.rcept_no}, report={self.report_nm})>"
