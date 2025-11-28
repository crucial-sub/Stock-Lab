"""
투자 전략 모델
AI 어시스턴트 전략 추천 및 백테스트 실행을 위한 전략 데이터
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class InvestmentStrategy(Base):
    """투자 전략 마스터 테이블"""
    __tablename__ = "investment_strategies"

    # 기본 식별자
    id = Column(String(50), primary_key=True, index=True, comment="전략 고유 식별자")

    # 전략 메타데이터
    name = Column(String(100), nullable=False, comment="전략 표시명")
    summary = Column(Text, nullable=False, comment="전략 요약 설명")
    description = Column(Text, nullable=True, comment="전략 상세 설명")
    tags = Column(ARRAY(String), nullable=False, index=True, comment="추천 매칭용 태그")

    # 백테스트 실행 설정
    # BacktestRunRequest 형식 (user_id, start_date, end_date, initial_investment 제외)
    backtest_config = Column(JSONB, nullable=False, comment="백테스트 실행 전체 설정")

    # UI 표시용 조건 설명
    display_conditions = Column(JSONB, nullable=False, comment="UI 표시용 조건 배열")

    # 메타데이터
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성일시"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정일시"
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 여부")
    popularity_score = Column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        comment="사용 횟수 (조회 시 증가)"
    )

    def __repr__(self):
        return f"<InvestmentStrategy(id={self.id}, name={self.name}, popularity={self.popularity_score})>"

    def to_dict(self):
        """딕셔너리 변환 (API 응답용)"""
        return {
            "id": self.id,
            "name": self.name,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "backtest_config": self.backtest_config,
            "display_conditions": self.display_conditions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "popularity_score": self.popularity_score,
        }
