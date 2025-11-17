"""Chat API Endpoints."""
import json
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

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
            answer=request.answer
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
            session_id=request.session_id,
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


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response (SSE)."""
    raise HTTPException(
        status_code=501,
        detail="Streaming not implemented"
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
    if session_id in chatbot.handler.conversation_history:
        del chatbot.handler.conversation_history[session_id]

    return {"message": "Session deleted", "session_id": session_id}
