from typing import Any

from pydantic import ValidationError

from contracts.tool_envelopes import ToolError


STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "AUTHENTICATION_REQUIRED",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "UPSTREAM_UNAVAILABLE",
    503: "UPSTREAM_UNAVAILABLE",
    504: "UPSTREAM_TIMEOUT",
}

ERROR_HINTS: dict[str, str] = {
    "VALIDATION_ERROR": "請檢查欄位格式或補齊必填資訊後再試。",
    "AUTHENTICATION_REQUIRED": "請先完成登入或重新驗證。",
    "PERMISSION_DENIED": "目前帳號沒有操作權限。",
    "NOT_FOUND": "請確認資源 ID 或範圍是否正確。",
    "CONFLICT": "資源狀態衝突，請調整參數後重試。",
    "RATE_LIMITED": "請稍後再試，或降低呼叫頻率。",
    "UPSTREAM_UNAVAILABLE": "外部服務暫時不可用，請稍後重試。",
    "UPSTREAM_TIMEOUT": "外部服務逾時，建議稍後重試。",
    "INTERNAL_ERROR": "系統發生未預期錯誤，請稍後再試。",
}


def map_exception_to_tool_error(exc: Exception) -> ToolError:
    if isinstance(exc, ValidationError):
        return ToolError(
            error_code="VALIDATION_ERROR",
            message=str(exc),
            retryable=False,
            hint=ERROR_HINTS["VALIDATION_ERROR"],
        )

    status_code = getattr(exc, "status_code", 500)
    if not isinstance(status_code, int):
        status_code = 500

    error_code = STATUS_TO_ERROR_CODE.get(status_code, "INTERNAL_ERROR")
    retryable = error_code in {"UPSTREAM_UNAVAILABLE", "UPSTREAM_TIMEOUT"}
    if error_code == "INTERNAL_ERROR":
        message = ERROR_HINTS["INTERNAL_ERROR"]
    else:
        message = str(getattr(exc, "message", str(exc)) or "工具執行失敗")

    return ToolError(
        error_code=error_code,
        message=message,
        retryable=retryable,
        hint=ERROR_HINTS.get(error_code, ERROR_HINTS["INTERNAL_ERROR"]),
    )


def route_from_tool_error(error: ToolError | dict[str, Any], retry_count: int = 0, retry_limit: int = 2) -> str:
    retryable = error.retryable if isinstance(error, ToolError) else bool(error.get("retryable", False))
    error_code = error.error_code if isinstance(error, ToolError) else str(error.get("error_code", "INTERNAL_ERROR"))

    if retryable and retry_count < retry_limit:
        return "retry"
    if error_code in {"VALIDATION_ERROR", "NOT_FOUND", "CONFLICT"}:
        return "ask_user"
    return "stop"


def normalize_tool_result(raw: dict[str, Any]) -> dict[str, Any]:
    if "ok" in raw:
        return raw
    return {"ok": True, "data": raw}
