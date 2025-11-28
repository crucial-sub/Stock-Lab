# API 명세서

> SL-ChatBot AI 퀀트 투자 상담 챗봇 REST API

**Base URL:** `http://localhost:8001`

---

## 헬스체크

### `GET /`

서버 상태 확인

```json
{
  "service": "Quant Advisor API",
  "status": "healthy",
  "version": "0.1.0"
}
```

### `GET /health`

컴포넌트별 상태 확인

```json
{
  "status": "healthy",
  "components": {
    "api": "ok",
    "chatbot": "ok",
    "rag": "ok"
  }
}
```

---

## Chat API

### `POST /api/v1/chat/message`

채팅 메시지 전송 (JSON 응답)

**Request:**
```json
{
  "message": "PER이 뭐예요?",
  "session_id": "user_123",
  "client_type": "assistant"
}
```

**Parameters:**
- `message` (string): 사용자 메시지
- `session_id` (string, optional): 세션 ID
- `client_type` (string, optional): `assistant` | `ai_helper` | `home_widget`
- `answer` (object, optional): 설문 응답 `{question_id, option_id}`

**Response:**
```json
{
  "answer": "PER(주가수익비율)은...",
  "intent": "factor_explanation",
  "context": null,
  "conditions": null,
  "session_id": "user_123",
  "ui_language": null,
  "backtest_conditions": null
}
```

**Response Fields:**
- `answer` (string): 챗봇 응답
- `intent` (string): 감지된 의도
- `context` (string): RAG 컨텍스트
- `conditions` (object): 생성된 조건
- `session_id` (string): 세션 ID
- `ui_language` (object): UI 렌더링 데이터
- `backtest_conditions` (object): 백테스트 DSL 조건

**Error Response:**
```json
{
  "answer": "응답 생성 중 오류가 발생했습니다.",
  "intent": "error",
  "session_id": "user_123"
}
```

---

### `GET /api/v1/chat/stream`

SSE 스트리밍 응답

**Query Parameters:**
- `sessionId` (string): 세션 ID
- `message` (string): 사용자 메시지
- `clientType` (string, optional): 클라이언트 타입

**Response Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**SSE Events:**

**stream_start** - 스트리밍 시작
```
data: {"type":"stream_start","messageId":"msg_abc123"}
```

**stream_chunk** - 콘텐츠 청크
```
data: {"type":"stream_chunk","content":"PER은 ","format":"markdown"}
```

**ui_language** - UI 데이터 (선택적)
```
data: {"type":"ui_language","data":{...}}
```

**stream_end** - 스트리밍 종료
```
data: {"type":"stream_end","messageId":"msg_abc123"}
```

**error** - 에러 발생
```
data: {"type":"error","code":"THROTTLING","message":"..."}
```

**Error Codes:**
- `CHATBOT_NOT_INITIALIZED` - 챗봇 초기화 실패
- `THROTTLING` - AWS Bedrock 요청 제한 초과
- `INTERNAL_ERROR` - 내부 서버 오류

---

### `DELETE /api/v1/chat/session/{session_id}`

세션 히스토리 삭제

**Path Parameters:**
- `session_id` (string): 삭제할 세션 ID

**Response:**
```json
{
  "message": "Session deleted",
  "session_id": "test_session_001"
}
```

---

## DSL API

### `POST /api/v1/dsl/parse`

자연어를 DSL 조건식으로 변환

**Request:**
```json
{
  "text": "PER 15 이하이고 ROE 10% 이상인 종목"
}
```

**Response:**
```json
{
  "conditions": [
    {
      "factor": "PER",
      "params": [],
      "operator": "<=",
      "right_factor": null,
      "right_params": [],
      "value": 15.0
    },
    {
      "factor": "ROE",
      "params": [],
      "operator": ">=",
      "right_factor": null,
      "right_params": [],
      "value": 10.0
    }
  ]
}
```

**Condition Object Fields:**
- `factor` (string): 팩터 이름
- `params` (array): 팩터 파라미터
- `operator` (string): 비교 연산자 (`<`, `>`, `<=`, `>=`, `==`)
- `right_factor` (string): 우측 팩터 (팩터 간 비교 시)
- `right_params` (array): 우측 팩터 파라미터
- `value` (number): 비교 값

**지원하는 자연어 패턴:**

| 표현 | 연산자 | 예시 |
|-----|--------|------|
| "이상", "초과", "넘는", "크다" | `>=` | "PER 15 이상" |
| "이하", "미만", "낮은", "작다" | `<=` | "PBR 1 이하" |
| "같다", "동일" | `==` | "부채비율 50" |
| "사이", "범위" | `BETWEEN` | "ROE 10에서 20 사이" |

**Error Response:**
```json
{
  "code": "E002",
  "message": "DSL parsing failed: ...",
  "user_message": "DSL 변환에 실패했습니다. 입력을 수정하거나 잠시 후 다시 시도해주세요.",
  "error_type": "INVALID_RESPONSE",
  "retry_allowed": true
}
```

---

## Recommend API

### `POST /api/v1/recommend/strategy`

투자 전략 추천

**Request:**
```json
{
  "risk_tolerance": "medium",
  "investment_horizon": "long",
  "preferred_style": "value"
}
```

**Parameters:**
- `risk_tolerance` (string): 위험 허용도 (`low` | `medium` | `high`)
- `investment_horizon` (string): 투자 기간 (`short` | `medium` | `long`)
- `preferred_style` (string, optional): 선호 스타일 (`value` | `growth` | `quality` | `momentum` | `dividend` | `multi_factor`)

**Response:**
```json
{
  "strategy": "value",
  "description": "저평가된 우량주를 발굴하는 가치투자 전략입니다.",
  "primary_factors": ["PER", "PBR", "PSR"],
  "secondary_factors": ["ROE", "부채비율", "영업이익률"],
  "sample_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "PBR", "operator": "<", "value": 1.5},
    {"factor": "ROE", "operator": ">", "value": 10}
  ]
}
```

**Response Fields:**
- `strategy` (string): 추천 전략 타입
- `description` (string): 전략 설명
- `primary_factors` (array): 핵심 팩터 리스트
- `secondary_factors` (array): 보조 팩터 리스트
- `sample_conditions` (array): 샘플 조건 리스트

**전략 매핑 규칙:**

| Risk Tolerance | Investment Horizon | Recommended Strategy |
|----------------|-------------------|---------------------|
| low | long / medium | dividend |
| low | short | quality |
| high | short | momentum |
| high | medium / long | growth |
| medium | long | quality |
| medium | short | momentum |
| medium | medium | multi_factor |

> `preferred_style`이 제공되면 위 규칙보다 우선 적용

**Error Response:**
```json
{
  "code": "E004",
  "message": "Recommendation failed: ...",
  "user_message": "전략 추천 중 오류가 발생했습니다. 다시 시도해주세요."
}
```

---

### `POST /api/v1/recommend/conditions`

백테스트 조건 생성

**Request:**
```json
{
  "buy_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
  ],
  "sell_conditions": [
    {"factor": "PER", "operator": ">", "value": 30}
  ],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000000,
  "rebalance_frequency": "MONTHLY",
  "max_positions": 20
}
```

**Parameters:**
- `buy_conditions` (array): 매수 조건 리스트
- `sell_conditions` (array, optional): 매도 조건 리스트
- `start_date` (string, optional): 백테스트 시작일 (기본: `2024-01-01`)
- `end_date` (string, optional): 백테스트 종료일 (기본: `2024-12-31`)
- `initial_capital` (integer, optional): 초기 자본(원) (기본: `100000000`)
- `rebalance_frequency` (string, optional): 리밸런싱 주기 (`DAILY` | `WEEKLY` | `MONTHLY`, 기본: `MONTHLY`)
- `max_positions` (integer, optional): 최대 보유 종목 수 (기본: `20`)

**Condition Object:**
- `factor` (string): 팩터 이름
- `operator` (string): 비교 연산자
- `value` (number): 비교 값

**Response:**
```json
{
  "backtest_request": {
    "buy_conditions": [
      {"factor": "PER", "operator": "<", "value": 15},
      {"factor": "ROE", "operator": ">", "value": 10}
    ],
    "sell_conditions": [
      {"factor": "PER", "operator": ">", "value": 30}
    ],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000000,
    "rebalance_frequency": "MONTHLY",
    "max_positions": 20
  }
}
```

**Error Response:**
```json
{
  "code": "E006",
  "message": "Condition building failed: ...",
  "user_message": "백테스트 조건 생성 중 오류가 발생했습니다. 다시 시도해주세요."
}
```

---

## 에러 코드

| Code | Description | Retry |
|------|-------------|-------|
| `E002` | 초기화 실패 / DSL 파싱 실패 | ✅ |
| `E004` | FactorSync 오류 | ✅ |
| `E006` | 조건 생성 실패 | ✅ |
| `CHATBOT_NOT_INITIALIZED` | 챗봇 미초기화 | ✅ |
| `THROTTLING` | AWS Bedrock 요청 제한 초과 | ✅ (30초~1분 후) |
| `INTERNAL_ERROR` | 내부 서버 오류 | ✅ |

### Throttling 처리

AWS Bedrock 요청 제한 초과 시:

```json
{
  "answer": "요청이 많아 일시적으로 응답이 지연되고 있습니다.\n잠시 후(30초~1분) 다시 시도해주세요.",
  "intent": "error"
}
```

**권장 재시도 전략:**
- 30초~1분 대기 후 재시도
- Exponential Backoff 구현
- 프론트엔드에서 요청 큐잉

---

## 클라이언트 타입

| Type | Description | Response Style |
|------|-------------|----------------|
| `assistant` | 메인 상담 챗봇 | 상세한 교육적 설명 |
| `ai_helper` | 백테스트 AI 헬퍼 | DSL 생성 중심, 간결한 설명 |
| `home_widget` | 홈 위젯 간편 상담 | 매우 간결한 답변 (2-3문장) |

---

## CORS 설정

```python
allow_origins = ["*"]
allow_credentials = False
allow_methods = ["*"]
allow_headers = ["*"]
```

모든 origin에서 접근 가능

---
