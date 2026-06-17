from typing import Any

from pydantic import BaseModel


def validate_response_payload(model_cls: type[BaseModel], payload: dict[str, Any]) -> dict[str, Any]:
    model_cls.model_validate(payload)
    return payload


def build_response_payload(
    model_cls: type[BaseModel],
    payload: dict[str, Any],
    *,
    exclude_none: bool = False,
) -> dict[str, Any]:
    response = model_cls.model_validate(payload)
    return response.model_dump(exclude_none=exclude_none)
