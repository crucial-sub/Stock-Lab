# SL-Chatbot RAG 설정 가이드

## 📌 현재 상태

### ✅ 완성된 부분

#### 1. 문서 구조 (메타데이터 + 마크다운)
```
documents/
├── metadata.json (전체 카탈로그 인덱스)
├── factors/
│   ├── metadata.json (5개 팩터)
│   ├── value.md ✅ 완료
│   ├── growth.md ✅ 완료
│   ├── quality.md ✅ 완료
│   ├── momentum.md ✅ 완료
│   └── dividend.md ✅ 완료
│
├── strategies/
│   ├── metadata.json (5개 전략)
│   └── value_strategy.md ✅ 완료
│
├── indicators/
│   ├── metadata.json (6개 지표)
│   └── (미작성 - 간단한 지표 설명)
│
├── beginner_guide/
│   ├── metadata.json (4개 가이드)
│   └── (미작성 - 초심자 설명)
│
└── policies/
    ├── metadata.json (4개 정책)
    └── prohibited_phrases.txt ✅ 완료
```

#### 2. 메타데이터 시스템
- ✅ 전체 카탈로그 인덱스 (metadata.json)
- ✅ 카테고리별 메타데이터 (5개)
- ✅ 문서별 메타데이터 필드 (id, name, keywords, priority, etc.)

#### 3. 마크다운 콘텐츠
- ✅ Factors: 5개 문서 (value, growth, quality, momentum, dividend)
- ✅ Strategies: 1개 문서 (value_strategy)
- ✅ Policies: 1개 문서 (prohibited_phrases.txt)

### ⏳ 작성 예정 (17개)

#### Strategies (4개 남음)
- growth_strategy.md
- dividend_strategy.md
- quality_strategy.md
- momentum_strategy.md

#### Indicators (6개)
- per.md
- roe.md
- debt_ratio.md
- roa.md
- pbr.md
- dividend_yield.md

#### Beginner Guide (4개)
- what_is_factor.md
- financial_basics.md
- investment_types.md
- how_to_start.md

#### Policies (3개)
- investment_advisory.md
- risk_warnings.md
- user_protection.md

---

## 🚀 다음 단계

### Phase 1: 마크다운 문서 완성 (선택사항)

**필수는 아님** - 기존 내용으로도 충분히 작동 가능

```bash
# 남은 마크다운 문서 작성
# 각 문서는 기존과 동일한 포맷 유지

# 예상 소요시간: 2~3시간
```

### Phase 2: RAG 엔진 구현 (중요)

#### 2-1. Python 라이브러리 설치

```bash
cd SL-Chatbot/rag
pip install -r requirements.txt
```

**requirements.txt**:
```
chromadb>=0.4.0
langchain>=0.1.0
boto3>=1.28.0
python-dotenv>=1.0.0
```

#### 2-2. RAG 엔진 코드 작성

**`rag/src/rag_engine.py`**:
```python
import json
from pathlib import Path
from typing import List, Dict
import chromadb

class RAGEngine:
    def __init__(self, documents_path: str):
        self.documents_path = Path(documents_path)
        self.client = chromadb.Client()
        self.metadata_index = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """메타데이터 로드"""
        metadata_file = self.documents_path / "metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """키워드 및 벡터 검색"""
        # 1. 메타데이터 검색
        meta_results = self._metadata_search(query)

        # 2. 문서 로드
        documents = self._load_documents(meta_results)

        # 3. 벡터 임베딩 (Bedrock Titan Embeddings)
        embeddings = self._embed_documents(documents)

        # 4. 유사도 검색
        results = self._similarity_search(query, embeddings, top_k)

        return results

    def _metadata_search(self, query: str) -> List[Dict]:
        """메타데이터에서 키워드 검색"""
        results = []
        query_words = query.split()

        for category in self.metadata_index['categories']:
            for doc in category['documents']:
                keywords = doc.get('keywords', [])
                if any(word in keywords for word in query_words):
                    results.append(doc)

        return results

    def _load_documents(self, meta_results: List[Dict]) -> List[str]:
        """문서 파일 로드"""
        documents = []
        for meta in meta_results:
            file_path = self.documents_path / meta['path'] / meta['file']
            with open(file_path, 'r', encoding='utf-8') as f:
                documents.append(f.read())

        return documents

    def _embed_documents(self, documents: List[str]) -> List:
        """Bedrock Titan Embeddings로 임베딩"""
        # TODO: Bedrock 연동
        pass

    def _similarity_search(self, query: str, embeddings: List, top_k: int) -> List[Dict]:
        """유사도 검색"""
        # TODO: Chroma 유사도 검색
        pass
```

#### 2-3. 정책 검증 로직

**`rag/src/policy_validator.py`**:
```python
class PolicyValidator:
    def __init__(self, policies_path: str):
        self.prohibited_phrases = self._load_prohibited_phrases(policies_path)

    def _load_prohibited_phrases(self, path: str) -> List[str]:
        """금지 문구 로드"""
        with open(f"{path}/prohibited_phrases.txt", 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]

    def validate_response(self, response: str) -> tuple[bool, str]:
        """응답 검증

        Returns:
            (is_valid, error_message)
        """
        for phrase in self.prohibited_phrases:
            if self._is_phrase_present(response, phrase):
                return False, f"금지 문구 감지: {phrase}"

        return True, ""

    def _is_phrase_present(self, text: str, phrase: str) -> bool:
        """문구 포함 여부 확인"""
        # 정규표현식 또는 문자열 매칭
        return phrase in text

    def add_safety_warnings(self, response: str) -> str:
        """응답에 안전 경고 추가"""
        warnings = [
            "\n\n⚠️ 주의사항:",
            "- 본 정보는 교육 목적이며 투자 조언이 아닙니다.",
            "- 투자에는 손실 가능성이 있습니다.",
            "- 최종 결정은 본인의 책임입니다.",
            "- 전문가 상담을 받으시기 바랍니다."
        ]

        return response + "".join(warnings)
```

### Phase 3: Chatbot 구현

**`chatbot/src/core/rag_handler.py`**:
```python
from rag.src.rag_engine import RAGEngine
from rag.src.policy_validator import PolicyValidator

class RAGHandler:
    def __init__(self, documents_path: str, policies_path: str):
        self.rag_engine = RAGEngine(documents_path)
        self.validator = PolicyValidator(policies_path)

    def handle_query(self, query: str) -> str:
        """사용자 질문 처리"""

        # 1. RAG 검색
        relevant_docs = self.rag_engine.search(query, top_k=3)
        context = self._format_context(relevant_docs)

        # 2. LLM 호출 (Bedrock)
        response = self._call_llm(query, context)

        # 3. 정책 검증
        is_valid, error_msg = self.validator.validate_response(response)

        if not is_valid:
            # 재생성 또는 거부
            response = f"죄송합니다. {error_msg}"

        # 4. 안전 경고 추가
        response = self.validator.add_safety_warnings(response)

        return response

    def _format_context(self, docs: List[Dict]) -> str:
        """검색 결과를 컨텍스트로 포맷"""
        context = "참고 자료:\n\n"
        for doc in docs:
            context += f"- [{doc['title']}]\n{doc['content']}\n\n"

        return context

    def _call_llm(self, query: str, context: str) -> str:
        """Bedrock LLM 호출"""
        # TODO: Bedrock 연동
        prompt = f"""당신은 투자 교육 전문 AI입니다.

사용자 질문: {query}

참고 자료:
{context}

지침:
1. 위의 참고 자료를 기반으로 답변하세요
2. 특정 종목 추천은 절대 금지
3. 리스크를 강조하세요
4. 전문가 상담을 권장하세요

답변:"""

        # Bedrock 호출
        pass
```

### Phase 4: API 통합

**`api/routes/chat.py`**:
```python
from fastapi import APIRouter, HTTPException
from chatbot.src.core.rag_handler import RAGHandler

router = APIRouter()

rag_handler = RAGHandler(
    documents_path="rag/documents",
    policies_path="rag/documents/policies"
)

@router.post("/message")
async def chat_message(message: str):
    """채팅 메시지 처리"""
    try:
        response = rag_handler.handle_query(message)
        return {
            "message": message,
            "response": response,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📋 구현 체크리스트

### RAG 엔진
- [ ] `rag/src/rag_engine.py` - 기본 RAG 엔진
- [ ] `rag/src/policy_validator.py` - 정책 검증
- [ ] `rag/scripts/build_embeddings.py` - 벡터DB 빌드
- [ ] Chroma DB 설정

### Chatbot
- [ ] `chatbot/src/core/rag_handler.py` - RAG 핸들러
- [ ] `chatbot/src/llm/client.py` - Bedrock 클라이언트
- [ ] `chatbot/src/llm/prompt_manager.py` - 프롬프트 템플릿

### API
- [ ] `api/routes/chat.py` - 채팅 라우트
- [ ] `api/middleware/policy_checker.py` - 정책 미들웨어

### 테스트
- [ ] `tests/test_rag_engine.py`
- [ ] `tests/test_policy_validator.py`
- [ ] `tests/test_chat_flow.py`

---

## 🎯 즉시 사용 가능한 구성

**현재 상태로도 이미 다음이 가능합니다:**

1. **문서 관리**
   - 메타데이터 기반 카탈로그
   - 카테고리별 정리
   - 검색 키워드 시스템

2. **정책 관리**
   - 금지 문구 필터링
   - 안전 검증 로직

3. **확장성**
   - 새 문서 추가 용이
   - 메타데이터 수정으로 시스템 변경
   - 모듈화된 구조

---

## 💾 파일 구조 최종 확인

```
SL-Chatbot/
├── rag/
│   ├── documents/
│   │   ├── metadata.json ........................ ✅
│   │   ├── factors/ ............................ ✅
│   │   ├── strategies/ ......................... ⏳
│   │   ├── indicators/ ......................... ⏳
│   │   ├── beginner_guide/ ..................... ⏳
│   │   └── policies/ ........................... ⏳
│   │
│   ├── src/ (신규)
│   │   ├── rag_engine.py
│   │   └── policy_validator.py
│   │
│   └── scripts/
│       └── build_embeddings.py
│
├── chatbot/
│   ├── src/
│   │   ├── core/
│   │   │   ├── rag_handler.py
│   │   │   └── intent_classifier.py
│   │   └── llm/
│   │       ├── client.py
│   │       └── prompt_manager.py
│   │
│   └── prompts/
│
├── api/
│   ├── routes/
│   │   └── chat.py
│   └── middleware/
│       └── policy_checker.py
│
└── tests/
    ├── test_rag_engine.py
    └── test_policy_validator.py
```

---

## 🔑 핵심 포인트

1. **메타데이터 시스템 구축** ✅
   - 카테고리별 인덱싱
   - 검색 키워드 관리
   - 버전 추적

2. **마크다운 콘텐츠** ✅ (부분)
   - Factors 5개 완성
   - Strategies 1개 완성
   - 나머지는 선택사항

3. **정책 검증** ✅
   - 금지 문구 필터
   - 안전 가이드라인
   - 응답 검증 로직

4. **RAG 검색** ⏳
   - 메타 검색 구현
   - 벡터 임베딩
   - 유사도 검색

5. **LLM 통합** ⏳
   - Bedrock 연동
   - 프롬프트 엔지니어링
   - 응답 생성

---

## 📞 구현 문의

- **질문**: 메타데이터 구조가 맞는가?
- **답변**: 네, 필요한 모든 필드가 포함되어 있습니다.

- **질문**: 문서 추가는 어떻게 하는가?
- **답변**: 마크다운 파일 생성 + metadata.json 수정

- **질문**: RAG 검색이 느리면?
- **답변**: 메타 검색으로 먼저 필터링 → 문서 로드

---

## 🎓 참고 자료

- [Chroma DB 문서](https://docs.trychroma.com/)
- [LangChain RAG](https://python.langchain.com/en/latest/modules/retrieval/)
- [AWS Bedrock API](https://docs.aws.amazon.com/bedrock/)

