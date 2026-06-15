from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from contracts.shared_fields import parse_int_or_none
from contracts.task_contracts import TaskCreateInput, TaskCreateRequest, TaskUpdateInput, TaskUpdateRequest
from contracts.timeline_contracts import ConflictCheckInput, TimelineWriteRequest


class CreateTaskToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    data: "CreateTaskToolPayload"


class UpdateTaskToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_user_id: int
    task_id: int
    data: "UpdateTaskToolPayload"


class ListTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int


class TaskCommentSummaryToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int


class TimelineGenerateTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    actor_user_id: int
    project_name: str
    description: str = ""


class CreateTimelineToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    data: "CreateTimelineToolPayload"


class TimelineBatchCreateTasksToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    user_id: int
    tasks: list["BatchCreateTaskItem"]


class TimelineConflictCheckToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int
    actor_user_id: int
    payload: ConflictCheckInput


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
        parsed = parse_int_or_none(value)
        if parsed is None or parsed <= 0:
            return 50
        return min(parsed, 100)

    @field_validator("offset", mode="before")
    @classmethod
    def _normalize_offset(cls, value: Any) -> int:
        parsed = parse_int_or_none(value)
        if parsed is None or parsed < 0:
            return 0
        return parsed


class CreateTaskToolPayload(TaskCreateRequest):
    name: str | None = None
    end_date: str | None = None

    @model_validator(mode="after")
    def _validate_contract_shape(self):
        payload = self.model_dump(exclude_none=True)
        TaskCreateInput.model_validate(
            {
                "status": payload.get("status", "pending"),
                "priority": payload.get("priority", 2),
                "start_date": payload.get("start_date"),
                "end_date": payload.get("end_date", "1970-01-01T00:00:00"),
                "timeline_id": payload.get("timeline_id"),
                "assignee_user_ids": payload.get("assignee_user_ids") or [],
                "depends_on_task_ids": payload.get("depends_on_task_ids") or [],
            }
        )
        return self


class UpdateTaskToolPayload(TaskUpdateRequest):

    @model_validator(mode="after")
    def _validate_contract_shape(self):
        TaskUpdateInput.model_validate(self.model_dump(exclude_none=True))
        return self


class CreateTimelineToolPayload(TimelineWriteRequest):
    pass


class BatchCreateTaskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int | None = None
    isExisting: bool = False
    name: str | None = None
    priority: int | None = 2
    status: str | None = "pending"
    estimated_days: int | None = 3
    task_remark: str | None = ""
    depends_on_task_ids: list[int] | None = None
    depends_on_task_refs: list[str] | None = None

    @field_validator("task_id", mode="before")
    @classmethod
    def _normalize_task_id(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        parsed = parse_int_or_none(value)
        if parsed is None or parsed <= 0:
            raise ValueError("task_id 必須是正整數")
        return parsed

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            raise ValueError("name 不可為空")
        return text

    @field_validator("estimated_days", mode="before")
    @classmethod
    def _normalize_estimated_days(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        parsed = parse_int_or_none(value)
        if parsed is None or parsed <= 0:
            raise ValueError("estimated_days 必須是正整數")
        return parsed

    @field_validator("depends_on_task_refs", mode="before")
    @classmethod
    def _normalize_dependency_refs(cls, value: Any) -> list[str] | None:
        if value in (None, ""):
            return None
        if not isinstance(value, list):
            raise ValueError("depends_on_task_refs 必須是陣列")
        normalized: list[str] = []
        for item in value:
            text = str(item).strip()
            if not text:
                continue
            normalized.append(text)
        return normalized

    @model_validator(mode="after")
    def _validate_item_shape(self):
        if self.isExisting:
            if self.task_id is None:
                raise ValueError("isExisting=true 時必須提供 task_id")
            return self
        if self.name is None:
            raise ValueError("新任務必須提供 name")
        return self
