"""FastAPI Application for Quant Advisor Chatbot."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add chatbot source to path. In Docker, the WORKDIR is /app, which corresponds to SL-ChatBot/api locally.
# The chatbot source is in ../chatbot/src relative to this file.
current_dir = Path(__file__).parent
chatbot_path = (current_dir.parent / "chatbot" / "src").resolve()
if chatbot_path.exists() and str(chatbot_path) not in sys.path:
    sys.path.insert(0, str(chatbot_path))
sys.path.insert(0, str(chatbot_path))

from routes import chat, recommend, dsl
from models.request import ChatRequest, RecommendRequest
from models.response import ChatResponse, RecommendResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("Quant Advisor API starting up...")
    yield
    print("Quant Advisor API shutting down...")


app = FastAPI(
    title="Quant Advisor API",
    description="AI-powered quant investment advisor",
    version="0.1.0",
    lifespan=lifespan
)

# CORS - Allow all origins for development (including file:// protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins is "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["recommend"])
app.include_router(dsl.router, prefix="/api/v1/dsl", tags=["dsl"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Quant Advisor API",
        "status": "healthy",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "api": "ok",
            "chatbot": "ok",
            "rag": "ok"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
