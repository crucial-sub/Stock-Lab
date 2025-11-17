"""응답 모델"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatResponse(BaseModel):
    """채팅 응답"""
    answer: str = Field(..., description="Bot response")
    intent: Optional[str] = Field(None, description="Detected intent")
    context: Optional[str] = Field(None, description="Retrieved context")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Generated conditions if applicable")
    session_id: Optional[str] = Field(None, description="Session ID")
    ui_language: Optional[Dict[str, Any]] = Field(None, description="UI Language JSON payload for frontend rendering")
    backtest_conditions: Optional[List[Dict[str, Any]]] = Field(None, description="DSL conditions for backtesting")


class RecommendResponse(BaseModel):
    """전략 추천 응답"""
    strategy: str = Field(..., description="Recommended strategy type")
    description: str = Field(..., description="Strategy description")
    primary_factors: List[str] = Field(..., description="Primary factors")
    secondary_factors: List[str] = Field(..., description="Secondary factors")
    sample_conditions: List[Dict[str, Any]] = Field(..., description="Sample conditions")


class ConditionsResponse(BaseModel):
    """빌드 상태 응답"""
    backtest_request: Dict[str, Any] = Field(..., description="Complete backtest request for Stock-Lab-Demo")
