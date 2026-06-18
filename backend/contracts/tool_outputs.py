from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.group_contracts import GroupSnapshotResponse
from contracts.knowledge_contracts import (
    KnowledgeDocumentUploadResponse,
    KnowledgeDocumentsListResponse,
)
from contracts.task_contracts import TaskCommentSummaryPayloadResponse
from contracts.timeline_contracts import (
    TimelineBatchCreateTasksResponse,
    TimelineConflictCheckResponse,
    TimelineGeneratedTaskResponse,
)


class TaskCreateToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: int


class CommonToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    updated: bool = True


class ListTasksToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[dict[str, Any]] = Field(default_factory=list)


class TimelineGenerateTasksToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    tasks: list[TimelineGeneratedTaskResponse] = Field(default_factory=list)
    existingCount: int = 0
    generatedCount: int = 0


class TimelineConflictCheckToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: TimelineConflictCheckResponse


class CreateTimelineToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeline_id: int


class TimelineBatchCreateTasksToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: TimelineBatchCreateTasksResponse


class GroupSnapshotToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: GroupSnapshotResponse


class KnowledgeUploadToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: KnowledgeDocumentUploadResponse


class KnowledgeListToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: KnowledgeDocumentsListResponse


class TaskCommentSummaryToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: TaskCommentSummaryPayloadResponse
