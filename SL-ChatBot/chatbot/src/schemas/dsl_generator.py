"""Strategy DSL parser utilities.

Natural language → normalized conditions JSON for 백테스트/전략 구성에 사용.
FastAPI와 분리된 순수 로직만 포함합니다.
"""
import json
import logging
import os
from typing import Any, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

logger = logging.getLogger("quant-dsl-parser")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-northeast-2")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
CLAUDE_SYSTEM_PROMPT = (
    "You are a trading DSL parser. Convert natural language Korean/English strategy descriptions "
    "into JSON that matches the Condition schema. Always respond with valid JSON only."
)

_bedrock_client = None


def get_bedrock_client():
    """Lazily create a Bedrock client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _bedrock_client


class Condition(BaseModel):
    factor: str
    params: List[Any] = []
    operator: str
    right_factor: Optional[str] = None
    right_params: List[Any] = []
    value: Optional[float] = None


class StrategyRequest(BaseModel):
    text: str


class StrategyResponse(BaseModel):
    conditions: List[Condition]


def build_conditions_from_text(text: str) -> List[Condition]:
    """단순 휴리스틱으로 조건 생성 (Claude 호출 실패 시 폴백)."""
    conditions: List[Condition] = []

    normalized = text.lower()
    if "20 day" in normalized and "60 day" in normalized:
        conditions.append(
            Condition(
                factor="SMA",
                params=[20],
                operator=">",
                right_factor="SMA",
                right_params=[60],
                value=None,
            )
        )

    if "per" in normalized and ("below" in normalized or "<" in text or "under" in normalized):
        import re

        match = re.search(r"per[^\d]*(\d+)", text, re.IGNORECASE)
        per_val = float(match.group(1)) if match else 10.0
        conditions.append(
            Condition(
                factor="PER",
                params=[],
                operator="<",
                right_factor=None,
                right_params=[],
                value=per_val,
            )
        )

    return conditions


def _fallback_response(text: str) -> dict:
    return {"conditions": [condition.model_dump() for condition in build_conditions_from_text(text)]}


def normalize_conditions(raw_conditions: List[dict]) -> List[dict]:
    """조건 리스트를 일관된 키/타입으로 정규화."""
    normalized = []
    for condition in raw_conditions:
        if not isinstance(condition, dict):
            continue
        normalized.append(
            {
                "factor": condition.get("factor", ""),
                "params": condition.get("params") or [],
                "operator": condition.get("operator", ""),
                "right_factor": condition.get("right_factor"),
                "right_params": condition.get("right_params") or [],
                "value": condition.get("value"),
            }
        )
    return normalized


def call_claude_and_get_json(text: str) -> dict:
    """Bedrock Claude 호출로 자연어 → 조건 JSON 변환."""
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
        "temperature": 0.2,
        "system": CLAUDE_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Input trading strategy:\n"
                            f"{text}\n\n"
                            "Output JSON strictly in this schema:\n"
                            '{\n  "conditions": [\n    {\n      "factor": "SMA",\n'
                            '      "params": [20],\n      "operator": ">",\n'
                            '      "right_factor": "SMA",\n      "right_params": [60],\n'
                            '      "value": null\n    }\n  ]\n}\n'
                        ),
                    }
                ],
            }
        ],
    }

    try:
        client = get_bedrock_client()
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload),
        )
        body = json.loads(response["body"].read())
        completion = body["content"][0]["text"]
        parsed = json.loads(completion)
        if "conditions" not in parsed:
            raise ValueError("Claude response missing 'conditions'.")
        parsed["conditions"] = normalize_conditions(parsed.get("conditions", []))
        return parsed
    except (BotoCoreError, ClientError, NoCredentialsError, json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.warning("Falling back to heuristic parsing because Claude call failed: %s", exc)
        return _fallback_response(text)


def parse_strategy_text(text: str) -> StrategyResponse:
    """외부에서 사용할 파서 엔트리 포인트."""
    claude_payload = call_claude_and_get_json(text or "")
    normalized = normalize_conditions(claude_payload.get("conditions", []))
    return StrategyResponse(conditions=[Condition(**c) for c in normalized])
