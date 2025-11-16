"""ChromaDB 기반 Retriever (로컬 테스트용)"""
from typing import List, Dict
import chromadb
import os
import json
from pathlib import Path
from .base_retriever import BaseRetriever


class ChromaDBRetriever(BaseRetriever):
    """현재 RAGRetriever를 추상화한 버전"""

    def __init__(self, config: Dict):
        db_path = config.get("vectordb_path", "rag/vectordb/chroma")
        self.client = chromadb.PersistentClient(path=db_path)

        try:
            self.collection = self.client.get_collection(
                name="quant_knowledge"
            )
            print(f"[OK] ChromaDB collection loaded: {self.collection.count()} documents")
        except Exception as e:
            print(f"⚠️ ChromaDB collection not found, creating new one: {e}")
            # 빈 컬렉션 생성
            self.collection = self.client.create_collection(
                name="quant_knowledge"
            )

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """ChromaDB에서 검색"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            retrieved_docs = []
            if results and results["ids"]:
                for i, doc_id in enumerate(results["ids"][0]):
                    retrieved_docs.append({
                        "document_id": doc_id,
                        "title": results["metadatas"][0][i].get("title", ""),
                        "content": results["documents"][0][i],
                        "source": "chromadb",
                        "score": float(results["distances"][0][i])
                    })
            return retrieved_docs
        except Exception as e:
            print(f"[FAIL] ChromaDB retrieval failed: {e}")
            return []

    async def get_context(self, query: str, top_k: int = 3) -> str:
        """포맷된 컨텍스트 반환"""
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
        """ChromaDB 상태 확인"""
        try:
            self.collection.count() >= 0
            print("[OK] ChromaDB health check passed")
            return True
        except Exception as e:
            print(f"[FAIL] ChromaDB health check failed: {e}")
            return False
