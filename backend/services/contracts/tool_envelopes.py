from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_code: str
    message: str
    retryable: bool = False
    hint: str = ""


class ToolSuccess(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    data: dict[str, Any] = Field(default_factory=dict)


class ToolFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = False
    error: ToolError


def make_success(data: dict[str, Any]) -> dict[str, Any]:
    return ToolSuccess(data=data).model_dump()


def make_failure(error: ToolError) -> dict[str, Any]:
    return ToolFailure(error=error).model_dump()
