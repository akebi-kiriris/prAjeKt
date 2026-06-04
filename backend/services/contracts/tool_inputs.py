from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class CreateTaskToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    data: dict[str, Any]


class UpdateTaskToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_user_id: int
    task_id: int
    data: dict[str, Any]


class ListTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int


class TaskCommentSummaryToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int


class TimelineGenerateTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    project_name: str
    description: str = ""


class CreateTimelineToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    data: dict[str, Any]


class TimelineBatchCreateTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    user_id: int
    tasks: list[dict[str, Any]]


class TimelineConflictCheckToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    actor_user_id: int
    payload: dict[str, Any]


class GroupSnapshotToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: int
    window_days: int = 30
    created_by: int | None = None
    force: bool = False


class KnowledgeUploadToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    filename: str
    content: str
    project_id: int | None = None
    mime_type: str | None = None

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        filename = value.strip()
        if not filename:
            raise ValueError("filename 不可為空")
        return filename

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content 不可為空")
        return value


class KnowledgeListToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    limit: int = 50
    offset: int = 0
    project_id: int | None = None
    q: str | None = None
    sort: str = "created_desc"
    status: str | None = None

    @field_validator("limit", mode="before")
    @classmethod
    def _normalize_limit(cls, value: Any) -> int:
        parsed = _to_int_or_none(value)
        if parsed is None or parsed <= 0:
            return 50
        return min(parsed, 100)

    @field_validator("offset", mode="before")
    @classmethod
    def _normalize_offset(cls, value: Any) -> int:
        parsed = _to_int_or_none(value)
        if parsed is None or parsed < 0:
            return 0
        return parsed
