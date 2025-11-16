"""추상 Retriever 인터페이스"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseRetriever(ABC):
    """모든 Retriever의 기본 인터페이스"""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        관련 문서를 검색합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 수

        Returns:
            List[{
                "document_id": str,
                "title": str,
                "content": str,
                "source": str,
                "score": float
            }]
        """
        pass

    @abstractmethod
    async def get_context(self, query: str, top_k: int = 3) -> str:
        """LLM을 위한 포맷된 컨텍스트 문자열"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Retriever 상태 확인"""
        pass
