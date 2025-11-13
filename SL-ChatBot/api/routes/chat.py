"""Chat API Endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Optional
import sys
from pathlib import Path

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
        raise HTTPException(
            status_code=500,
            detail="Chatbot not initialized"
        )

    try:
        result = await chatbot.chat(
            message=request.message,
            session_id=request.session_id
        )

        return ChatResponse(
            answer=result["answer"],
            intent=result.get("intent"),
            context=result.get("context"),
            conditions=result.get("conditions"),
            session_id=request.session_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response (SSE).

    TODO: Implement streaming response
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming not implemented yet"
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
