"""
퀀트 전략 DSL 파서 유틸리티 (한국어 버전)
한국어/영어 자연어 → JSON 조건 DSL 변환
"""

import json
import logging
import os
import time
from typing import Any, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from pydantic import BaseModel

logger = logging.getLogger("quant-dsl-parser")
logging.basicConfig(level="INFO")

# ==============================
# AWS Bedrock 설정
# ==============================
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-northeast-2")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# ==============================
# Claude 시스템 프롬프트 (한국어)
# ==============================
CLAUDE_SYSTEM_PROMPT = """
당신은 퀀트 전략 DSL 파서입니다.

목표:
사용자가 한국어 또는 영어로 작성한 어떤 조건이라도
퀀트 백테스트 DSL JSON 형식으로 변환하세요.

출력 규칙:
- JSON만 출력
- 자연어 금지
- Markdown 금지
- 스키마 절대 변경 금지

DSL 스키마:
{
  "conditions": [
    {
      "factor": "STRING",
      "params": [NUMBER],
      "operator": "STRING",
      "right_factor": "STRING|null",
      "right_params": [NUMBER],
      "value": NUMBER|null
    }
  ]
}

사용 가능한 팩터 (화이트리스트):
PER, PBR, PSR, PCR, PEG,
ROE, ROA, EPS, EBITDA, OperatingProfitMargin, DebtRatio, DividendYield,
SMA, EMA, RSI, MACD,
MOMENTUM_3M, MOMENTUM_6M, MOMENTUM_12M,
VOLATILITY_20D, VOLATILITY_60D,
TURNOVER_RATE_20D, VOLUME_MA_20,
PRICE_CHANGE_1D, PRICE_CHANGE_5D

사용 가능한 연산자:
>, <, >=, <=, ==

예시:
입력: "PER 10 이하"
출력:
{
  "conditions": [
    {
      "factor": "PER",
      "params": [],
      "operator": "<=",
      "right_factor": null,
      "right_params": [],
      "value": 10
    }
  ]
}
"""

# ======================================
# Bedrock 클라이언트 지연 생성
# ======================================
_bedrock_client = None

def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _bedrock_client

# ======================================
# DSL 스키마 모델
# ======================================
class Condition(BaseModel):
    factor: str
    params: List[Any] = []
    operator: str
    right_factor: Optional[str] = None
    right_params: List[Any] = []
    value: Optional[float] = None

class StrategyResponse(BaseModel):
    conditions: List[Condition]

# ======================================
# JSON 추출 유틸
# ======================================
def sanitize_json(text: str) -> str:
    """Claude가 JSON 외의 것을 출력하면 중괄호 블록만 추출."""
    import re
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0)
    return "{}"

# ======================================
# Claude 호출
# ======================================
def call_claude_and_get_json(text: str) -> dict:
    """Bedrock 호출 + 간단한 재시도(Throttling 대비)."""
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0.2,
        "system": CLAUDE_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"다음 문장을 DSL JSON으로 변환하세요:\n{text}"
            }
        ],
    }

    client = get_bedrock_client()
    attempts = [1, 2, 4]  # seconds backoff
    for idx, wait in enumerate([0] + attempts):
        if wait:
            time.sleep(wait)
        try:
            response = client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )

            body = json.loads(response["body"].read())
            completion = body["content"][0]["text"]

            cleaned = sanitize_json(completion)
            parsed = json.loads(cleaned)

            return parsed
        except Exception as exc:
            logger.warning(
                "Claude DSL 변환 실패(시도 %s/%s) → %s",
                idx + 1,
                len(attempts) + 1,
                exc,
            )
            last_exc = exc
            # 다음 루프에서 재시도
    logger.warning("Claude DSL 변환 재시도 모두 실패 → fallback 사용. 사유: %s", last_exc)
    return {"conditions": []}

# ======================================
# 최종 파싱 인터페이스
# ======================================
def parse_strategy_text(text: str) -> StrategyResponse:
    claude_payload = call_claude_and_get_json(text)
    conditions = claude_payload.get("conditions", [])
    typed_conditions = [Condition(**c) for c in conditions]
    return StrategyResponse(conditions=typed_conditions)
