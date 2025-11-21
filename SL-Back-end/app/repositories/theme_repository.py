"""
테마 마스터 레포지토리
- DB에서 테마 조회
- 테마 코드 → 한글명 변환
"""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.theme import Theme


class ThemeRepository:
    """테마 마스터 데이터 조회"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Optional[Dict[str, str]] = None

    async def get_all_themes(self) -> List[Theme]:
        """모든 테마 조회"""
        result = await self.db.execute(
            select(Theme).order_by(Theme.theme_code)
        )
        return list(result.scalars().all())

    async def get_theme_mapping(self) -> Dict[str, str]:
        """
        테마 영문명 → 한글명 매핑 딕셔너리 반환

        Returns:
            {"semiconductor": "반도체", "ai": "AI", ...}
        """
        if self._cache is not None:
            return self._cache

        result = await self.db.execute(
            select(Theme.theme_name, Theme.theme_name_kor)
        )
        rows = result.fetchall()

        # 영문명 → 한글명 매핑 (대소문자 무관하게 조회 가능하도록 소문자로 저장)
        self._cache = {
            row[0].lower(): row[1]
            for row in rows
            if row[0] and row[1]
        }
        return self._cache

    async def get_korean_name(self, theme_name_en: str) -> Optional[str]:
        """
        영문 테마명 → 한글 테마명 변환

        Args:
            theme_name_en: 영문 테마명 (예: "semiconductor", "ai")

        Returns:
            한글 테마명 (예: "반도체", "AI") or None
        """
        mapping = await self.get_theme_mapping()
        return mapping.get(theme_name_en.lower())

    async def get_theme_by_code(self, theme_code: str) -> Optional[Theme]:
        """테마 코드로 테마 조회"""
        result = await self.db.execute(
            select(Theme).where(Theme.theme_code == theme_code)
        )
        return result.scalar_one_or_none()

    def clear_cache(self):
        """캐시 초기화"""
        self._cache = None


# Helper function for backward compatibility
async def get_theme_mapping_dict(db: AsyncSession) -> Dict[str, str]:
    """
    하위 호환성을 위한 헬퍼 함수
    기존 THEME_MAPPING 딕셔너리를 대체

    Usage:
        THEME_MAPPING = await get_theme_mapping_dict(db)
        korean_name = THEME_MAPPING.get(theme_name.lower(), theme_name)
    """
    repo = ThemeRepository(db)
    return await repo.get_theme_mapping()
