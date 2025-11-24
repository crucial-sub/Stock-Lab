"""Chat API Endpoints."""
import json
import sys
import asyncio
import uuid
from pathlib import Path
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

# Add chatbot to path (when running in Docker, chatbot is at /app/sl-chatbot/chatbot/src)
chatbot_path = Path("/app/sl-chatbot/chatbot/src")
if not chatbot_path.exists():
    # Fallback for local development
    chatbot_path = Path(__file__).parent.parent.parent / "chatbot" / "src"
sys.path.insert(0, str(chatbot_path))

try:
    # Import with full module path to avoid conflict with api/main.py
    import importlib.util
    main_file = chatbot_path / "main.py"
    if not main_file.exists():
        raise FileNotFoundError(f"main.py not found at {main_file}")
    spec = importlib.util.spec_from_file_location("chatbot_main", str(main_file))
    chatbot_main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chatbot_main)
    QuantAdvisorBot = chatbot_main.QuantAdvisorBot
except Exception as e:
    print(f"Failed to import QuantAdvisorBot: {e}")
    import traceback
    traceback.print_exc()
    QuantAdvisorBot = None

from models.request import ChatRequest
from models.response import ChatResponse
from ..errors import make_error_response


router = APIRouter()

# Global bot instance
bot = None


def get_bot():
    """Get or create bot instance."""
    global bot
    if bot is None and QuantAdvisorBot:
        # Docker path or local development path
        config_path = Path("/app/sl-chatbot/chatbot/config.yaml")
        if not config_path.exists():
            config_path = Path(__file__).parent.parent.parent / "chatbot" / "config.yaml"
        bot = QuantAdvisorBot(str(config_path))
    return bot


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """Process chat message.

    Args:
        request: Chat request with message and optional session_id

    Returns:
        ChatResponse with answer and metadata
    """
    chatbot = get_bot()

    if not chatbot:
        return make_error_response(
            status_code=500,
            code="E002",
            message="Chatbot not initialized",
            user_message="챗봇을 초기화하지 못했습니다. 잠시 후 다시 시도해주세요.",
            error_type="INVALID_RESPONSE",
            retry_allowed=True,
        )

    try:
        result = await chatbot.chat(
            message=request.message,
            session_id=request.session_id,
            answer=request.answer,
            client_type=request.client_type or "assistant"
        )

        print(f"DEBUG CHAT: User message: {request.message}")
        print(f"DEBUG CHAT: Bot answer: {result.get('answer', 'N/A')[:200]}")
        print(f"DEBUG CHAT: Intent: {result.get('intent', 'N/A')}")
        print(f"DEBUG CHAT: Sources count: {len(result.get('sources', []))}")

        return ChatResponse(
            answer=result["answer"],
            intent=result.get("intent"),
            context=result.get("context"),
            conditions=result.get("conditions"),
            session_id=result.get("session_id") or request.session_id,
            ui_language=result.get("ui_language"),
            backtest_conditions=result.get("backtest_conditions")
        )

    except Exception as e:
        error_str = str(e)

        # Throttling 에러 감지
        if "ThrottlingException" in error_str or "Too many requests" in error_str:
            user_message = "요청이 많아 일시적으로 응답이 지연되고 있습니다.\n잠시 후(30초~1분) 다시 시도해주세요."
        else:
            user_message = "응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."

        # 에러를 ChatResponse 형식으로 반환 (HTTPException 대신)
        return ChatResponse(
            answer=user_message,
            intent="error",
            context=None,
            conditions=None,
            session_id=request.session_id or "error",
            ui_language=None,
            backtest_conditions=None
        )


async def generate_sse_stream(
    message: str,
    session_id: str,
    chatbot,
    client_type: str = "assistant"
) -> AsyncGenerator[str, None]:
    """
    SSE 스트림 생성기

    기존 chatbot.chat() 응답을 토큰 단위로 분할하여 SSE 형식으로 전송합니다.

    Args:
        message: 사용자 메시지
        session_id: 세션 ID
        chatbot: QuantAdvisorBot 인스턴스

    Yields:
        SSE 형식의 문자열 ("data: {json}\n\n")
    """
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    try:
        # stream_start 이벤트 전송
        yield f"data: {json.dumps({'type': 'stream_start', 'messageId': message_id}, ensure_ascii=False)}\n\n"

        # 전체 응답 생성 (기존 chatbot.chat 호출)
        result = await chatbot.chat(
            message=message,
            session_id=session_id,
            client_type=client_type
        )
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


@router.get("/stream")
async def chat_stream(
    sessionId: str = Query(..., description="채팅 세션 ID"),
    message: str = Query(..., description="사용자 메시지"),
    clientType: str = Query("assistant", description="클라이언트 유형 (assistant, ai_helper, home_widget)")
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
    chatbot = get_bot()

    if not chatbot:
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
        generate_sse_stream(message, sessionId, chatbot, clientType),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
        }
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete chat session history."""
    chatbot = get_bot()

    if not chatbot:
        raise HTTPException(
            status_code=500,
            detail="Chatbot not initialized"
        )

    # Clear session history
    if hasattr(chatbot.handler, "delete_session_history"):
        chatbot.handler.delete_session_history(session_id)

    return {"message": "Session deleted", "session_id": session_id}
