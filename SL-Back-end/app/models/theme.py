"""
테마 마스터 데이터 모델
- 테마 코드, 영문명, 한글명 관리
"""
from sqlalchemy import Column, String
from app.core.database import Base


class Theme(Base):
    """
    테마 마스터 테이블
    - 테마 코드(T001, T002 등)와 영문/한글명 매핑
    - 단일 소스로 모든 테마 정보 관리
    """
    __tablename__ = "themes"

    # Primary Key (기존 DB 스키마에 맞춤)
    theme_code = Column(String, primary_key=True, nullable=False, comment="테마 코드 (T001, T002 등)")

    # Theme Info
    theme_name = Column(String, nullable=True, comment="테마명 (영문)")
    theme_name_kor = Column(String, nullable=True, comment="테마명 (한글)")

    def __repr__(self):
        return f"<Theme(code={self.theme_code}, name={self.theme_name}, kor={self.theme_name_kor})>"
