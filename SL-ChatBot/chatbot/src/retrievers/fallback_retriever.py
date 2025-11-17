"""Primary 실패 시 자동으로 Fallback으로 전환하는 Retriever"""
from typing import List, Dict, Optional
from .base_retriever import BaseRetriever


class FallbackRetriever(BaseRetriever):
    """Primary 실패 시 Fallback으로 자동 전환"""

    def __init__(self, primary: BaseRetriever, fallback: BaseRetriever):
        self.primary = primary
        self.fallback = fallback
        self.current = primary
        self._primary_failed = False

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Primary로 시도, 실패하면 Fallback 사용"""

        # Primary가 이미 실패했으면 Fallback 직접 사용
        if self._primary_failed:
            return await self.fallback.retrieve(query, top_k)

        try:
            results = await self.primary.retrieve(query, top_k)
            if results:  # 결과가 있으면 성공
                return results
            else:
                # 결과가 없으면 Fallback 시도
                print("⚠️ Primary retriever returned no results, trying fallback")
                return await self.fallback.retrieve(query, top_k)

        except Exception as e:
            print(f"[WARN] Primary retriever failed: {e}, switching to fallback")
            self._primary_failed = True
            try:
                return await self.fallback.retrieve(query, top_k)
            except Exception as fallback_error:
                print(f"[FAIL] Both primary and fallback failed: {fallback_error}")
                return []

    async def get_context(self, query: str, top_k: int = 3) -> str:
        """컨텍스트 생성"""
        results = await self.retrieve(query, top_k)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[참고자료 {i}] {result['title']}\n{result['content'].strip()}"
            )

        return "\n\n".join(context_parts)

    async def health_check(self) -> bool:
        """Primary 또는 Fallback이 살아있는지 확인"""
        primary_ok = await self.primary.health_check()

        if primary_ok:
            self._primary_failed = False
            return True

        # Primary가 실패했으면 Fallback 확인
        fallback_ok = await self.fallback.health_check()
        if fallback_ok:
            print("⚠️ Primary retriever unhealthy, using fallback")
            self._primary_failed = True
            return True

        print("❌ Both primary and fallback retrievers are unhealthy")
        return False
