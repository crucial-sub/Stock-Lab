"""응답 모델"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class UILanguageBase(BaseModel):
    type: str = Field(..., description="UI language type")


class QuestionnaireUI(UILanguageBase):
    type: str = Field("questionnaire_progress", const=True)
    total_questions: int
    current_question: int
    progress_percentage: Optional[int] = None
    question: Dict[str, Any]


class StrategyRecommendationUI(UILanguageBase):
    type: str = Field("strategy_recommendation", const=True)
    recommendations: List[Dict[str, Any]]
    user_profile_summary: Dict[str, Any]


class BacktestConfigurationUI(UILanguageBase):
    type: str = Field("backtest_configuration", const=True)
    strategy: Dict[str, Any]
    configuration_fields: List[Dict[str, Any]]


class ChatResponse(BaseModel):
    """채팅 응답"""
    answer: str = Field(..., description="Bot response")
    intent: Optional[str] = Field(None, description="Detected intent")
    context: Optional[str] = Field(None, description="Retrieved context")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Generated conditions if applicable")
    session_id: Optional[str] = Field(None, description="Session ID")
    ui_language: Optional[Dict[str, Any]] = Field(
        None,
        description="UI Language JSON payload for frontend rendering (questionnaire_progress | strategy_recommendation | backtest_configuration)",
    )
    backtest_conditions: Optional[Dict[str, Any]] = Field(None, description="DSL conditions for backtesting (buy/sell)")


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
