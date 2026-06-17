from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contracts.auth_contracts import AuthUserResponse


class StrictResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")


def response_payload(response: BaseModel) -> dict[str, Any]:
    return response.model_dump(exclude_none=True)


class MessageResponse(StrictResponse):
    message: str


class IdMutationResponse(MessageResponse):
    id: int


class TaskIdMutationResponse(MessageResponse):
    task_id: int


class UserIdMutationResponse(MessageResponse):
    user_id: int


class CompletionResponse(MessageResponse):
    completed: bool


class TaskStatusMutationResponse(CompletionResponse):
    status: str


class CountResponse(StrictResponse):
    count: int


class UnreadCountResponse(StrictResponse):
    unread_count: int


class AuthLoginResponse(StrictResponse):
    access_token: str
    refresh_token: str
    user: AuthUserResponse


class AuthRefreshResponse(StrictResponse):
    access_token: str


class GroupCreateResponse(MessageResponse):
    group_id: int
    invite_code: str


class GroupMessageSentResponse(MessageResponse):
    message_id: int


class GroupSnapshotQueuedResponse(StrictResponse):
    job_id: str
    status: str
    source_count: int
    threshold: int


class SearchUserResponse(StrictResponse):
    id: int
    name: str


class SubtaskMutationResponse(MessageResponse):
    subtask: dict[str, Any]


class ToolsListResponse(StrictResponse):
    tools: list[dict[str, Any]]


class HealthDatabaseInfo(StrictResponse):
    type: str | None = None
    url: str | None = None
    relative_path: str | None = None
    absolute_path: str | None = None
    exists: bool | None = None


class HealthDebugInfo(StrictResponse):
    cwd: str
    flask_env: str


class HealthResponse(StrictResponse):
    status: str = "ok"
    database: HealthDatabaseInfo | None = None
    debug: HealthDebugInfo | None = None


class OpenApiInfo(StrictResponse):
    title: str
    version: str


class OpenApiServer(StrictResponse):
    url: str


class OpenApiResponse(StrictResponse):
    description: str


class OpenApiOperation(StrictResponse):
    summary: str
    responses: dict[str, OpenApiResponse]


class OpenApiPathItem(StrictResponse):
    get: OpenApiOperation | None = None
    post: OpenApiOperation | None = None
    put: OpenApiOperation | None = None
    patch: OpenApiOperation | None = None
    delete: OpenApiOperation | None = None


class OpenApiDocument(StrictResponse):
    openapi: str = "3.1.0"
    info: OpenApiInfo
    servers: list[OpenApiServer] = Field(default_factory=list)
    paths: dict[str, OpenApiPathItem]
