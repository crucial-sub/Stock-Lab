# SL-ChatBot

AI 기반 퀀트 투자 상담 챗봇 시스템

---

## 개요

**SL-ChatBot**은 Stock-Lab 프로젝트의 대화형 AI 어드바이저로, AWS Bedrock Claude Sonnet 4.5와 LangChain을 활용하여 퀀트 투자 전략 상담, 팩터 설명, 백테스트 조건 자동 생성 기능을 제공합니다.

### 핵심 기능

- **자연어 투자 상담** - 팩터, 전략, 백테스트 관련 질문에 실시간 답변
- **RAG 기반 정확성** - 54개 팩터 문서 + 11개 전략 가이드 기반 검색 증강 생성
- **DSL 자동 생성** - 자연어를 백테스트 조건식(DSL)으로 자동 변환
- **스트리밍 응답** - SSE 프로토콜로 토큰 단위 실시간 스트리밍
- **멀티 클라이언트** - 일반 상담/AI 헬퍼/홈 위젯용 3가지 모드

---

## 아키텍처

### 시스템 구조

```
┌─────────────┐
│  Frontend   │
│ (Next.js)   │
└──────┬──────┘
       │ HTTP/SSE
┌──────▼──────────────────────────────────────────┐
│          FastAPI API Server (8001)              │
│  /api/v1/chat/message  (POST)                   │
│  /api/v1/chat/stream   (GET SSE)                │
│  /api/v1/recommend/strategy                     │
│  /api/v1/dsl/generate                           │
└──────┬──────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────┐
│         Chatbot Logic (LangChain)               │
│  ┌───────────────────────────────────────────┐  │
│  │  ChatHandler (Orchestrator)               │  │
│  │  - Session Management (max 10 turns)      │  │
│  │  - Intent Detection                       │  │
│  │  - Client Type Routing                    │  │
│  └──────────┬────────────────────────────────┘  │
│             │                                   │
│  ┌──────────▼────────────────────────────────┐  │
│  │  LangChain Agent + AWS Bedrock            │  │
│  │  - Tool Calling Agent                     │  │
│  │  - Conversation Memory                    │  │
│  │  - 9 Tools (Auto Selection)               │  │
│  └──────────┬────────────────────────────────┘  │
└─────────────┼───────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼──┐  ┌──▼───┐  ┌──▼───────┐
│ RAG  │  │ News │  │ Backend  │
│System│  │ API  │  │ API      │
└──────┘  └──────┘  └──────────┘
```

### RAG 시스템 (환경별)

**프로덕션**
- **AWS Bedrock Knowledge Base**
- S3 문서 저장 + 자동 임베딩
- 관리형 벡터 검색
- 설정: `AWS_KB_ID` 환경변수

**로컬 개발**
- **ChromaDB** (선택적)
- 로컬 임베딩 생성 (`rag/scripts/build_embeddings.py`)
- Sentence Transformers
- 설정: `AWS_KB_ID` 미설정 시 자동 선택

---

## 디렉토리 구조

```
SL-ChatBot/
├── api/                            # FastAPI 웹 서버
│   ├── main.py                     # 앱 진입점
│   ├── routes/                     # API 라우트
│   │   ├── chat.py                 # 채팅 엔드포인트
│   │   ├── recommend.py            # 전략 추천
│   │   └── dsl.py                  # DSL 생성
│   └── models/                     # Pydantic 스키마
│
├── chatbot/                        # 챗봇 로직
│   ├── src/
│   │   ├── main.py                 # QuantAdvisorBot
│   │   ├── handlers/
│   │   │   └── chat_handler.py     # 오케스트레이터
│   │   ├── retrievers/
│   │   │   ├── aws_kb_retriever.py # AWS KB (프로덕션)
│   │   │   └── factory.py          # Retriever 자동 선택
│   │   ├── schemas/
│   │   │   └── dsl_generator.py    # 자연어→DSL 변환
│   │   └── tools.py                # LangChain Tools (9개)
│   └── config.yaml                 # LLM/세션 설정
│
├── rag/                            # RAG 지식 베이스
│   ├── documents/                  # Markdown 문서
│   │   ├── factors/                # 54개 팩터 설명
│   │   ├── strategies/             # 11개 전략 가이드
│   │   ├── beginner_guide/         # 초보자 가이드
│   │   └── policies/               # 투자 자문 정책
│   ├── vectordb/chroma/            # ChromaDB (gitignore)
│   └── scripts/build_embeddings.py # 임베딩 생성
│
├── config/                         # 글로벌 설정
│   ├── factor_alias.json           # 팩터 별칭 매핑
│   ├── forbidden_patterns.yaml     # 금지 패턴
│   └── operator_rules.yaml         # 자연어→연산자 규칙
│
└── prompts/                        # 시스템 프롬프트
    ├── system_assistant.txt        # 일반 상담
    ├── system_ai_helper.txt        # AI 헬퍼
    └── system_home_widget.txt      # 홈 위젯
```

---

## 기술 스택

| 영역 | 기술 | 버전 |
|-----|------|------|
| **LLM** | AWS Bedrock Claude Sonnet 4.5 | - |
| **AI Framework** | LangChain | 0.2+ |
| **Web Framework** | FastAPI | 0.109+ |
| **RAG (Prod)** | AWS Bedrock Knowledge Base | - |
| **RAG (Dev)** | ChromaDB | 0.4+ |
| **Embeddings** | Sentence Transformers | 2.2+ |
| **Async I/O** | HTTPX, aiohttp | - |

---

## 주요 워크플로우

### 1. 일반 대화 (Chat)

```
사용자: "PER이 낮은 종목을 찾고 싶어요"
    ↓
ChatHandler
    ├─ Intent 감지: "factor_explanation"
    ├─ Session 확인: 기존 대화 로드 (최대 10턴)
    └─ LangChain Agent 실행
           ↓
Agent가 Tool 선택
    ├─ get_factor_info("PER")  ← Backend API 호출
    └─ RAG 검색 (자동)
           ├─ AWS KB (프로덕션)
           └─ ChromaDB (로컬)
              → factors/value.md
              → beginner_guide/financial_basics.md
           ↓
Claude Sonnet 4.5
    ├─ System Prompt (client_type별)
    ├─ Retrieved Docs (RAG)
    ├─ Conversation History
    └─ User Question
           ↓
응답 생성
    ├─ 정책 검증 (투자 자문 제한)
    ├─ 금지 문구 필터링
    └─ SSE 스트리밍 or JSON 반환
```

### 2. DSL 생성

```
사용자: "PER 15 이하이고 ROE 10% 이상인 종목"
    ↓
Agent가 Tool 선택
    └─ build_backtest_conditions()
           ↓
dsl_generator.py
    ├─ 자연어 파싱
    ├─ 팩터 추출: ["PER", "ROE"]
    ├─ 연산자 매칭 (operator_rules.yaml)
    │   ├─ "이하" → "<="
    │   └─ "이상" → ">="
    └─ DSL 생성
           ↓
출력: "PER <= 15 AND ROE >= 10"
```

### 3. 전략 추천

```
입력: {risk: "medium", horizon: "long", style: "value"}
    ↓
Agent가 Tool 선택
    └─ recommend_strategy()
           ↓
전략 매트릭스 매칭
    └─ (medium, long) → "quality"
    └─ preferred_style 우선 → "value"
           ↓
전략 상세 정보 반환
    ├─ 이름: "가치주(Value) 전략"
    ├─ 설명: "저평가된 우량주 발굴"
    └─ 조건: ["PER < 15", "PBR < 1.5"]
```

---

## API 명세

챗봇 API의 상세한 엔드포인트, 파라미터, 에러 처리 등은 별도 문서를 참고하세요:

**👉 [CHATBOT_API.md](CHATBOT_API.md) - SL-ChatBot REST API 명세서**

---

## 개발 가이드

### 로컬 개발 환경 설정

**1. 환경 변수 (.env)**
```bash
# AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_DEFAULT_REGION=ap-northeast-2

# LLM
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# RAG (로컬 개발용)
RETRIEVER_TYPE=chroma  # ChromaDB 사용

# Backend
BACKEND_API_URL=http://localhost:8000
```

**2. ChromaDB 임베딩 생성**
```bash
cd SL-ChatBot/rag
pip install -r requirements.txt
python scripts/build_embeddings.py
# vectordb/chroma/ 생성됨
```

**3. API 서버 실행**
```bash
cd SL-ChatBot/api
pip install -r requirements.txt
python main.py
# http://localhost:8001
```

### 새 팩터 문서 추가

**1단계: Markdown 작성**
```bash
# rag/documents/factors/new_factor.md 생성
```

**2단계: 메타데이터 업데이트**
```json
// rag/documents/factors/metadata.json
{
  "documents": [
    {
      "id": "factor_new",
      "name": "새 팩터",
      "file": "new_factor.md",
      "keywords": ["키워드1", "키워드2"]
    }
  ]
}
```

**3단계: 배포**
- **프로덕션:** S3 업로드 → AWS KB 자동 동기화
- **로컬:** `python rag/scripts/build_embeddings.py` 재실행

### LangChain Tools 커스터마이징

`chatbot/src/tools.py`에서 Tool 추가:

```python
@tool
async def new_tool(param: str) -> Dict:
    """Tool description for LLM to understand when to use."""
    # 로직 구현
    return {"success": True, "result": "..."}

# get_tools() 함수의 return 리스트에 추가
return [
    search_stock_news,
    get_factor_info,
    new_tool,  # 추가
    ...
]
```

### 프롬프트 커스터마이징

**클라이언트별 프롬프트:**
- `prompts/system_assistant.txt` - 상세한 교육적 설명
- `prompts/system_ai_helper.txt` - DSL 생성 중심
- `prompts/system_home_widget.txt` - 간결한 답변

**적용 위치:**
`chatbot/src/handlers/chat_handler.py`의 `_load_system_prompt()`

---

## 설정 파일

### chatbot/config.yaml

```yaml
llm:
  provider: "bedrock"
  model: "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
  temperature: 0.7          # 창의성 (0-1)
  max_tokens: 8000          # 최대 출력 길이
  region: "ap-northeast-2"

conversation:
  max_history: 10           # 대화 히스토리 최대 턴
  session_timeout: 3600     # 세션 타임아웃 (초)

backend:
  api_url: "http://localhost:8000"
  timeout: 30
```

### config/operator_rules.yaml

자연어 연산자 매핑:

```yaml
operators:
  greater_than:
    keywords: ["이상", "초과", "넘는", "크다"]
    operator: ">="
  less_than:
    keywords: ["이하", "미만", "낮은", "작다"]
    operator: "<="
  between:
    keywords: ["사이", "범위"]
    operator: "BETWEEN"
```

### config/forbidden_patterns.yaml

금지 패턴 (정규식):

```yaml
patterns:
  - ".*특정 종목.*추천.*"
  - ".*매수.*타이밍.*"
  - ".*확실.*수익.*"
  - ".*보장.*"
```

---

## 테스트

### CLI 테스트

```bash
cd SL-ChatBot/chatbot
python src/main.py

# 인터랙티브 CLI 실행
You: PER이 뭐예요?
Bot: PER(주가수익비율)은...
```

### API 테스트 (curl)

```bash
# Health Check
curl http://localhost:8001/

# Chat Message
curl -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"PER이란?","session_id":"test_123"}'

# SSE Streaming
curl -N http://localhost:8001/api/v1/chat/stream?sessionId=test&message=PER이란?
```

---

## 배포

### 프로덕션 환경

**1. AWS Knowledge Base 설정**
- Bedrock Console → Knowledge Bases 생성
- S3 버킷 연결 (`rag/documents/` 업로드)
- 임베딩 모델 선택 (Titan Embeddings)
- Knowledge Base ID 확인

**2. 환경 변수**
```bash
AWS_KB_ID=your_kb_id  # Knowledge Base ID
RETRIEVER_TYPE=aws_kb # 명시적 설정
```

**3. Docker 배포**
```bash
docker build -t sl-chatbot-api -f api/Dockerfile .
docker run -p 8001:8001 --env-file .env sl-chatbot-api
```

### 로컬 개발 환경

```bash
# ChromaDB 사용
RETRIEVER_TYPE=chroma

# 임베딩 생성
cd rag
python scripts/build_embeddings.py

# API 서버 실행
cd ../api
python main.py
```

---

## 기술적 의사결정

### 왜 LangChain을 사용했나?

- **Tool Calling** - Agent가 필요한 기능을 자동 선택
- **Memory Management** - 대화 히스토리 자동 관리
- **Prompt Template** - 클라이언트별 프롬프트 체계적 관리
- **Retriever 추상화** - AWS KB/ChromaDB 전환 용이

### 왜 AWS Bedrock을 선택했나?

- **Claude Sonnet 4.5** - 한국어 성능 우수
- **관리형 서비스** - 인프라 관리 불필요
- **Knowledge Base** - S3 기반 자동 RAG 구축
- **보안** - AWS IAM 기반 인증/인가

### 환경별 RAG 전략

| 환경 | 벡터 DB | 이유 |
|-----|--------|------|
| **프로덕션** | AWS KB | 관리형, 자동 동기화, 확장성 |
| **로컬** | ChromaDB | 빠른 개발, 비용 절감, 오프라인 |

### SSE vs WebSocket

**SSE 선택 이유:**
- 단방향 스트리밍 (서버→클라이언트)만 필요
- EventSource API (브라우저 기본 지원)
- 간단한 HTTP 기반 (방화벽 친화적)
- Reconnection 자동 처리

---

## 성능 최적화

### Redis 캐싱

```bash
# .env
REDIS_HOST=localhost
REDIS_PORT=6379

# LangChain 자동 캐싱 활성화
# 동일 질문 재요청 시 LLM 호출 생략
```

### Conversation Memory

- **최대 10턴** 유지 (config.yaml)
- 오래된 대화는 자동 삭제
- 토큰 사용량 최적화

### Tool 실행 최적화

- 비동기 Tool 실행 (async/await)
- Backend API 타임아웃 설정 (30초)
- 실패 시 graceful degradation

---