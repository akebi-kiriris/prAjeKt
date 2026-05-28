from flask import jsonify
from pydantic import ValidationError
from typing import Any, Callable, TypeVar

ModelT = TypeVar("ModelT")


def status_to_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, "UNKNOWN_ERROR")


def error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
):
    payload = {
        "error": message,
        "error_code": code,
    }
    if details is not None:
        payload["error_details"] = details
    return jsonify(payload), status_code


def error_from_exception(err: Exception):
    status_code = getattr(err, "status_code", 500)
    message = getattr(err, "message", "伺服器發生未預期錯誤")
    return error_response(status_to_error_code(status_code), message, status_code)


def format_pydantic_error(
    err: ValidationError,
    *,
    default_message: str = "輸入資料格式錯誤",
    integer_field_messages: dict[str, str] | None = None,
    custom_message_by_field: dict[str, str] | None = None,
):
    first_error = err.errors()[0] if err.errors() else {}
    error_type = first_error.get("type", "")
    field = str((first_error.get("loc") or ["欄位"])[-1])
    message = str(first_error.get("msg", default_message))

    if error_type == "extra_forbidden":
        return f"不允許的欄位: {field}"

    if custom_message_by_field and field in custom_message_by_field:
        return custom_message_by_field[field]

    if integer_field_messages and "valid integer" in message and field in integer_field_messages:
        return integer_field_messages[field]

    return message


def validate_payload_or_400(
    model_cls: type[ModelT],
    payload: dict[str, Any],
    *,
    error_message_builder: Callable[[ValidationError], str] | None = None,
    by_alias: bool = False,
) -> tuple[dict[str, Any] | None, tuple[Any, int] | None]:
    try:
        model = model_cls.model_validate(payload)
        return model.model_dump(exclude_unset=True, by_alias=by_alias), None
    except ValidationError as err:
        if error_message_builder:
            message = error_message_builder(err)
        else:
            message = format_pydantic_error(err)
        return None, error_response("VALIDATION_ERROR", message, 400)
