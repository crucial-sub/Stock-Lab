"""LLM Chat API Server - FastAPI 기반"""
import asyncio
import json
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, AsyncGenerator
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


async def generate_sse_stream(
    message: str,
    session_id: str
) -> AsyncGenerator[str, None]:
    """
    SSE 스트림 생성기

    기존 handler.handle() 응답을 토큰 단위로 분할하여 SSE 형식으로 전송합니다.

    Args:
        message: 사용자 메시지
        session_id: 세션 ID

    Yields:
        SSE 형식의 문자열 ("data: {json}\n\n")
    """
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    try:
        # stream_start 이벤트 전송
        yield f"data: {json.dumps({'type': 'stream_start', 'messageId': message_id}, ensure_ascii=False)}\n\n"

        # 전체 응답 생성 (기존 handler.handle 호출)
        result = await handler.handle(message=message, session_id=session_id)
        answer = result.get("answer", "")

        # 토큰 단위 분할 및 전송 (5-10 토큰씩 배칭)
        # 간단한 구현: 단어 단위로 분할 (공백 기준)
        words = answer.split()
        batch_size = 7  # 평균 배칭 크기

        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]
            chunk_content = " ".join(batch)

            # 마지막 청크가 아니면 공백 추가
            if i + batch_size < len(words):
                chunk_content += " "

            # stream_chunk 이벤트 전송
            chunk_event = {
                "type": "stream_chunk",
                "content": chunk_content,
                "format": "markdown"
            }
            yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"

            # 200ms 대기 (토큰 배칭 시뮬레이션)
            await asyncio.sleep(0.2)

        # ui_language가 있으면 전송
        if result.get("ui_language"):
            ui_language_event = {
                "type": "ui_language",
                "data": result["ui_language"]
            }
            yield f"data: {json.dumps(ui_language_event, ensure_ascii=False)}\n\n"

        # stream_end 이벤트 전송
        yield f"data: {json.dumps({'type': 'stream_end', 'messageId': message_id}, ensure_ascii=False)}\n\n"

    except Exception as e:
        # 에러 이벤트 전송
        error_str = str(e)

        # Throttling 에러 감지
        if "ThrottlingException" in error_str or "Too many requests" in error_str:
            error_message = "요청이 많아 일시적으로 응답이 지연되고 있습니다.\n잠시 후(30초~1분) 다시 시도해주세요."
            error_code = "THROTTLING"
        else:
            error_message = "응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            error_code = "INTERNAL_ERROR"

        error_event = {
            "type": "error",
            "code": error_code,
            "message": error_message
        }
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"


@app.get("/api/v1/chat/stream")
async def chat_stream(
    sessionId: str = Query(..., description="채팅 세션 ID"),
    message: str = Query(..., description="사용자 메시지")
):
    """
    SSE 기반 채팅 스트리밍 엔드포인트

    프론트엔드 EventSource API와 호환되는 SSE 프로토콜로 응답을 스트리밍합니다.

    Query Parameters:
        - sessionId: 채팅 세션 ID
        - message: 사용자 메시지

    Response:
        - Content-Type: text/event-stream
        - SSE 프로토콜 (data: {json}\n\n)

    Events:
        - stream_start: 스트리밍 시작
        - stream_chunk: 콘텐츠 청크 (마크다운 형식)
        - stream_end: 스트리밍 완료
        - ui_language: UI 언어 데이터 (선택)
        - error: 에러 발생
    """
    if handler is None:
        # 챗봇 초기화 실패 시 에러 이벤트 즉시 전송
        async def error_stream():
            error_event = {
                "type": "error",
                "code": "CHATBOT_NOT_INITIALIZED",
                "message": "챗봇을 초기화하지 못했습니다. 잠시 후 다시 시도해주세요."
            }
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
            }
        )

    # SSE 스트리밍 응답 반환
    return StreamingResponse(
        generate_sse_stream(message, sessionId),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
