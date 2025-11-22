"""
퀀트 전략 DSL 파서 유틸리티 
한국어/영어 자연어 → JSON 조건 DSL 변환
"""

import json
import logging
import os
import re
import time
from typing import Any, List, Optional, Dict
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from pydantic import BaseModel

logger = logging.getLogger("quant-dsl-parser")
logging.basicConfig(level="INFO")

# ==============================
# AWS Bedrock 설정
# ==============================
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-northeast-2")
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
)
BEDROCK_INFERENCE_PROFILE_ID = (
    os.getenv("BEDROCK_INFERENCE_PROFILE_ID")
    or os.getenv("BEDROCK_INFERENCE_PROFILE_ARN")
    or "arn:aws:bedrock:ap-northeast-2:749559064959:inference-profile/global.anthropic.claude-sonnet-4-5-20250929-v1:0"
)

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

사용 가능한 팩터:
- 기본 재무/기술/모멘텀 팩터: PER, PBR, PSR, PCR, PEG, ROE, ROA, EPS, EBITDA, OperatingProfitMargin, DebtRatio, DividendYield,
  SMA, EMA, RSI, MACD, MOMENTUM_3M/6M/12M, VOLATILITY_20D/60D, TURNOVER_RATE_20D, VOLUME_MA_20
- 수익률/가격 변화 팩터: RET_[N]D (N일 수익률), PRICE_CHANGE_[N]D (N일 가격 변화)
  - N은 1, 3, 5, 7, 10, 20, 60 등 어떤 숫자도 가능
  - 예: RET_3D, RET_10D, PRICE_CHANGE_7D
- 그 외 입력된 팩터명도 그대로 허용 (화이트리스트에 없어도 반환)

사용 가능한 연산자:
>, <, >=, <=, ==

중요 규칙:
- "N일동안 X% 오르면" → RET_[N]D >= X (X는 소수, 예: 0.05 = 5%, 0.10 = 10%)
- "N일 전 대비 X% 상승" → RET_[N]D >= X (동일)
- 퍼센트는 항상 소수로 변환 (5% → 0.05, 10% → 0.10)

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

입력: "3일동안 8% 이상 오르면 매수"
출력:
{
  "conditions": [
    {
      "factor": "RET_3D",
      "params": [],
      "operator": ">=",
      "right_factor": null,
      "right_params": [],
      "value": 0.08
    }
  ]
}

입력: "10일동안 10% 이상 오르면 매수"
출력:
{
  "conditions": [
    {
      "factor": "RET_10D",
      "params": [],
      "operator": ">=",
      "right_factor": null,
      "right_params": [],
      "value": 0.10
    }
  ]
}
"""

# ======================================
# Bedrock 클라이언트 지연 생성
# ======================================
_bedrock_client = None
_factor_alias_map: Dict[str, str] = {}
_operator_map: Dict[str, str] = {}
_known_factors: set[str] = set()

def get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    return _bedrock_client


def _normalize_factor_key(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def _load_alias_and_operator_maps():
    """Load factor alias and operator map from config files (with safe fallback)."""
    global _factor_alias_map, _operator_map
    # factor alias
    factor_path = Path("/app/config/factor_alias.json")
    if not factor_path.exists():
        factor_path = Path(__file__).parent.parent.parent / "config" / "factor_alias.json"
    try:
        if factor_path.exists():
            _factor_alias_map = json.loads(factor_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("factor_alias.json 로드 실패: %s", exc)
    # operator map
    op_path = Path("/app/config/operator_rules.yaml")
    if not op_path.exists():
        op_path = Path(__file__).parent.parent.parent / "config" / "operator_rules.yaml"
    try:
        if op_path.exists():
            import yaml  # local import to avoid hard dependency elsewhere
            data = yaml.safe_load(op_path.read_text(encoding="utf-8")) or {}
            _operator_map = data.get("operator_map", {})
    except Exception as exc:
        logger.warning("operator_rules.yaml 로드 실패: %s", exc)


def _load_known_factors():
    """Load known factor identifiers from metadata."""
    global _known_factors
    if _known_factors:
        return

    meta_path = Path("/app/rag/documents/factors/metadata.json")
    if not meta_path.exists():
        meta_path = Path(__file__).parent.parent.parent / "rag" / "documents" / "factors" / "metadata.json"

    if meta_path.exists():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            docs = data.get("documents", [])
            for doc in docs:
                for token in (
                    [doc.get("id")]
                    + (doc.get("subcategories") or [])
                    + (doc.get("keywords") or [])
                ):
                    if isinstance(token, str) and token.strip():
                        _known_factors.add(_normalize_factor_key(token))
        except Exception as exc:
            logger.warning("팩터 메타데이터 로드 실패: %s", exc)

    # alias에서 사용하는 정식 팩터명도 추가
    for target in _factor_alias_map.values():
        if isinstance(target, str):
            _known_factors.add(_normalize_factor_key(target))

    # 기본 제공 팩터 (메타데이터 누락 대비)
    defaults = [
        "PER", "PBR", "PEG", "ROE", "ROA", "EPS",
        "PRICE_CHANGE_1D", "PRICE_CHANGE_5D",
        "RET_1D", "RET_5D",
    ]
    for token in defaults:
        _known_factors.add(_normalize_factor_key(token))

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


def _normalize_condition(cond: Dict[str, Any]) -> Dict[str, Any]:
    """factor/operator 정규화."""
    if not _factor_alias_map and not _operator_map:
        _load_alias_and_operator_maps()
    if not _known_factors:
        _load_known_factors()

    factor = cond.get("factor")
    if isinstance(factor, str):
        key = factor.lower().strip()
        cond["factor"] = _factor_alias_map.get(key, factor)

    op = cond.get("operator")
    if isinstance(op, str):
        key = op.lower().strip()
        cond["operator"] = _operator_map.get(op) or _operator_map.get(key) or op

    normalized_factor_key = None
    if isinstance(cond.get("factor"), str):
        normalized_factor_key = _normalize_factor_key(cond["factor"])
        factor_upper = cond["factor"].upper()

        # RET_[N]D 또는 PRICE_CHANGE_[N]D 패턴은 자동 허용
        is_dynamic_factor = (
            re.match(r"^RET_\d+D$", factor_upper) or
            re.match(r"^PRICE_CHANGE_\d+D$", factor_upper)
        )

        if _known_factors and not is_dynamic_factor and normalized_factor_key not in _known_factors:
            raise ValueError(f"unknown_factor:{cond.get('factor')}")

    # between 처리: Claude가 value를 리스트로 주는 경우 대비
    if cond.get("operator") == "between" and isinstance(cond.get("value"), list) and len(cond["value"]) == 2:
        low, high = cond["value"]
        return [
            {**{k: v for k, v in cond.items() if k != "value"}, "operator": ">", "value": low},
            {**{k: v for k, v in cond.items() if k != "value"}, "operator": "<", "value": high},
        ]

    # 퍼센트 계산
    factor_upper = str(cond.get("factor", "")).upper()
    if factor_upper.startswith(("RET_", "PRICE_CHANGE_")):
        val = cond.get("value")
        if isinstance(val, (int, float)) and val >= 1:
            cond["value"] = val / 100.0

    return cond

# ======================================
# Claude 호출
# ======================================
def call_claude_and_get_json(text: str) -> dict:
    """Bedrock 호출 + 간단한 재시도(Throttling 대비)."""
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
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
            invoke_kwargs = {
                "contentType": "application/json",
                "accept": "application/json",
                "body": json.dumps(payload),
            }
            if BEDROCK_INFERENCE_PROFILE_ID:
                invoke_kwargs["inferenceProfileId"] = BEDROCK_INFERENCE_PROFILE_ID
            else:
                invoke_kwargs["modelId"] = BEDROCK_MODEL_ID

            response = client.invoke_model(**invoke_kwargs)

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
    normalized: List[Condition] = []
    for raw in conditions:
        try:
            norm = _normalize_condition(raw)
        except ValueError as exc:
            logger.warning("지원하지 않는 팩터 조건 무시: %s", exc)
            continue
        if isinstance(norm, list):
            # between 같은 경우 두 조건으로 확장
            for n in norm:
                normalized.append(Condition(**n))
        else:
            normalized.append(Condition(**norm))

    typed_conditions = normalized
    return StrategyResponse(conditions=typed_conditions)
