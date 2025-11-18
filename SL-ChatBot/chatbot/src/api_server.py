"""LLM Chat API Server - FastAPI 기반"""
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn

from handlers.chat_handler import ChatHandler

# Pydantic 모델
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    answer: Optional[Dict[str, str]] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    session_id: str
    ui_language: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    sources: Optional[list] = None

    class Config:
        extra = "allow"  # Allow extra fields from handler response


class DeleteSessionRequest(BaseModel):
    session_id: str


# DSL 관련 모델
class DSLRequest(BaseModel):
    text: str


class ConditionSchema(BaseModel):
    factor: str
    params: List = []
    operator: str
    right_factor: Optional[str] = None
    right_params: List = []
    value: Optional[float] = None


class DSLResponse(BaseModel):
    conditions: List[ConditionSchema]


# FastAPI 앱 초기화
app = FastAPI(
    title="SL-ChatBot LLM API",
    description="Stock Lab 투자 자문 챗봇 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포시 ["http://localhost:3000"] 등으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 글로벌 ChatHandler 인스턴스
handler: Optional[ChatHandler] = None


@app.on_event("startup")
async def startup_event():
    """서버 시작시 ChatHandler 초기화"""
    global handler
    handler = ChatHandler()
    print("[Server] ChatHandler initialized")


@app.get("/")
async def root():
    """헬스 체크"""
    return {"status": "running", "version": "1.0.0"}


@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest) -> ChatResponse:
    """
    채팅 메시지 처리 엔드포인트

    ### Request
    ```json
    {
      "message": "전략을 추천받고 싶어요",
      "session_id": "uuid-here",
      "answer": {
        "question_id": "investment_period",
        "option_id": "long_term"
      }
    }
    ```

    ### Response
    ```json
    {
      "answer": "질문 1/5: ...",
      "intent": "questionnaire_progress",
      "session_id": "uuid-here",
      "ui_language": {
        "type": "questionnaire_start",
        "total_questions": 5,
        "current_question": 1,
        "question": {...}
      }
    }
    ```
    """
    if handler is None:
        raise HTTPException(status_code=500, detail="ChatHandler not initialized")

    try:
        response = await handler.handle(
            message=request.message,
            session_id=request.session_id,
            answer=request.answer
        )
        print(f"DEBUG API: Handler response keys: {list(response.keys())}")
        print(f"DEBUG API: Has ui_language: {'ui_language' in response}")
        return ChatResponse(**response)
    except Exception as e:
        print(f"ERROR API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/recommend/conditions")
async def recommend_conditions(request: Dict[str, Any]):
    """
    백테스트 조건 생성 엔드포인트

    ### Request
    ```json
    {
      "buy_conditions": [
        {"factor": "PEG", "operator": ">", "value": 0},
        {"factor": "PEG", "operator": "<", "value": 2}
      ],
      "sell_conditions": [],
      "start_date": "2024-01-01",
      "end_date": "2024-12-31",
      "initial_capital": 100000000,
      "rebalance_frequency": "MONTHLY",
      "max_positions": 20
    }
    ```
    """
    try:
        # 향후 백테스트 API 호출
        return {
            "status": "success",
            "message": "Backtest conditions received",
            "backtest_request": request
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/chat/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    if handler is None:
        raise HTTPException(status_code=500, detail="ChatHandler not initialized")

    try:
        # 세션 데이터 정리
        if session_id in handler.session_state:
            del handler.session_state[session_id]
        if session_id in handler.conversation_history:
            del handler.conversation_history[session_id]

        return {
            "message": "Session deleted",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """헬스 체크 (상세)"""
    return {
        "status": "healthy",
        "handler_initialized": handler is not None,
        "version": "1.0.0"
    }


@app.post("/api/v1/dsl/parse", response_model=DSLResponse)
async def parse_dsl(request: DSLRequest):
    """
    자연어 전략 설명을 DSL JSON으로 변환

    ### Request
    ```json
    {
      "text": "PER 10 이하이고 ROE 15% 이상"
    }
    ```

    ### Response
    ```json
    {
      "conditions": [
        {
          "factor": "PER",
          "params": [],
          "operator": "<=",
          "value": 10
        }
      ]
    }
    ```
    """
    try:
        from schemas.dsl_generator import parse_strategy_text

        result = parse_strategy_text(request.text)
        # Pydantic v1 호환: dict() 사용
        conditions = [ConditionSchema(**cond.dict()) for cond in result.conditions]
        return DSLResponse(conditions=conditions)
    except Exception as e:
        print(f"DSL 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"DSL 변환에 실패했습니다: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
