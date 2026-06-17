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


class TaskMemberResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    name: str
    role: int
    email: str | None = None
    avatar: str | None = None
    assigned_at: str | None = None


class SubtaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    task_id: int
    name: str
    completed: bool
    sort_order: int
    created_at: str | None = None


class TaskListItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    name: str
    completed: bool
    completed_at: str | None = None
    timeline_id: int | None = None
    priority: int
    status: str
    tags: list[str] | str | None = None
    estimated_hours: int | float | None = None
    actual_hours: int | float | None = None
    members: list[dict[str, Any]] = Field(default_factory=list)
    subtasks: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    updated_at: str | None = None
    task_remark: str | None = None
    isWork: int | bool | None = None
    depends_on_task_ids: list[int] = Field(default_factory=list)
    is_owner: bool


class TaskCommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment_id: int
    task_id: int | None = None
    user_id: int
    user_name: str
    user_avatar: str | None = None
    task_message: str
    created_at: str | None = None


class TaskCommentSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decisions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    raw: str | None = None


class TaskCommentSummaryMetaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int | None = None
    comment_count: int
    total_comments: int | None = None
    used_comments: int | None = None
    truncated: bool | None = None
    context_chars: int | None = None
    model: str | None = None


class TaskCommentSummaryPayloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int
    message: str | None = None
    summary: TaskCommentSummaryResponse
    meta: TaskCommentSummaryMetaResponse


class TaskFileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: str | None = None
    uploaded_by: int | None = None
    uploaded_by_name: str | None = None


class TaskFileUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    message: str
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: str | None = None
