"""Simple RAG Retriever for Quant Investment Knowledge.

Upgraded to ChromaDB for vector-based retrieval.
Now uses AWS Bedrock Titan for embeddings.
"""
from typing import List, Dict
import os
import json
import chromadb
import boto3
from botocore.config import Config
from pathlib import Path


class RAGRetriever:
    """ChromaDB-based document retriever."""

    def __init__(self, config: Dict):
        """Initialize with ChromaDB client and knowledge base.

        Args:
            config: RAG configuration dictionary.
        """
        db_path = config.get("vectordb_path", "rag/vectordb/chroma")
        self.client = chromadb.PersistentClient(path=db_path)

        # Configure Bedrock Titan embeddings
        region = os.getenv("AWS_REGION", config.get("region", "us-east-1"))
        embed_model_id = os.getenv(
            "BEDROCK_EMBEDDING_MODEL_ID",
            config.get("embedding_model_id", "amazon.titan-embed-text-v2:0")
        )

        aws_config = Config(
            region_name=region,
            signature_version='v4',
            retries={'max_attempts': 3, 'mode': 'standard'}
        )
        bedrock_client = boto3.client(
            'bedrock-runtime',
            config=aws_config,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        class BedrockTitanEmbeddingFunction:
            """Callable embedding function for Chroma using Bedrock Titan."""

            def __init__(self, client, model_id: str):
                self._client = client
                self._model_id = model_id

            def name(self) -> str:
                """Return the name of this embedding function."""
                return f"bedrock_titan_{self._model_id}"

            def __call__(self, input: List[str]) -> List[List[float]]:
                vectors: List[List[float]] = []
                for t in input:
                    payload = {"inputText": t}
                    resp = self._client.invoke_model(
                        modelId=self._model_id,
                        body=json.dumps(payload)
                    )
                    data = json.loads(resp["body"].read())
                    vec = data.get("embedding") or data.get("vector")
                    if not vec:
                        raise RuntimeError("Bedrock Titan did not return embedding")
                    vectors.append(vec)
                return vectors

            def embed_query(self, input: List[str]) -> List[List[float]]:
                """Embed a list of query texts."""
                vectors: List[List[float]] = []
                for t in input:
                    payload = {"inputText": t}
                    resp = self._client.invoke_model(
                        modelId=self._model_id,
                        body=json.dumps(payload)
                    )
                    data = json.loads(resp["body"].read())
                    vec = data.get("embedding") or data.get("vector")
                    if not vec:
                        raise RuntimeError("Bedrock Titan did not return embedding")
                    vectors.append(vec)
                return vectors


        self.embedding_function = BedrockTitanEmbeddingFunction(
            client=bedrock_client,
            model_id=embed_model_id,
        )

        self.collection = self.client.get_or_create_collection(
            name="quant_knowledge",
            embedding_function=self.embedding_function
        )

        # 컬렉션이 비어있으면 문서 인덱싱
        if self.collection.count() == 0:
            print("ChromaDB 컬렉션이 비어있습니다. 문서 인덱싱 중...")
            self._index_documents()

    def _load_all_documents(self) -> List[Dict]:
        """모든 문서 폴더에서 자동 로드: factors, strategies, policies, beginner_guide, indicators"""
        all_documents = []
        base_path = Path(__file__).parent.parent.parent / "rag" / "documents"

        # 로드할 폴더들
        folders = ["factors", "strategies", "policies", "beginner_guide", "indicators"]

        for folder in folders:
            folder_path = base_path / folder

            if not folder_path.exists():
                print(f"⚠️  폴더 없음: {folder_path}")
                continue

            # metadata.json 로드
            metadata_file = folder_path / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"❌ metadata.json 로드 실패 ({folder}): {e}")

            # .md 파일들 로드
            for md_file in sorted(folder_path.glob("*.md")):
                if md_file.name == "metadata.json":
                    continue

                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 파일명에서 ID 생성
                    file_id = md_file.stem
                    doc_id = f"{folder}_{file_id}"

                    # metadata에서 제목과 요약 가져오기
                    title = f"{folder.upper()}: {file_id.replace('_', ' ').title()}"
                    summary = ""

                    if metadata.get("documents"):
                        for doc_meta in metadata["documents"]:
                            if doc_meta.get("file") == md_file.name:
                                title = doc_meta.get("name", title)
                                summary = doc_meta.get("summary", "")
                                break

                    all_documents.append({
                        "id": doc_id,
                        "title": title,
                        "content": content,
                        "summary": summary,
                        "file": md_file.name,
                        "folder": folder
                    })

                    print(f"✅ 로드됨: {folder}/{md_file.name} -> {title}")

                except Exception as e:
                    print(f"❌ 파일 로드 실패 ({folder}/{md_file.name}): {e}")

        if all_documents:
            print(f"\n📚 총 {len(all_documents)}개 문서 로드 완료\n")
            return all_documents
        else:
            print(f"❌ 문서 로드 실패")
            return []

    def _build_knowledge_base(self) -> List[Dict]:
        """모든 문서를 로드 (factors, strategies, policies, beginner_guide, indicators)"""
        documents = self._load_all_documents()
        if not documents:
            print("❌ 문서를 로드할 수 없습니다.")
            return []
        return documents

    def _index_documents(self):
        """문서를 ChromaDB에 임베딩하여 저장."""
        documents = self._build_knowledge_base()
        self.collection.add(
            ids=[doc["id"] for doc in documents],
            documents=[doc["content"] for doc in documents],
            metadatas=[{"title": doc["title"]} for doc in documents]
        )
        print(f"✅ {len(documents)}개 문서가 ChromaDB에 인덱싱되었습니다.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """쿼리를 기반으로 관련 문서를 검색.

        Args:
            query: 사용자 쿼리.
            top_k: 반환할 문서 수.

        Returns:
            점수가 포함된 관련 문서 리스트.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        retrieved_docs = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                retrieved_docs.append({
                    "document": {
                        "id": doc_id,
                        "title": results["metadatas"][0][i]["title"],
                        "content": results["documents"][0][i]
                    },
                    "score": results["distances"][0][i]
                })
        return retrieved_docs

    def get_context(self, query: str, top_k: int = 3) -> str:
        """LLM을 위한 포맷된 컨텍스트 문자열을 생성.

        Args:
            query: 사용자 쿼리
            top_k: 검색할 문서 수

        Returns:
            포맷된 컨텍스트 문자열
        """
        results = self.retrieve(query, top_k)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            doc = result["document"]
            context_parts.append(
                f"[참고자료 {i}] {doc['title']}\n{doc['content'].strip()}"
            )

        return "\n\n".join(context_parts)
