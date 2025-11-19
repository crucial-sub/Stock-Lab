"""Request Models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ChatRequest(BaseModel):
    """Chat message request."""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation history")
    answer: Optional[dict] = Field(None, description="Questionnaire answer {question_id, option_id}")
    client_type: Optional[Literal["assistant", "ai_helper"]] = Field(
        "assistant",
        description="Client context (assistant UI or AI helper UI)"
    )


class RecommendRequest(BaseModel):
    """Strategy recommendation request."""
    risk_tolerance: Literal["low", "medium", "high"] = Field(..., description="Risk tolerance level")
    investment_horizon: Literal["short", "medium", "long"] = Field(..., description="Investment time horizon")
    preferred_style: Optional[Literal["value", "growth", "quality", "momentum", "dividend", "multi_factor"]] = Field(
        None,
        description="Preferred investment style"
    )


class ConditionDict(BaseModel):
    """Single condition."""
    factor: str = Field(..., description="Factor name")
    operator: Literal["<", ">", "<=", ">=", "=="] = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")


class BuildConditionsRequest(BaseModel):
    """Build conditions request."""
    buy_conditions: List[ConditionDict] = Field(..., description="Buy conditions")
    sell_conditions: Optional[List[ConditionDict]] = Field(None, description="Sell conditions")
    start_date: Optional[str] = Field("2024-01-01", description="Backtest start date")
    end_date: Optional[str] = Field("2024-12-31", description="Backtest end date")
    initial_capital: Optional[int] = Field(100_000_000, description="Initial capital in KRW")
    rebalance_frequency: Optional[Literal["DAILY", "WEEKLY", "MONTHLY"]] = Field("MONTHLY", description="Rebalancing frequency")
    max_positions: Optional[int] = Field(20, description="Maximum number of positions")
