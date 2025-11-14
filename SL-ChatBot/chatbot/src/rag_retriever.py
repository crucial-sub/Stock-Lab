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

        # Index documents if the collection is empty
        if self.collection.count() == 0:
            print("ChromaDB collection is empty. Indexing documents...")
            self._index_documents()

    def _load_factors_from_files(self) -> List[Dict]:
        """factors 폴더에서 마크다운 파일들을 자동으로 로드"""
        documents = []
        factors_dir = Path("rag/documents/factors")

        # 상대 경로가 작동하지 않으면 절대 경로 시도
        if not factors_dir.exists():
            # 현재 파일 기준으로 경로 계산
            current_dir = Path(__file__).parent.parent.parent
            factors_dir = current_dir / "rag" / "documents" / "factors"

        if not factors_dir.exists():
            print(f"❌ factors 폴더를 찾을 수 없습니다: {factors_dir}")
            return []

        # metadata.json에서 문서 정보 읽기
        metadata_file = factors_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception as e:
                print(f"❌ metadata.json 로드 실패: {e}")

        # .md 파일들 로드
        for md_file in sorted(factors_dir.glob("*.md")):
            if md_file.name == "metadata.json":
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 파일명에서 ID 생성 (예: value.md -> factor_value)
                file_id = md_file.stem
                doc_id = f"factor_{file_id}"

                # metadata에서 제목과 요약 가져오기
                title = f"팩터: {file_id.upper()}"
                summary = ""

                if metadata.get("documents"):
                    for doc_meta in metadata["documents"]:
                        if doc_meta.get("file") == md_file.name:
                            title = doc_meta.get("name", title)
                            summary = doc_meta.get("summary", "")
                            break

                documents.append({
                    "id": doc_id,
                    "title": title,
                    "content": content,
                    "summary": summary,
                    "file": md_file.name
                })

                print(f"✅ 로드됨: {md_file.name} -> {title}")

            except Exception as e:
                print(f"❌ 파일 로드 실패 ({md_file.name}): {e}")

        if documents:
            print(f"\n📚 총 {len(documents)}개 팩터 문서 로드 완료\n")
            return documents
        else:
            print(f"❌ factors 문서 로드 실패")
            return []

    def _build_knowledge_base(self) -> List[Dict]:
        """팩터 설명 - 파일에서 자동 로드"""
        documents = self._load_factors_from_files()
        if not documents:
            print("❌ factors 문서를 로드할 수 없습니다.")
            return []
        return documents

    def _index_documents(self):
        """Embed and store documents in ChromaDB."""
        documents = self._build_knowledge_base()
        self.collection.add(
            ids=[doc["id"] for doc in documents],
            documents=[doc["content"] for doc in documents],
            metadatas=[{"title": doc["title"]} for doc in documents]
        )
        print(f"Indexed {len(documents)} documents into ChromaDB.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant documents based on query.

        Args:
            query: User query.
            top_k: Number of documents to return.

        Returns:
            List of relevant documents with scores.
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
        """Get formatted context string for LLM.

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            Formatted context string
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
