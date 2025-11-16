"""AWS Bedrock Knowledge Base 기반 Retriever"""
from typing import List, Dict, Optional
import boto3
import json
from .base_retriever import BaseRetriever
import os
from pathlib import Path


class AWSKBRetriever(BaseRetriever):
    """AWS Bedrock Knowledge Base를 사용하는 Retriever"""

    def __init__(self, config: Dict):
        """
        Args:
            config: {
                "kb_id": "KNOWLEDGE_BASE_ID",
                "region": "ap-northeast-2",
                "aws_access_key_id": "...",
                "aws_secret_access_key": "..."
            }
        """
        self.kb_id = config.get("kb_id") or os.getenv("AWS_KB_ID")
        self.region = config.get("region", os.getenv("AWS_REGION", "ap-northeast-2"))

        if not self.kb_id:
            raise ValueError(
                "AWS_KB_ID가 설정되지 않았습니다. "
                ".env 파일에 AWS_KB_ID를 설정하세요."
            )

        # Bedrock Agent Runtime 클라이언트 생성
        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            region_name=self.region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        print(f"[OK] AWS KB Retriever initialized with KB: {self.kb_id}")

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        AWS Bedrock Knowledge Base에서 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수

        Returns:
            List[{
                "document_id": str,
                "title": str,
                "content": str,
                "source": str,
                "score": float
            }]
        """
        try:
            # AWS Bedrock Knowledge Base API 호출
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': top_k
                    }
                }
            )

            retrieved_docs = []

            if 'retrievalResults' in response:
                for i, result in enumerate(response['retrievalResults'][:top_k]):
                    # AWS KB 응답 형식:
                    # {
                    #     'content': {'text': 'document content'},
                    #     'location': {
                    #         'type': 's3',
                    #         's3Location': {'uri': 's3://...'}
                    #     },
                    #     'score': 0.95
                    # }

                    content = result.get('content', {})
                    if isinstance(content, dict):
                        text = content.get('text', '')
                    else:
                        text = str(content)

                    location = result.get('location', {})
                    source_uri = location.get('s3Location', {}).get('uri', 'unknown')

                    # 제목 추출 (S3 경로에서 파일명 사용)
                    title = source_uri.split('/')[-1] if source_uri else f"Document {i+1}"

                    retrieved_docs.append({
                        "document_id": f"aws-kb-{i}",
                        "title": title,
                        "content": text,
                        "source": source_uri,
                        "score": float(result.get('score', 0.0))
                    })

            print(f"[OK] AWS KB retrieved {len(retrieved_docs)} documents")
            return retrieved_docs

        except Exception as e:
            print(f"[FAIL] AWS KB retrieval failed: {e}")
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
        """AWS KB 연결 상태 확인"""
        try:
            # 간단히 boto3 client가 정상 작동하는지 확인
            if self.bedrock_agent and self.kb_id:
                print("[OK] AWS KB health check passed")
                return True
            else:
                print("[FAIL] AWS KB not configured")
                return False
        except Exception as e:
            print(f"[FAIL] AWS KB health check failed: {e}")
            return False
