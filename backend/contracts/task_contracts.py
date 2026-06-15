from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from contracts.shared_fields import (
    TASK_STATUS_BOARD_VALUES,
    parse_iso_datetime_or_none,
    validate_iso_datetime_text,
    validate_member_role,
    validate_non_empty_text,
    validate_priority,
    validate_task_status,
)


class TaskWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    timeline_id: int | None = None
    priority: int | None = None
    status: str | None = None
    tags: list[str] | None = None
    estimated_hours: int | float | None = None
    actual_hours: int | float | None = None
    start_date: str | None = None
    end_date: str | None = None
    task_remark: str | None = None
    isWork: int | bool | None = None
    depends_on_task_ids: list[int] | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="name 不可為空",
            allow_none=True,
        )

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str | None) -> str | None:
        return validate_task_status(value, allow_none=True)

    @field_validator("priority", mode="before")
    @classmethod
    def _validate_priority(cls, value: Any) -> int | None:
        return validate_priority(value, allow_none=True)

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> str | None:
        return validate_iso_datetime_text(value, field_name="start_date", allow_none=True)

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> str | None:
        return validate_iso_datetime_text(value, field_name="end_date", allow_none=True)


class TaskCreateRequest(TaskWriteRequest):
    name: str
    end_date: str
    assignee_user_ids: list[int] | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _validate_required_name(cls, value: Any) -> str:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="name 不可為空",
            allow_none=False,
        )

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_required_end_date(cls, value: Any) -> str:
        text = validate_iso_datetime_text(value, field_name="end_date", allow_none=False)
        if text is None:
            raise ValueError("end_date 格式錯誤")
        return text


class TaskUpdateRequest(TaskWriteRequest):
    pass


class TaskMemberAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    role: int = 1

    @field_validator("role", mode="before")
    @classmethod
    def _validate_role(cls, value: Any) -> int:
        return validate_member_role(value)


class TaskMemberRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: int

    @field_validator("role", mode="before")
    @classmethod
    def _validate_role(cls, value: Any) -> int:
        return validate_member_role(value)


class TaskCommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str | None = None
    task_message: str | None = None


class SubtaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="請提供子任務名稱",
            allow_none=False,
        )


class SubtaskUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    completed: bool | None = None
    sort_order: int | None = None


class TaskCreateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "pending"
    priority: int = 2
    start_date: datetime | None = None
    end_date: datetime
    timeline_id: int | None = None
    assignee_user_ids: list[int] = Field(default_factory=list)
    depends_on_task_ids: list[int] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        normalized = validate_task_status(value, allow_none=False)
        if normalized is None:
            raise ValueError("status 欄位值不合法")
        return normalized

    @field_validator("priority", mode="before")
    @classmethod
    def _validate_priority(cls, value: Any) -> int:
        normalized = validate_priority(value, allow_none=False)
        if normalized is None:
            raise ValueError("priority 必須是數字")
        return normalized

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> datetime | None:
        return parse_iso_datetime_or_none(value, field_name="start_date")

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> datetime:
        parsed = parse_iso_datetime_or_none(value, field_name="end_date")
        if parsed is None:
            raise ValueError("end_date 格式錯誤")
        return parsed


class TaskUpdateInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    timeline_id: int | None = None
    priority: int | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    depends_on_task_ids: list[int] | None = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str | None) -> str | None:
        return validate_task_status(value, allow_none=True)

    @field_validator("priority", mode="before")
    @classmethod
    def _validate_priority(cls, value: Any) -> int | None:
        return validate_priority(value, allow_none=True)

    @field_validator("name", mode="before")
    @classmethod
    def _validate_name(cls, value: Any) -> str | None:
        return validate_non_empty_text(
            value,
            field_name="name",
            empty_message="name 不可為空",
            allow_none=True,
        )

    @field_validator("start_date", mode="before")
    @classmethod
    def _validate_start_date(cls, value: Any) -> datetime | None:
        return parse_iso_datetime_or_none(value, field_name="start_date")

    @field_validator("end_date", mode="before")
    @classmethod
    def _validate_end_date(cls, value: Any) -> datetime | None:
        return parse_iso_datetime_or_none(value, field_name="end_date")


class TaskStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        if value not in TASK_STATUS_BOARD_VALUES:
            raise ValueError(f"無效的狀態，有效值為: {['pending', 'in_progress', 'completed']}")
        return value


class TaskStatusUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def _validate_status(cls, value: str) -> str:
        if value not in TASK_STATUS_BOARD_VALUES:
            raise ValueError(f"無效的狀態，有效值為: {['pending', 'in_progress', 'completed']}")
        return value
