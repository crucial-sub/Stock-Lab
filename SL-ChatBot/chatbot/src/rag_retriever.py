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

    def _build_knowledge_base(self) -> List[Dict]:
        """ 팩터 설명 """
        return [
            {
                "id": "per_explanation",
                "title": "PER (주가수익비율) 설명",
                "content": """
PER (Price to Earnings Ratio, 주가수익비율)은 주가를 주당순이익(EPS)으로 나눈 값입니다.
- 계산식: PER = 주가 / EPS
- 낮을수록 저평가된 것으로 판단
- 일반적으로 PER < 15를 저평가로 봄
- 가치투자(Value)의 핵심 지표
""",
                "keywords": ["per", "주가수익비율", "가치", "저평가", "eps"]
            },
            {
                "id": "pbr_explanation",
                "title": "PBR (주가순자산비율) 설명",
                "content": """
PBR (Price to Book Ratio, 주가순자산비율)은 주가를 주당순자산(BPS)으로 나눈 값입니다.
- 계산식: PBR = 주가 / BPS
- PBR < 1이면 순자산보다 저평가
- 일반적으로 PBR < 1.5를 저평가로 봄
- 가치투자 전략에서 PER과 함께 사용
""",
                "keywords": ["pbr", "주가순자산비율", "가치", "저평가", "bps", "순자산"]
            },
            {
                "id": "roe_explanation",
                "title": "ROE (자기자본이익률) 설명",
                "content": """
ROE (Return on Equity, 자기자본이익률)는 기업의 수익성을 나타내는 지표입니다.
- 계산식: ROE = 당기순이익 / 자기자본 × 100
- ROE > 15%를 우량 기업으로 봄
- 높을수록 자본 활용 효율이 높음
- Quality(우량주) 전략의 핵심 지표
""",
                "keywords": ["roe", "자기자본이익률", "수익성", "우량", "quality"]
            },
            {
                "id": "momentum_explanation",
                "title": "Momentum (모멘텀) 전략 설명",
                "content": """
Momentum 전략은 과거 수익률이 높은 종목이 지속적으로 상승할 것이라는 가정에 기반합니다.
- 1개월, 3개월, 6개월, 12개월 수익률 사용
- 상승 추세가 강한 종목 매수
- 일반적으로 상위 20% 수익률 종목 선택
- 단기 투자에 적합
""",
                "keywords": ["모멘텀", "momentum", "수익률", "추세", "단기"]
            },
            {
                "id": "growth_explanation",
                "title": "Growth (성장주) 전략 설명",
                "content": """
Growth 전략은 높은 성장률을 보이는 기업에 투자하는 전략입니다.
- 매출성장률 > 20%
- 영업이익성장률 > 15%
- 순이익성장률 > 15%
- 미래 성장 가능성에 투자
- 중장기 투자에 적합
""",
                "keywords": ["성장", "growth", "매출", "이익", "성장률"]
            },
            {
                "id": "dividend_explanation",
                "title": "Dividend (배당주) 전략 설명",
                "content": """
Dividend 전략은 안정적인 배당 수익을 목표로 하는 전략입니다.
- 배당수익률 > 3%
- 배당성향 안정적 (30-70%)
- 부채비율 < 100%
- 저위험 장기 투자에 적합
- 현금 흐름 중시
""",
                "keywords": ["배당", "dividend", "안정", "저위험", "장기"]
            },
            {
                "id": "value_strategy",
                "title": "Value (가치주) 전략",
                "content": """
Value 전략은 저평가된 우량주를 발굴하는 전략입니다.
핵심 지표:
- PER < 15
- PBR < 1.5
- ROE > 10%
- 부채비율 < 150%
장점: 안정적 수익, 하락 방어
단점: 빠른 수익 어려움
""",
                "keywords": ["가치", "value", "저평가", "per", "pbr", "밸류에이션"]
            },
            {
                "id": "quality_strategy",
                "title": "Quality (우량주) 전략",
                "content": """
Quality 전략은 재무 건전성이 뛰어난 기업에 투자하는 전략입니다.
핵심 지표:
- ROE > 15%
- ROA > 10%
- 영업이익률 > 10%
- 부채비율 < 100%
- 유동비율 > 150%
장점: 안정적 성장
대상: 중장기 투자자
""",
                "keywords": ["우량", "quality", "건전", "roe", "roa", "안정"]
            },
            {
                "id": "multi_factor",
                "title": "Multi-Factor (다중팩터) 전략",
                "content": """
Multi-Factor 전략은 여러 팩터를 조합하여 리스크를 분산하는 전략입니다.
- Value + Growth + Quality + Momentum
- 각 팩터의 장점 결합
- 리스크 분산 효과
- 중위험 중수익 추구
추천 조합:
- PER < 20
- ROE > 12%
- 매출성장률 > 10%
- 3개월 수익률 > 5%
""",
                "keywords": ["다중", "multi", "조합", "분산", "균형"]
            },
            {
                "id": "backtest_explanation",
                "title": "백테스트(Backtest) 설명",
                "content": """
백테스트는 과거 데이터로 투자 전략을 검증하는 과정입니다.
주요 지표:
- 총 수익률 (Total Return): 전체 투자 기간 수익
- 연환산 수익률 (Annualized Return): 연간 평균 수익
- MDD (Maximum Drawdown): 최대 낙폭
- Sharpe Ratio: 위험 대비 수익
- 승률 (Win Rate): 수익 거래 비율

백테스트 설정:
- 기간: 최소 3년 이상 권장
- 리밸런싱: 월간/분기별
- 초기자본: 1억원 기준
- 수수료: 0.3% 적용
""",
                "keywords": ["백테스트", "backtest", "검증", "수익률", "mdd", "샤프"]
            },
            {
                "id": "rebalancing",
                "title": "리밸런싱(Rebalancing) 설명",
                "content": """
리밸런싱은 정기적으로 포트폴리오를 재조정하는 과정입니다.

주기별 특징:
- 일간: 변동성 높음, 수수료 多
- 주간: 단기 전략에 적합
- 월간: 가장 일반적, 균형적
- 분기: 장기 투자에 적합

리밸런싱 시:
1. 기존 포지션 정리
2. 조건 재검증
3. 새로운 종목 선정
4. 동일 가중 배분
""",
                "keywords": ["리밸런싱", "rebalance", "재조정", "포트폴리오"]
            },
            {
                "id": "risk_management",
                "title": "리스크 관리",
                "content": """
퀀트 투자의 리스크 관리 원칙:

1. 분산 투자
   - 최소 10개 이상 종목
   - 섹터 분산 권장

2. 손절 규칙
   - 개별 종목: -10% 손절
   - 포트폴리오: -20% MDD 시 전략 재검토

3. 포지션 사이징
   - 동일 가중: 각 종목 동일 비중
   - 시가총액 가중: 대형주 높은 비중
   - 위험 기반: 변동성 고려

4. 백테스트 주의사항
   - 과최적화(Overfitting) 주의
   - 생존편향(Survivorship Bias) 고려
   - 거래비용 반영 필수
""",
                "keywords": ["리스크", "risk", "손절", "분산", "관리"]
            }
        ]

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
