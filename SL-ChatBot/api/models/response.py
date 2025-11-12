"""Response Models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatResponse(BaseModel):
    """Chat response."""
    answer: str = Field(..., description="Bot response")
    intent: Optional[str] = Field(None, description="Detected intent")
    context: Optional[str] = Field(None, description="Retrieved context")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Generated conditions if applicable")
    session_id: Optional[str] = Field(None, description="Session ID")


class RecommendResponse(BaseModel):
    """Strategy recommendation response."""
    strategy: str = Field(..., description="Recommended strategy type")
    description: str = Field(..., description="Strategy description")
    primary_factors: List[str] = Field(..., description="Primary factors")
    secondary_factors: List[str] = Field(..., description="Secondary factors")
    sample_conditions: List[Dict[str, Any]] = Field(..., description="Sample conditions")


class ConditionsResponse(BaseModel):
    """Conditions build response."""
    backtest_request: Dict[str, Any] = Field(..., description="Complete backtest request for Stock-Lab-Demo")
