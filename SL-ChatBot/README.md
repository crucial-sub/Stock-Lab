# Quant Advisor

AI-powered investment advisor chatbot for quantitative trading strategies.

## Overview

Quant Advisor는 사용자 맞춤형 퀀트 투자 전략을 추천하고, Stock-Lab-Demo 백테스트 시스템과 연동하여 전략 검증을 도와주는 AI 챗봇입니다.

## Features

- 📊 **팩터 기반 전략 추천**: 가치, 성장, 퀄리티, 모멘텀, 배당 전략
- 🤖 **AI 대화형 인터페이스**: 자연어로 전략 상담
- 📚 **RAG 지식 베이스**: 투자 팩터, 전략, 업종별 가이드
- 🔧 **MCP 도구 통합**: 조건식 자동 생성
- 🔗 **백테스트 연동**: Stock-Lab-Demo API 직접 연동

## Architecture

```
quant-advisor/
├── mcp-server/        # MCP 서버 (도구 제공)
├── rag/               # RAG 지식 베이스
├── chatbot/           # 챗봇 로직
└── api/               # FastAPI 백엔드
```

## Quick Start

### 1. 환경 설정

```bash
cp .env.example .env
```

### 2. 의존성 설치

```bash
# MCP Server
cd mcp-server
pip install -r requirements.txt

# RAG
cd ../rag
pip install -r requirements.txt
python scripts/build_embeddings.py  # 벡터 DB 생성

# Chatbot
cd ../chatbot
pip install -r requirements.txt

# API
cd ../api
pip install -r requirements.txt
```

### 3. API 서버 실행

```bash
cd api
python main.py
```

서버가 http://localhost:8001 에서 실행됩니다.

### 4. API 테스트

```bash
# Health Check
curl http://localhost:8001/health

# Chat
curl -X POST http://localhost:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "가치주 투자 전략 추천해줘"}'

# Strategy Recommendation
curl -X POST http://localhost:8001/api/v1/recommend/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "risk_tolerance": "medium",
    "investment_horizon": "long",
    "preferred_style": "value"
  }'
```

## API Endpoints

### Chat

**POST** `/api/v1/chat/message`

```json
{
  "message": "안정적인 배당 투자 전략 추천해줘",
  "session_id": "optional_session_id"
}
```

**Response:**
```json
{
  "answer": "안정적인 배당 투자 전략을 추천드립니다...",
  "intent": "recommend",
  "conditions": {...}
}
```

### Recommend Strategy

**POST** `/api/v1/recommend/strategy`

```json
{
  "risk_tolerance": "low",
  "investment_horizon": "long",
  "preferred_style": "dividend"
}
```

**Response:**
```json
{
  "strategy": "dividend",
  "description": "안정적 배당 수익",
  "primary_factors": ["배당수익률", "배당성향"],
  "secondary_factors": ["ROE", "부채비율"],
  "sample_conditions": [...]
}
```

### Build Conditions

**POST** `/api/v1/recommend/conditions`

```json
{
  "buy_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
  ]
}
```

**Response:**
```json
{
  "backtest_request": {
    "buy_conditions": [...],
    "sell_conditions": [],
    "start_date": "2024-01-01",
    ...
  }
}
```

## Components

### 1. MCP Server

팩터 추천 및 조건식 생성 도구를 제공하는 MCP 서버.

**Tools:**
- `recommend_factors`: 전략별 팩터 조합 추천
- `build_conditions`: Stock-Lab-Demo 조건식 생성

**Resources:**
- `factor_definitions`: 팩터 메타데이터

### 2. RAG Knowledge Base

투자 팩터, 전략, 업종별 가이드 문서.

**Documents:**
- `factors/`: 팩터 설명 (value, growth, quality, momentum, risk)
- `strategies/`: 전략 가이드
- `sectors/`: 업종별 가이드

### 3. Chatbot

대화형 AI 로직 구현.

**Features:**
- 의도 분류 (Explain, Recommend, Build)
- RAG 컨텍스트 검색
- MCP 도구 호출
- LLM 응답 생성

### 4. API

FastAPI 기반 REST API.

**Routes:**
- `/api/v1/chat/*`: 채팅 엔드포인트
- `/api/v1/recommend/*`: 추천 엔드포인트

## Integration with Stock-Lab-Demo

Quant Advisor는 Stock-Lab-Demo 백테스트 시스템과 연동됩니다.

```
User → Quant Advisor API → Stock-Lab-Demo API → Backtest Result
       (Generate Conditions)  (Run Backtest)
```

**Flow:**
1. 사용자가 전략 요청
2. Quant Advisor가 조건식 생성
3. Stock-Lab-Demo API로 백테스트 요청
4. 결과 반환

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
black .
ruff check .
```

### Building Embeddings

```bash
cd rag
python scripts/build_embeddings.py
```

## Docker Deployment

```bash
docker-compose up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STOCK_LAB_API_URL` | Stock-Lab API URL | `http://localhost:8000` |
| `API_PORT` | API server port | `8001` |
| `ENVIRONMENT` | Environment (dev/prod) | `development` |

## Roadmap

- [ ] RAG 검색 구현
- [ ] MCP 클라이언트 통합
- [ ] 스트리밍 응답
- [ ] 대화 히스토리 DB 저장
- [ ] 사용자 프로필 관리
- [ ] 전략 성과 추적
- [ ] 다국어 지원

## License

Proprietary

## Contact

For questions or issues, please contact the development team.
