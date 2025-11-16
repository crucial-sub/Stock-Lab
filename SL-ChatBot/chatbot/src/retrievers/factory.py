"""Retriever 팩토리 - 환경에 따라 적절한 Retriever 생성"""
from typing import Dict, Optional
from .base_retriever import BaseRetriever
from .aws_kb_retriever import AWSKBRetriever
import os

# ChromaDB는 선택적으로 import
try:
    from .chroma_retriever import ChromaDBRetriever
    HAS_CHROMADB = True
except ImportError:
    ChromaDBRetriever = None
    HAS_CHROMADB = False


class RetrieverFactory:
    """Retriever 인스턴스를 생성하는 팩토리"""

    @staticmethod
    def create_retriever(
        retriever_type: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> BaseRetriever:
        """
        환경 설정에 따라 Retriever 생성

        Args:
            retriever_type: "aws_kb" | "chroma" | None (자동 선택)
            config: Retriever 설정 딕셔너리

        Returns:
            BaseRetriever 인스턴스
        """
        config = config or {}

        # 자동 선택: RETRIEVER_TYPE 환경변수 확인, 없으면 AWS KB ID 확인
        if retriever_type is None:
            retriever_type = os.getenv("RETRIEVER_TYPE")
            if retriever_type is None:
                if os.getenv("AWS_KB_ID"):
                    retriever_type = "aws_kb"
                else:
                    retriever_type = "chroma" if HAS_CHROMADB else "aws_kb"

        print(f"Creating {retriever_type} retriever")

        if retriever_type == "aws_kb":
            if not os.getenv("AWS_KB_ID"):
                raise ValueError(
                    "AWS_KB_ID 환경 변수가 설정되지 않았습니다. "
                    ".env 파일에 AWS_KB_ID를 설정하세요."
                )
            return AWSKBRetriever(config)

        elif retriever_type == "chroma":
            if not HAS_CHROMADB:
                raise ImportError(
                    "chromadb가 설치되어 있지 않습니다. "
                    "설치: pip install chromadb"
                )
            return ChromaDBRetriever(config)

        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")

    @staticmethod
    def create_with_fallback(
        primary_type: str = "aws_kb",
        fallback_type: str = "chroma",
        config: Optional[Dict] = None
    ) -> BaseRetriever:
        """
        Fallback을 지원하는 Retriever 생성
        (Primary가 실패하면 Fallback으로 자동 전환)

        Args:
            primary_type: 주 Retriever 타입
            fallback_type: 폴백 Retriever 타입
            config: 공통 설정

        Returns:
            BaseRetriever 인스턴스 (실제로는 FallbackRetriever)
        """
        from .fallback_retriever import FallbackRetriever

        config = config or {}

        try:
            primary = RetrieverFactory.create_retriever(primary_type, config)
            fallback = RetrieverFactory.create_retriever(fallback_type, config)
            return FallbackRetriever(primary, fallback)
        except Exception as e:
            print(f"Warning: Failed to create fallback retriever: {e}")
            return RetrieverFactory.create_retriever(fallback_type, config)
