from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from contracts.shared_fields import validate_iso_datetime_text, validate_non_empty_text, validate_priority


class TodoWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    content: str | None = None
    type: str | None = None
    deadline: str | None = None
    priority: int | None = None
    completed: bool | None = None

    @field_validator("title", "content", mode="before")
    @classmethod
    def _validate_text(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="field",
            empty_message="請確認是否有填入事項名稱或內容",
            allow_none=True,
        )

    @field_validator("deadline", mode="before")
    @classmethod
    def _validate_deadline(cls, value: Any) -> str | None:
        return validate_iso_datetime_text(value, field_name="deadline", allow_none=True)

    @field_validator("priority", mode="before")
    @classmethod
    def _validate_priority(cls, value: Any) -> int | None:
        return validate_priority(value, allow_none=True)


class TodoCreateRequest(TodoWriteRequest):
    title: str
    content: str

    @field_validator("title", "content", mode="before")
    @classmethod
    def _validate_required_text(cls, value: Any) -> str:
        text = validate_non_empty_text(
            value,
            field_name="field",
            empty_message="請確認是否有填入事項名稱或內容",
            allow_none=False,
        )
        if text is None:
            raise ValueError("請確認是否有填入事項名稱或內容")
        return text


class TodoUpdateRequest(TodoWriteRequest):
    pass


class TodoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    content: str
    type: str | None = None
    deadline: str | None = None
    completed: bool
    priority: int
    created_at: str | None = None
    updated_at: str | None = None
