"""공통 에러 응답 유틸리티."""
from fastapi.responses import JSONResponse

ERROR_TYPES = {
    "E001": "LLM_TIMEOUT",
    "E002": "INVALID_RESPONSE",
    "E003": "SESSION_EXPIRED",
    "E004": "STRATEGY_NOT_FOUND",
    "E005": "INVALID_QUESTION_ID",
    "E006": "BACKTEST_API_ERROR",
    "E999": "INTERNAL_ERROR",
}


def make_error(
    code: str,
    message: str,
    user_message: str = "",
    error_type: str | None = None,
    details: str | None = None,
    retry_allowed: bool | None = None,
) -> dict:
    """사양서에 맞춘 에러 페이로드를 생성합니다."""
    error_type = error_type or ERROR_TYPES.get(code, "INTERNAL_ERROR")

    payload = {
        "error": {
            "type": error_type,
            "code": code,
            "message": message,
            "user_message": user_message or message,
        }
    }

    if details:
        payload["error"]["details"] = details
    if retry_allowed is not None:
        payload["error"]["retry_allowed"] = retry_allowed

    return payload


def make_error_response(
    status_code: int,
    code: str,
    message: str,
    user_message: str = "",
    error_type: str | None = None,
    details: str | None = None,
    retry_allowed: bool | None = None,
):
    """JSONResponse를 바로 반환합니다."""
    payload = make_error(
        code=code,
        message=message,
        user_message=user_message,
        error_type=error_type,
        details=details,
        retry_allowed=retry_allowed,
    )
    return JSONResponse(status_code=status_code, content=payload)
