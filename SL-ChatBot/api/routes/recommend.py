"""Recommendation API Endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List
import sys
from pathlib import Path

# Add chatbot to path for FactorSync (when running in Docker, chatbot is at /app/sl-chatbot/chatbot/src)
chatbot_path = Path("/app/sl-chatbot/chatbot/src")
if not chatbot_path.exists():
    # Fallback for local development
    chatbot_path = Path(__file__).parent.parent.parent / "chatbot" / "src"
sys.path.insert(0, str(chatbot_path))

try:
    from factor_sync import FactorSync
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    FactorSync = None

from models.request import RecommendRequest, BuildConditionsRequest
from models.response import RecommendResponse, ConditionsResponse


router = APIRouter()

# Global FactorSync instance
factor_sync = None


def get_factor_sync():
    """Get or create FactorSync instance."""
    global factor_sync
    if factor_sync is None and FactorSync:
        factor_sync = FactorSync()
    return factor_sync


@router.post("/strategy", response_model=RecommendResponse)
async def recommend_strategy(request: RecommendRequest):
    """Recommend investment strategy.

    Args:
        request: User investment profile

    Returns:
        Recommended strategy with factors and conditions
    """
    sync = get_factor_sync()
    if not sync:
        raise HTTPException(
            status_code=500,
            detail="FactorSync not available"
        )

    try:
        # Map user profile to strategy
        strategy = _map_profile_to_strategy(request)

        # Get recommendations from Backend via FactorSync
        recommendation = await sync.build_strategy_recommendation(strategy)

        return RecommendResponse(
            strategy=recommendation["strategy"],
            description=recommendation["description"],
            primary_factors=recommendation["primary_factors"],
            secondary_factors=recommendation["secondary_factors"],
            sample_conditions=recommendation["sample_conditions"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {str(e)}"
        )


@router.post("/conditions", response_model=ConditionsResponse)
async def build_conditions(request: BuildConditionsRequest):
    """Build backtest conditions.

    Args:
        request: Factor conditions

    Returns:
        Formatted conditions for Stock-Lab-Demo
    """
    try:
        # Directly build the backtest request dictionary
        backtest_request = {
            "buy_conditions": request.buy_conditions,
            "sell_conditions": request.sell_conditions or [],
            "start_date": request.start_date or "2024-01-01",
            "end_date": request.end_date or "2024-12-31",
            "initial_capital": request.initial_capital or 100_000_000,
            "rebalance_frequency": request.rebalance_frequency or "MONTHLY",
            "max_positions": request.max_positions or 20
        }

        return ConditionsResponse(
            backtest_request=backtest_request
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Condition building failed: {str(e)}"
        )


def _map_profile_to_strategy(request: RecommendRequest) -> str:
    """Map user profile to strategy type."""
    # Priority: preferred_style > risk_tolerance + horizon

    if request.preferred_style:
        return request.preferred_style

    # Map based on risk and horizon
    if request.risk_tolerance == "low":
        if request.investment_horizon in ["long", "medium"]:
            return "dividend"
        else:
            return "quality"

    elif request.risk_tolerance == "high":
        if request.investment_horizon == "short":
            return "momentum"
        else:
            return "growth"

    else:  # medium
        if request.investment_horizon == "long":
            return "quality"
        elif request.investment_horizon == "short":
            return "momentum"
        else:
            return "multi_factor"
