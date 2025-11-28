# Stock Lab AI Chatbot 명세서

## 목차
1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [API 엔드포인트](#api-엔드포인트)
4. [프롬프트 시스템](#프롬프트-시스템)
5. [DSL 생성](#dsl-생성)
6. [세션 관리](#세션-관리)
7. [배포 가이드](#배포-가이드)

---

## 개요

### 프로젝트 목적
Stock Lab AI Chatbot은 **AWS Bedrock Claude 기반 대화형 투자 어시스턴트**로, 사용자의 투자 성향을 파악하고 맞춤형 퀀트 전략을 추천합니다.

### 핵심 기능
1. **투자 상담**: 자연어 기반 투자 성향 분석
2. **전략 추천**: 피터 린치, 워렌 버핏 등 유명 전략 템플릿 제공
3. **조건 생성**: 자연어 → DSL 변환 (백테스트 조건 자동 생성)
4. **실시간 채팅**: SSE 기반 스트리밍 응답

### 기술 스택
- **LLM**: AWS Bedrock (Claude 3.5 Sonnet)
- **Framework**: LangChain 0.2, LangChain-AWS
- **API**: FastAPI, Uvicorn
- **Cache**: Redis (Session Management)

---

## 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│                    AI Assistant UI Component                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/SSE
┌──────────────────────────────────────────────────────────────────┐
│                     ChatBot API Server                           │
│                   FastAPI + LangChain                            │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ ChatHandler │  │ IntentRouter │  │ DSL Generator        │   │
│  │ (Main)      │  │ (Intent 분석)│  │ (NL → Conditions)    │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  AWS Bedrock     │ │    Redis     │ │  Main Backend    │
│  (Claude 3.5)    │ │  (Sessions)  │ │  (Backtest API)  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

---

## API 엔드포인트

### 1. 채팅 메시지 전송

```http
POST /api/v1/chat/message
Content-Type: application/json

{
  "message": "전략을 추천받고 싶어요",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": {
    "question_id": "investment_period",
    "option_id": "long_term"
  }
}
```

**응답 (200 OK)**
```json
{
  "answer": "장기 투자에 적합한 가치 투자 전략을 추천드립니다...",
  "intent": "strategy_recommendation",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ui_language": {
    "type": "strategy_list",
    "strategies": [
      {
        "name": "피터 린치 전략",
        "description": "PEG 레이쇼 기반 성장주 투자",
        "expected_return": "연 20-30%"
      }
    ]
  },
  "context": "long_term_value_investor",
  "sources": []
}
```

---

### 2. 스트리밍 채팅

```http
POST /api/v1/chat/stream
Content-Type: application/json
Accept: text/event-stream

{
  "message": "삼성전자에 대해 알려줘",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**SSE 응답 스트림**
```
event: message
data: {"type": "text", "content": "삼성전자는"}

event: message
data: {"type": "text", "content": " 대한민국 최대의"}

event: message
data: {"type": "text", "content": " 전자 기업입니다."}

event: done
data: {"session_id": "550e8400-e29b-41d4-a716-446655440000"}
```

---

### 3. 세션 삭제

```http
DELETE /api/v1/chat/session
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**응답 (200 OK)**
```json
{
  "status": "deleted",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. DSL 생성 (자연어 → 백테스트 조건)

```http
POST /api/v1/dsl/generate
Content-Type: application/json

{
  "text": "PER이 10 이하이고 ROE가 15% 이상인 종목"
}
```

**응답 (200 OK)**
```json
{
  "conditions": [
    {
      "factor": "per",
      "params": [],
      "operator": "LTE",
      "value": 10.0
    },
    {
      "factor": "roe",
      "params": [],
      "operator": "GTE",
      "value": 15.0
    }
  ]
}
```

---

### 5. 세션 목록 조회

```http
GET /api/v1/chat/sessions
```

**응답 (200 OK)**
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-15T10:30:00Z",
      "last_message": "전략을 추천받고 싶어요",
      "context": "long_term_value_investor"
    }
  ]
}
```

---

## 프롬프트 시스템

### 1. System Prompt 구조

Stock Lab Chatbot은 3가지 프롬프트 템플릿을 사용합니다:

#### A. AI Helper (전략 추천)
```
역할: 퀀트 투자 전략 상담 전문가
목적: 사용자 성향 파악 후 맞춤 전략 추천

질문 흐름:
1. 투자 목적 (장기/단기)
2. 위험 성향 (보수적/공격적)
3. 선호 투자 스타일 (가치/성장/모멘텀)
4. 관심 산업/섹터

출력 형식:
- type: "questionnaire" | "strategy_recommendation"
- strategies: [전략 목록]
- reasoning: 추천 이유
```

#### B. System Assistant (일반 대화)
```
역할: 퀀트 투자 교육 전문가
목적: 투자 개념, 팩터, 전략에 대한 설명

지원 주제:
- 팩터 설명 (PER, PBR, ROE 등)
- 백테스팅 개념
- 리스크 관리
- 종목 정보

출력 형식:
- type: "text"
- content: 설명 내용
```

#### C. Home Widget (홈 화면 요약)
```
역할: 시장 동향 요약 전문가
목적: 오늘의 시장, 인기 종목, 추천 전략 요약

출력 형식:
- type: "summary"
- market_status: 시장 동향
- hot_stocks: 인기 종목 3개
- recommended_strategy: 추천 전략
```

---

### 2. Intent 분류

ChatHandler는 사용자 메시지의 의도를 다음과 같이 분류합니다:

| Intent | 설명 | 예시 |
|--------|------|------|
| `greeting` | 인사 | "안녕하세요", "반가워요" |
| `strategy_recommendation` | 전략 추천 요청 | "전략 추천해줘", "어떤 전략이 좋을까?" |
| `factor_explanation` | 팩터 설명 요청 | "PER이 뭐야?", "ROE 알려줘" |
| `stock_inquiry` | 종목 문의 | "삼성전자 어때?", "카카오 분석해줘" |
| `backtest_request` | 백테스트 실행 | "이 전략으로 백테스트해줘" |
| `general_question` | 일반 질문 | "퀀트 투자가 뭐야?" |

---

## DSL 생성

### DSL (Domain-Specific Language) 개요

자연어 조건을 백테스트 API가 이해할 수 있는 구조화된 데이터로 변환합니다.

### 지원 팩터

**가치 팩터**
- `per`: 주가수익비율
- `pbr`: 주가순자산비율
- `psr`: 주가매출비율
- `ev_ebitda`: EV/EBITDA

**성장 팩터**
- `revenue_growth_1y`: 매출 성장률 (1년)
- `operating_profit_growth_1y`: 영업이익 성장률
- `eps_growth_1y`: EPS 성장률

**퀄리티 팩터**
- `roe`: 자기자본이익률
- `roa`: 총자산이익률
- `debt_ratio`: 부채비율

**모멘텀 팩터**
- `momentum_1m`: 1개월 모멘텀
- `momentum_3m`: 3개월 모멘텀
- `rsi_14`: 상대강도지수 (14일)

### 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `GT` | 초과 (>) | `per > 10` |
| `GTE` | 이상 (>=) | `roe >= 15` |
| `LT` | 미만 (<) | `pbr < 1.5` |
| `LTE` | 이하 (<=) | `debt_ratio <= 100` |
| `EQ` | 같음 (=) | `sector = IT` |

### 변환 예시

**입력 (자연어)**
```
PER이 10 이하이고 ROE가 15% 이상이며,
부채비율이 100% 미만인 종목을 찾아줘
```

**출력 (DSL)**
```json
{
  "conditions": [
    {
      "factor": "per",
      "operator": "LTE",
      "value": 10.0
    },
    {
      "factor": "roe",
      "operator": "GTE",
      "value": 15.0
    },
    {
      "factor": "debt_ratio",
      "operator": "LT",
      "value": 100.0
    }
  ],
  "logic": "AND"
}
```

---

## 세션 관리

### Redis 세션 구조

```python
# Key 형식
session:{session_id}

# Value (JSON)
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T10:30:00Z",
  "last_updated": "2025-01-15T10:35:00Z",
  "messages": [
    {
      "role": "user",
      "content": "전략을 추천받고 싶어요",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "투자 목적을 먼저 여쭤볼게요...",
      "timestamp": "2025-01-15T10:30:05Z"
    }
  ],
  "context": {
    "investment_period": "long_term",
    "risk_profile": "moderate",
    "style": "value"
  },
  "ttl": 3600
}
```

### 세션 TTL
- 기본 TTL: **1시간** (3600초)
- 메시지 전송 시 자동 갱신
- 만료 후 자동 삭제

---

## 배포 가이드

### 환경 변수 설정

```bash
# .env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
REDIS_URL=redis://localhost:6379/0

MAIN_BACKEND_URL=http://localhost:8000
```

### Docker 실행

```bash
# Build
docker build -t stocklab-chatbot:latest ./SL-ChatBot

# Run
docker run -d \
  --name stocklab-chatbot \
  -p 8001:8001 \
  --env-file .env \
  stocklab-chatbot:latest
```

### 로컬 개발

```bash
cd SL-ChatBot
pip install -r chatbot/requirements.txt

# API 서버 실행
cd chatbot/src
uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

### 헬스체크

```bash
curl http://localhost:8001/
# {"status":"running","version":"1.0.0"}
```

---

## 프롬프트 커스터마이징

### 프롬프트 파일 위치

```
SL-ChatBot/prompts/
├── system_ai_helper.txt      # 전략 추천 프롬프트
├── system_assistant.txt       # 일반 대화 프롬프트
├── system_home_widget.txt     # 홈 위젯 프롬프트
└── strategies.json            # 전략 템플릿
```

### 전략 템플릿 추가

```json
{
  "strategies": [
    {
      "name": "워렌 버핏 전략",
      "description": "장기 가치 투자 전략",
      "conditions": [
        {"factor": "roe", "operator": "GTE", "value": 15.0},
        {"factor": "debt_ratio", "operator": "LT", "value": 50.0}
      ],
      "expected_return": "연 15-20%",
      "risk_level": "moderate"
    }
  ]
}
```

---

## 성능 최적화

### 1. Redis 캐싱
- 세션 데이터 메모리 캐싱
- TTL 기반 자동 정리
- 응답 속도: < 100ms

### 2. AWS Bedrock 최적화
- 스트리밍 응답 (SSE)
- Temperature: 0.7 (적절한 창의성)
- Max Tokens: 2000

### 3. 비용 최적화
- 프롬프트 길이 최소화
- 컨텍스트 윈도우 관리 (최근 10개 메시지)
- Claude 3.5 Sonnet 사용 (Haiku 대비 성능 우수)

---

## 모니터링

### 로깅
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger.info(f"Chat message received: session={session_id}, intent={intent}")
```

### 메트릭
- 요청 수 (RPM)
- 평균 응답 시간
- 세션 수
- Bedrock API 호출 수

---

## 트러블슈팅

### 1. AWS Bedrock 연결 실패
```bash
# IAM 권한 확인
aws sts get-caller-identity

# Bedrock 모델 접근 권한 확인
aws bedrock list-foundation-models --region us-east-1
```

### 2. Redis 연결 실패
```bash
# Redis 상태 확인
redis-cli ping
# PONG

# 세션 확인
redis-cli keys "session:*"
```

### 3. 응답 속도 느림
- 프롬프트 길이 확인 (> 1000 tokens)
- 컨텍스트 윈도우 줄이기 (10개 → 5개)
- Temperature 낮추기 (0.7 → 0.5)

---

## 부록

### A. 지원 언어
- 한국어 (기본)
- 영어 (부분 지원)

### B. 제약사항
- 컨텍스트 윈도우: 최근 10개 메시지
- 세션 TTL: 1시간
- 동시 요청: 100 req/sec

### C. 향후 개선 사항
- [ ] RAG 파이프라인 (재무제표 기반 분석)
- [ ] 멀티모달 지원 (차트 이미지 분석)
- [ ] 실시간 시장 데이터 연동
- [ ] 음성 인터페이스 (STT/TTS)

---

**최종 수정일**: 2025-01-15
**작성자**: AI Team - 김은비
