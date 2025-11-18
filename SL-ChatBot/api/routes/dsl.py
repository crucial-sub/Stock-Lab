"""DSL parsing API routes."""
import sys
from pathlib import Path
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel
from errors import make_error_response

# Add chatbot source to path
chatbot_path = Path(__file__).parent.parent / "chatbot" / "src"
if chatbot_path.exists():
    sys.path.insert(0, str(chatbot_path))

router = APIRouter()


class DSLRequest(BaseModel):
    text: str


class ConditionSchema(BaseModel):
    factor: str
    params: List = []
    operator: str
    right_factor: str | None = None
    right_params: List = []
    value: float | None = None


class DSLResponse(BaseModel):
    conditions: List[ConditionSchema]


@router.post("/parse", response_model=DSLResponse)
async def parse_strategy(req: DSLRequest):
    try:
        from schemas.dsl_generator import parse_strategy_text
    except Exception as e:
        return make_error_response(
            status_code=500,
            code="E002",
            message=f"DSL parser not initialized: {e}",
            user_message="DSL 파서를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.",
            error_type="INVALID_RESPONSE",
            retry_allowed=True,
        )

    try:
        result = parse_strategy_text(req.text)
        # dict 형태로 변환 후 스키마에 매핑 (Pydantic v1 호환)
        conditions = [ConditionSchema(**cond.dict()) for cond in result.conditions]
        return DSLResponse(conditions=conditions)
    except Exception as e:
        return make_error_response(
            status_code=500,
            code="E002",
            message=f"DSL parsing failed: {e}",
            user_message="DSL 변환에 실패했습니다. 입력을 수정하거나 잠시 후 다시 시도해주세요.",
            error_type="INVALID_RESPONSE",
            retry_allowed=True,
        )
