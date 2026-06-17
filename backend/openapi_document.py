from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from contracts.auth_contracts import CurrentUserResponse, LoginRequest, RegisterRequest
from contracts.group_contracts import (
    GroupCreateRequest,
    GroupListItemResponse,
    GroupJoinRequest,
    GroupMemberResponse,
    GroupMessageRequest,
    GroupMessageResponse,
    GroupSnapshotJobResponse,
    GroupSnapshotRequest,
    GroupSnapshotResponse,
)
from contracts.knowledge_contracts import (
    KnowledgeBatchResponse,
    KnowledgeDocumentBatchRequest,
    KnowledgeDocumentEventsResponse,
    KnowledgeDocumentIdResponse,
    KnowledgeDocumentReindexResponse,
    KnowledgeDocumentsListResponse,
    KnowledgeDocumentUploadResponse,
)
from contracts.notification_contracts import NotificationResponse
from contracts.profile_contracts import (
    ProfileChartStatsResponse,
    ProfileResponse,
    ProfileSearchRequest,
    ProfileSearchResponse,
    ProfileUpdateRequest,
)
from contracts.response_contracts import (
    AuthLoginResponse,
    AuthRefreshResponse,
    CompletionResponse,
    CountResponse,
    GroupCreateResponse,
    GroupMessageSentResponse,
    GroupSnapshotQueuedResponse,
    HealthResponse,
    IdMutationResponse,
    MessageResponse,
    SearchUserResponse,
    SubtaskMutationResponse,
    TaskIdMutationResponse,
    TaskStatusMutationResponse,
    ToolsListResponse,
    UnreadCountResponse,
    UserIdMutationResponse,
)
from contracts.task_contracts import (
    SubtaskCreateRequest,
    SubtaskResponse,
    SubtaskUpdateRequest,
    TaskCommentRequest,
    TaskCommentResponse,
    TaskCommentSummaryPayloadResponse,
    TaskCreateRequest,
    TaskFileResponse,
    TaskFileUploadResponse,
    TaskListItemResponse,
    TaskMemberAddRequest,
    TaskMemberResponse,
    TaskMemberRoleUpdateRequest,
    TaskStatusRequest,
    TaskUpdateRequest,
)
from contracts.timeline_contracts import (
    ConflictCheckInput,
    TimelineAddMemberRequest,
    TimelineBatchCreateTasksRequest,
    TimelineBatchCreateTasksResponse,
    TimelineConflictCheckResponse,
    TimelineCreateRequest,
    TimelineGenerateTasksRequest,
    TimelineGenerateTasksResponse,
    TimelineListItemResponse,
    TimelineMemberResponse,
    TimelineMemberStatsResponse,
    TimelinePlanSuggestionResponse,
    TimelineRemarkRequest,
    TimelineRiskAnalysisResponse,
    TimelineRiskNotificationResponse,
    TimelineSearchUserRequest,
    TimelineTaskItemResponse,
    TimelineUpdateRequest,
    UpcomingTimelineResponse,
    WeeklyReportResponse,
)
from contracts.todo_contracts import TodoCreateRequest, TodoResponse, TodoUpdateRequest
from contracts.trash_contracts import TrashPayloadResponse


OPENAPI_VERSION = "3.1.0"
API_VERSION = "10.3.0"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "reference" / "openapi.json"
_SCHEMA_REF_PREFIX = "#/components/schemas/"


def _normalize_schema(schema: dict[str, Any], components: dict[str, dict[str, Any]]) -> dict[str, Any]:
    normalized = dict(schema)
    definitions = normalized.pop("$defs", {})
    for name, nested_schema in definitions.items():
        if name not in components:
            components[name] = _normalize_schema(nested_schema, components)
    return normalized


def _register_model(components: dict[str, dict[str, Any]], model_cls: type[BaseModel]) -> dict[str, str]:
    name = model_cls.__name__
    if name not in components:
        schema = model_cls.model_json_schema(ref_template=f"{_SCHEMA_REF_PREFIX}{{model}}")
        components[name] = _normalize_schema(schema, components)
    return {"$ref": f"{_SCHEMA_REF_PREFIX}{name}"}


def _register_inline_schema(
    components: dict[str, dict[str, Any]],
    name: str,
    schema: dict[str, Any],
) -> dict[str, str]:
    if name not in components:
        components[name] = schema
    return {"$ref": f"{_SCHEMA_REF_PREFIX}{name}"}


def _json_content(schema: dict[str, Any]) -> dict[str, Any]:
    return {"application/json": {"schema": schema}}


def _binary_content(mime_type: str = "application/octet-stream") -> dict[str, Any]:
    return {
        mime_type: {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


def _request_body_from_model(
    components: dict[str, dict[str, Any]],
    model_cls: type[BaseModel],
    *,
    description: str | None = None,
    required: bool = True,
) -> dict[str, Any]:
    request_body = {
        "required": required,
        "content": _json_content(_register_model(components, model_cls)),
    }
    if description:
        request_body["description"] = description
    return request_body


def _response_entry(
    components: dict[str, dict[str, Any]],
    description: str,
    *,
    model_cls: type[BaseModel] | None = None,
    many: bool = False,
    content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"description": description}
    if content is not None:
        payload["content"] = content
        return payload
    if model_cls is not None:
        schema = _register_model(components, model_cls)
        if many:
            schema = {"type": "array", "items": schema}
        payload["content"] = _json_content(schema)
    return payload


def _error_response_ref(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": _json_content({"$ref": f"{_SCHEMA_REF_PREFIX}ApiErrorResponse"}),
    }


def _default_error_responses() -> dict[str, Any]:
    return {
        "400": _error_response_ref("請求資料不合法"),
        "401": _error_response_ref("尚未登入或 token 無效"),
        "403": _error_response_ref("權限不足"),
        "404": _error_response_ref("資源不存在"),
        "409": _error_response_ref("資源狀態衝突"),
        "500": _error_response_ref("伺服器錯誤"),
    }


def _tag_for_path(path: str) -> list[str]:
    first_segment = path.strip("/").split("/", 1)[0] or "system"
    return [first_segment]


def _path_parameter(param_name: str) -> dict[str, Any]:
    is_integer = param_name.endswith("_id") or param_name == "id"
    schema_type = "integer" if is_integer else "string"
    description = f"路徑參數：{param_name}"
    return {
        "name": param_name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": schema_type},
    }


def _query_parameter(
    name: str,
    *,
    schema: dict[str, Any] | None = None,
    required: bool = False,
    description: str = "",
) -> dict[str, Any]:
    return {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": schema or {"type": "string"},
    }


def _path_parameters(path: str) -> list[dict[str, Any]]:
    return [_path_parameter(param_name) for param_name in re.findall(r"{([^}]+)}", path)]


def _security(auth_required: bool) -> list[dict[str, list[str]]] | list[Any]:
    return [{"bearerAuth": []}] if auth_required else []


def _operation(
    components: dict[str, dict[str, Any]],
    *,
    path: str,
    summary: str,
    success_code: str = "200",
    success_description: str = "成功回應",
    request_model: type[BaseModel] | None = None,
    response_model: type[BaseModel] | None = None,
    response_many: bool = False,
    request_body: dict[str, Any] | None = None,
    responses: dict[str, Any] | None = None,
    query_parameters: list[dict[str, Any]] | None = None,
    auth_required: bool = True,
    description: str | None = None,
) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "summary": summary,
        "tags": _tag_for_path(path),
        "parameters": _path_parameters(path) + (query_parameters or []),
        "responses": {},
        "security": _security(auth_required),
    }
    if description:
        operation["description"] = description
    if request_body is not None:
        operation["requestBody"] = request_body
    elif request_model is not None:
        operation["requestBody"] = _request_body_from_model(components, request_model)

    if response_model is not None:
        operation["responses"][success_code] = _response_entry(
            components,
            success_description,
            model_cls=response_model,
            many=response_many,
        )
    elif responses and success_code not in responses:
        operation["responses"][success_code] = {"description": success_description}

    if responses:
        operation["responses"].update(responses)

    for code, payload in _default_error_responses().items():
        operation["responses"].setdefault(code, payload)

    return operation


def _multipart_upload_request(name: str, description: str) -> dict[str, Any]:
    return {
        "required": True,
        "description": description,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["file"],
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                        }
                    },
                }
            }
        },
    }


def _prepare_components() -> dict[str, dict[str, Any]]:
    return {
        "ApiErrorResponse": {
            "type": "object",
            "required": ["error", "error_code"],
            "properties": {
                "error": {"type": "string"},
                "error_code": {"type": "string"},
                "error_details": {
                    "type": "object",
                    "additionalProperties": True,
                },
            },
            "additionalProperties": False,
        },
        "CopilotMcpExecuteRequest": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {"type": "string"},
                "context": {"type": "object", "additionalProperties": True},
                "preferred_tool": {"type": "string"},
                "tool_arguments": {"type": "object", "additionalProperties": True},
                "auto_create_generated_tasks": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "CopilotAgentPlanRequest": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {"type": "string"},
                "context": {"type": "object", "additionalProperties": True},
                "tool_payloads": {"type": "object", "additionalProperties": True},
                "request_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "CopilotAgentExecuteRequest": {
            "type": "object",
            "required": ["plan_id", "confirm"],
            "properties": {
                "plan_id": {"type": "string"},
                "confirm": {"type": "boolean"},
                "tool_payloads": {"type": "object", "additionalProperties": True},
                "max_loops": {"type": "integer"},
                "request_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "CopilotAgentRejectRequest": {
            "type": "object",
            "required": ["plan_id"],
            "properties": {
                "plan_id": {"type": "string"},
                "reason": {"type": "string"},
                "request_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "CopilotAgentReplanRequest": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {"type": "string"},
                "plan_id": {"type": "string"},
                "context": {"type": "object", "additionalProperties": True},
                "tool_payloads": {"type": "object", "additionalProperties": True},
                "request_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "CopilotGenericResponse": {
            "type": "object",
            "additionalProperties": True,
        },
    }


def build_openapi_document() -> dict[str, Any]:
    components = _prepare_components()

    paths: dict[str, Any] = {
        "/health": {
            "get": _operation(
                components,
                path="/health",
                summary="健康檢查",
                response_model=HealthResponse,
                auth_required=False,
            )
        },
        "/auth/register": {
            "post": _operation(
                components,
                path="/auth/register",
                summary="註冊使用者",
                success_code="201",
                request_model=RegisterRequest,
                response_model=UserIdMutationResponse,
                auth_required=False,
            )
        },
        "/auth/login": {
            "post": _operation(
                components,
                path="/auth/login",
                summary="登入並取得 token",
                request_model=LoginRequest,
                response_model=AuthLoginResponse,
                auth_required=False,
            )
        },
        "/auth/logout": {
            "post": _operation(
                components,
                path="/auth/logout",
                summary="登出",
                response_model=MessageResponse,
            )
        },
        "/auth/me": {
            "get": _operation(
                components,
                path="/auth/me",
                summary="取得當前使用者",
                response_model=CurrentUserResponse,
            )
        },
        "/auth/refresh": {
            "post": _operation(
                components,
                path="/auth/refresh",
                summary="刷新 access token",
                response_model=AuthRefreshResponse,
                description="需帶 refresh token 呼叫。",
            )
        },
        "/profile/me": {
            "get": _operation(
                components,
                path="/profile/me",
                summary="取得個人資料",
                response_model=ProfileResponse,
            ),
            "put": _operation(
                components,
                path="/profile/me",
                summary="更新個人資料",
                request_model=ProfileUpdateRequest,
                response_model=MessageResponse,
            ),
        },
        "/profile/search": {
            "post": _operation(
                components,
                path="/profile/search",
                summary="搜尋使用者",
                request_model=ProfileSearchRequest,
                response_model=ProfileSearchResponse,
            )
        },
        "/profile/chart-stats": {
            "get": _operation(
                components,
                path="/profile/chart-stats",
                summary="取得個人圖表統計",
                response_model=ProfileChartStatsResponse,
            )
        },
        "/tasks": {
            "get": _operation(
                components,
                path="/tasks",
                summary="取得任務清單",
                response_model=TaskListItemResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/tasks",
                summary="新增任務",
                success_code="201",
                request_model=TaskCreateRequest,
                response_model=TaskIdMutationResponse,
            ),
        },
        "/tasks/{task_id}": {
            "put": _operation(
                components,
                path="/tasks/{task_id}",
                summary="更新任務",
                request_model=TaskUpdateRequest,
                response_model=MessageResponse,
            ),
            "delete": _operation(
                components,
                path="/tasks/{task_id}",
                summary="刪除任務",
                response_model=MessageResponse,
            ),
        },
        "/tasks/{task_id}/toggle": {
            "patch": _operation(
                components,
                path="/tasks/{task_id}/toggle",
                summary="切換任務完成狀態",
                response_model=CompletionResponse,
            )
        },
        "/tasks/{task_id}/status": {
            "patch": _operation(
                components,
                path="/tasks/{task_id}/status",
                summary="更新任務看板狀態",
                request_model=TaskStatusRequest,
                response_model=TaskStatusMutationResponse,
            )
        },
        "/tasks/{task_id}/members": {
            "get": _operation(
                components,
                path="/tasks/{task_id}/members",
                summary="取得任務成員",
                response_model=TaskMemberResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/tasks/{task_id}/members",
                summary="新增任務成員",
                success_code="201",
                request_model=TaskMemberAddRequest,
                response_model=TaskMemberResponse,
            ),
        },
        "/tasks/{task_id}/members/{member_id}": {
            "patch": _operation(
                components,
                path="/tasks/{task_id}/members/{member_id}",
                summary="更新任務成員角色",
                request_model=TaskMemberRoleUpdateRequest,
                response_model=MessageResponse,
            ),
            "delete": _operation(
                components,
                path="/tasks/{task_id}/members/{member_id}",
                summary="移除任務成員",
                response_model=MessageResponse,
            ),
        },
        "/tasks/{task_id}/comments": {
            "get": _operation(
                components,
                path="/tasks/{task_id}/comments",
                summary="取得任務留言",
                response_model=TaskCommentResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/tasks/{task_id}/comments",
                summary="新增任務留言",
                success_code="201",
                request_model=TaskCommentRequest,
                response_model=TaskCommentResponse,
            ),
        },
        "/tasks/{task_id}/ai-comment-summary": {
            "post": _operation(
                components,
                path="/tasks/{task_id}/ai-comment-summary",
                summary="產生任務留言摘要",
                response_model=TaskCommentSummaryPayloadResponse,
            )
        },
        "/tasks/{task_id}/comments/{comment_id}": {
            "delete": _operation(
                components,
                path="/tasks/{task_id}/comments/{comment_id}",
                summary="刪除任務留言",
                response_model=MessageResponse,
            )
        },
        "/tasks/{task_id}/files": {
            "get": _operation(
                components,
                path="/tasks/{task_id}/files",
                summary="取得任務附件",
                response_model=TaskFileResponse,
                response_many=True,
            )
        },
        "/tasks/{task_id}/files/{file_id}": {
            "delete": _operation(
                components,
                path="/tasks/{task_id}/files/{file_id}",
                summary="刪除任務附件",
                response_model=MessageResponse,
            )
        },
        "/tasks/files/{filename}": {
            "get": _operation(
                components,
                path="/tasks/files/{filename}",
                summary="下載或預覽任務附件",
                responses={
                    "200": _response_entry(
                        components,
                        "檔案串流",
                        content=_binary_content(),
                    )
                },
            )
        },
        "/tasks/{task_id}/upload": {
            "post": _operation(
                components,
                path="/tasks/{task_id}/upload",
                summary="上傳任務附件",
                success_code="201",
                request_body=_multipart_upload_request("TaskFileUploadRequest", "以 multipart/form-data 上傳任務附件"),
                response_model=TaskFileUploadResponse,
            )
        },
        "/tasks/{task_id}/subtasks": {
            "get": _operation(
                components,
                path="/tasks/{task_id}/subtasks",
                summary="取得子任務",
                response_model=SubtaskResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/tasks/{task_id}/subtasks",
                summary="新增子任務",
                success_code="201",
                request_model=SubtaskCreateRequest,
                response_model=SubtaskMutationResponse,
            ),
        },
        "/tasks/{task_id}/subtasks/{subtask_id}": {
            "put": _operation(
                components,
                path="/tasks/{task_id}/subtasks/{subtask_id}",
                summary="更新子任務",
                request_model=SubtaskUpdateRequest,
                response_model=SubtaskMutationResponse,
            ),
            "delete": _operation(
                components,
                path="/tasks/{task_id}/subtasks/{subtask_id}",
                summary="刪除子任務",
                response_model=MessageResponse,
            ),
        },
        "/tasks/{task_id}/subtasks/{subtask_id}/toggle": {
            "patch": _operation(
                components,
                path="/tasks/{task_id}/subtasks/{subtask_id}/toggle",
                summary="切換子任務狀態",
                response_model=SubtaskMutationResponse,
            )
        },
        "/tasks/upcoming": {
            "get": _operation(
                components,
                path="/tasks/upcoming",
                summary="取得即將到期任務",
                response_model=TaskListItemResponse,
                response_many=True,
            )
        },
        "/timelines": {
            "get": _operation(
                components,
                path="/timelines",
                summary="取得專案清單",
                response_model=TimelineListItemResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/timelines",
                summary="新增專案",
                success_code="201",
                request_model=TimelineCreateRequest,
                response_model=IdMutationResponse,
            ),
        },
        "/timelines/{timeline_id}": {
            "put": _operation(
                components,
                path="/timelines/{timeline_id}",
                summary="更新專案",
                request_model=TimelineUpdateRequest,
                response_model=MessageResponse,
            ),
            "delete": _operation(
                components,
                path="/timelines/{timeline_id}",
                summary="刪除專案",
                response_model=MessageResponse,
            ),
        },
        "/timelines/{timeline_id}/tasks": {
            "get": _operation(
                components,
                path="/timelines/{timeline_id}/tasks",
                summary="取得專案任務",
                response_model=TimelineTaskItemResponse,
                response_many=True,
            )
        },
        "/timelines/{timeline_id}/weekly-report": {
            "get": _operation(
                components,
                path="/timelines/{timeline_id}/weekly-report",
                summary="取得專案週報",
                response_model=WeeklyReportResponse,
                query_parameters=[
                    _query_parameter("start_date", description="週報起始日期，格式 YYYY-MM-DD"),
                    _query_parameter("end_date", description="週報結束日期，格式 YYYY-MM-DD"),
                ],
            )
        },
        "/timelines/{timeline_id}/risk-analysis": {
            "get": _operation(
                components,
                path="/timelines/{timeline_id}/risk-analysis",
                summary="取得專案風險分析",
                response_model=TimelineRiskAnalysisResponse,
            )
        },
        "/timelines/{timeline_id}/risk-analysis/notify": {
            "post": _operation(
                components,
                path="/timelines/{timeline_id}/risk-analysis/notify",
                summary="觸發專案風險通知",
                response_model=TimelineRiskNotificationResponse,
            )
        },
        "/timelines/{timeline_id}/conflict-check": {
            "post": _operation(
                components,
                path="/timelines/{timeline_id}/conflict-check",
                summary="檢查專案任務衝突",
                request_model=ConflictCheckInput,
                response_model=TimelineConflictCheckResponse,
            )
        },
        "/timelines/{timeline_id}/remark": {
            "put": _operation(
                components,
                path="/timelines/{timeline_id}/remark",
                summary="更新專案備註",
                request_model=TimelineRemarkRequest,
                response_model=MessageResponse,
            )
        },
        "/timelines/search_user": {
            "post": _operation(
                components,
                path="/timelines/search_user",
                summary="依 Email 搜尋專案使用者",
                request_model=TimelineSearchUserRequest,
                response_model=SearchUserResponse,
            )
        },
        "/timelines/{timeline_id}/members": {
            "get": _operation(
                components,
                path="/timelines/{timeline_id}/members",
                summary="取得專案成員",
                response_model=TimelineMemberResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/timelines/{timeline_id}/members",
                summary="新增專案成員",
                success_code="201",
                request_model=TimelineAddMemberRequest,
                response_model=TimelineMemberResponse,
            ),
        },
        "/timelines/{timeline_id}/members/{member_user_id}": {
            "delete": _operation(
                components,
                path="/timelines/{timeline_id}/members/{member_user_id}",
                summary="移除專案成員",
                response_model=MessageResponse,
            )
        },
        "/timelines/{timeline_id}/generate-tasks": {
            "post": _operation(
                components,
                path="/timelines/{timeline_id}/generate-tasks",
                summary="AI 生成專案任務",
                request_model=TimelineGenerateTasksRequest,
                response_model=TimelineGenerateTasksResponse,
            )
        },
        "/timelines/{timeline_id}/batch-create-tasks": {
            "post": _operation(
                components,
                path="/timelines/{timeline_id}/batch-create-tasks",
                summary="批量建立 AI 任務",
                success_code="201",
                request_model=TimelineBatchCreateTasksRequest,
                response_model=TimelineBatchCreateTasksResponse,
            )
        },
        "/timelines/ai-suggest-plan": {
            "post": _operation(
                components,
                path="/timelines/ai-suggest-plan",
                summary="RAG 專案規劃建議",
                response_model=TimelinePlanSuggestionResponse,
                request_body={
                    "required": True,
                    "description": "目前仍由 RAG planning service 直接驗證的 payload。",
                    "content": _json_content(
                        {
                            "type": "object",
                            "additionalProperties": True,
                        }
                    ),
                },
            )
        },
        "/timelines/upcoming": {
            "get": _operation(
                components,
                path="/timelines/upcoming",
                summary="取得即將到期專案",
                response_model=UpcomingTimelineResponse,
                response_many=True,
            )
        },
        "/timelines/{timeline_id}/member-stats": {
            "get": _operation(
                components,
                path="/timelines/{timeline_id}/member-stats",
                summary="取得專案成員統計",
                response_model=TimelineMemberStatsResponse,
            )
        },
        "/knowledge/documents": {
            "get": _operation(
                components,
                path="/knowledge/documents",
                summary="取得知識文件清單",
                response_model=KnowledgeDocumentsListResponse,
                query_parameters=[
                    _query_parameter("limit", schema={"type": "integer"}, description="每頁筆數，預設 50"),
                    _query_parameter("offset", schema={"type": "integer"}, description="分頁偏移量，預設 0"),
                    _query_parameter("project_id", schema={"type": "integer"}, description="專案檔案區 id"),
                    _query_parameter("q", description="搜尋關鍵字"),
                    _query_parameter("sort", description="排序方式，例如 created_desc"),
                    _query_parameter("status", description="文件狀態篩選"),
                ],
            ),
            "post": _operation(
                components,
                path="/knowledge/documents",
                summary="上傳知識文件",
                success_code="201",
                request_body=_multipart_upload_request("KnowledgeDocumentUploadRequest", "以 multipart/form-data 上傳知識文件"),
                response_model=KnowledgeDocumentUploadResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, description="可選；指定專案檔案區"),
                ],
            ),
        },
        "/knowledge/documents/{document_id}": {
            "delete": _operation(
                components,
                path="/knowledge/documents/{document_id}",
                summary="刪除知識文件",
                response_model=KnowledgeDocumentIdResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, description="可選；專案檔案區 id"),
                ],
            )
        },
        "/knowledge/documents/{document_id}/reindex": {
            "post": _operation(
                components,
                path="/knowledge/documents/{document_id}/reindex",
                summary="重建單一知識文件索引",
                response_model=KnowledgeDocumentReindexResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, description="可選；專案檔案區 id"),
                ],
            )
        },
        "/knowledge/documents/batch-delete": {
            "post": _operation(
                components,
                path="/knowledge/documents/batch-delete",
                summary="批量刪除知識文件",
                request_model=KnowledgeDocumentBatchRequest,
                response_model=KnowledgeBatchResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, required=True, description="專案檔案區 id"),
                ],
            )
        },
        "/knowledge/documents/batch-reindex": {
            "post": _operation(
                components,
                path="/knowledge/documents/batch-reindex",
                summary="批量重建知識文件索引",
                request_model=KnowledgeDocumentBatchRequest,
                response_model=KnowledgeBatchResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, required=True, description="專案檔案區 id"),
                ],
            )
        },
        "/knowledge/documents/{document_id}/download": {
            "get": _operation(
                components,
                path="/knowledge/documents/{document_id}/download",
                summary="下載知識文件",
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, required=True, description="專案檔案區 id"),
                ],
                responses={
                    "200": _response_entry(
                        components,
                        "檔案下載串流",
                        content=_binary_content(),
                    )
                },
            )
        },
        "/knowledge/documents/{document_id}/preview": {
            "get": _operation(
                components,
                path="/knowledge/documents/{document_id}/preview",
                summary="預覽知識文件",
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, required=True, description="專案檔案區 id"),
                ],
                responses={
                    "200": _response_entry(
                        components,
                        "檔案預覽串流",
                        content=_binary_content(),
                    )
                },
            )
        },
        "/knowledge/documents/events": {
            "get": _operation(
                components,
                path="/knowledge/documents/events",
                summary="取得知識文件事件",
                response_model=KnowledgeDocumentEventsResponse,
                query_parameters=[
                    _query_parameter("project_id", schema={"type": "integer"}, required=True, description="專案檔案區 id"),
                    _query_parameter("limit", schema={"type": "integer"}, description="每頁筆數，預設 50"),
                    _query_parameter("offset", schema={"type": "integer"}, description="分頁偏移量，預設 0"),
                ],
            )
        },
        "/groups": {
            "get": _operation(
                components,
                path="/groups",
                summary="取得群組清單",
                response_model=GroupListItemResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/groups",
                summary="建立群組",
                success_code="201",
                request_model=GroupCreateRequest,
                response_model=GroupCreateResponse,
            ),
        },
        "/groups/join": {
            "post": _operation(
                components,
                path="/groups/join",
                summary="透過邀請碼加入群組",
                request_model=GroupJoinRequest,
                response_model=MessageResponse,
            )
        },
        "/groups/{group_id}/leave": {
            "post": _operation(
                components,
                path="/groups/{group_id}/leave",
                summary="離開群組",
                response_model=MessageResponse,
            )
        },
        "/groups/{group_id}/members": {
            "get": _operation(
                components,
                path="/groups/{group_id}/members",
                summary="取得群組成員",
                response_model=GroupMemberResponse,
                response_many=True,
            )
        },
        "/groups/{group_id}/messages": {
            "get": _operation(
                components,
                path="/groups/{group_id}/messages",
                summary="取得群組訊息",
                response_model=GroupMessageResponse,
                response_many=True,
            ),
            "post": _operation(
                components,
                path="/groups/{group_id}/messages",
                summary="發送群組訊息",
                success_code="201",
                request_model=GroupMessageRequest,
                response_model=GroupMessageSentResponse,
            ),
        },
        "/groups/{group_id}/ai-snapshot": {
            "post": _operation(
                components,
                path="/groups/{group_id}/ai-snapshot",
                summary="產生群組 AI 快照",
                request_model=GroupSnapshotRequest,
                response_model=GroupSnapshotResponse,
                responses={
                    "200": _response_entry(components, "同步回傳快照", model_cls=GroupSnapshotResponse),
                    "202": _response_entry(components, "已進入背景工作佇列", model_cls=GroupSnapshotQueuedResponse),
                },
            )
        },
        "/groups/snapshot-jobs/{job_id}": {
            "get": _operation(
                components,
                path="/groups/snapshot-jobs/{job_id}",
                summary="查詢群組 AI 快照工作",
                response_model=GroupSnapshotJobResponse,
            )
        },
        "/groups/{group_id}/ai-snapshot/latest": {
            "get": _operation(
                components,
                path="/groups/{group_id}/ai-snapshot/latest",
                summary="取得最新群組 AI 快照",
                response_model=GroupSnapshotResponse,
            )
        },
        "/messages/unread-count": {
            "get": _operation(
                components,
                path="/messages/unread-count",
                summary="取得未讀訊息數",
                response_model=UnreadCountResponse,
            )
        },
        "/messages/mark-all-read": {
            "post": _operation(
                components,
                path="/messages/mark-all-read",
                summary="標記所有訊息為已讀",
                response_model=MessageResponse,
            )
        },
        "/notifications": {
            "get": _operation(
                components,
                path="/notifications",
                summary="取得通知清單",
                response_model=NotificationResponse,
                response_many=True,
            )
        },
        "/notifications/unread-count": {
            "get": _operation(
                components,
                path="/notifications/unread-count",
                summary="取得未讀通知數",
                response_model=CountResponse,
            )
        },
        "/notifications/{notification_id}/read": {
            "patch": _operation(
                components,
                path="/notifications/{notification_id}/read",
                summary="標記通知為已讀",
                response_model=MessageResponse,
            )
        },
        "/notifications/read-all": {
            "patch": _operation(
                components,
                path="/notifications/read-all",
                summary="標記全部通知為已讀",
                response_model=MessageResponse,
            )
        },
        "/notifications/{notification_id}": {
            "delete": _operation(
                components,
                path="/notifications/{notification_id}",
                summary="刪除通知",
                response_model=MessageResponse,
            )
        },
        "/todos": {
            "get": _operation(
                components,
                path="/todos",
                summary="取得待辦清單",
                response_model=TodoResponse,
                response_many=True,
                query_parameters=[
                    _query_parameter("id", schema={"type": "integer"}, description="可選；僅查單筆待辦"),
                ],
            ),
            "post": _operation(
                components,
                path="/todos",
                summary="新增待辦",
                success_code="201",
                request_model=TodoCreateRequest,
                response_model=IdMutationResponse,
            ),
        },
        "/todos/{todo_id}": {
            "put": _operation(
                components,
                path="/todos/{todo_id}",
                summary="更新待辦",
                request_model=TodoUpdateRequest,
                response_model=MessageResponse,
            ),
            "delete": _operation(
                components,
                path="/todos/{todo_id}",
                summary="刪除待辦",
                response_model=MessageResponse,
            ),
        },
        "/todos/{todo_id}/toggle": {
            "patch": _operation(
                components,
                path="/todos/{todo_id}/toggle",
                summary="切換待辦狀態",
                response_model=CompletionResponse,
            )
        },
        "/trash": {
            "get": _operation(
                components,
                path="/trash",
                summary="取得垃圾桶內容",
                response_model=TrashPayloadResponse,
            )
        },
        "/trash/tasks/{task_id}/restore": {
            "patch": _operation(
                components,
                path="/trash/tasks/{task_id}/restore",
                summary="還原任務",
                response_model=MessageResponse,
            )
        },
        "/trash/tasks/{task_id}": {
            "delete": _operation(
                components,
                path="/trash/tasks/{task_id}",
                summary="永久刪除任務",
                response_model=MessageResponse,
            )
        },
        "/trash/timelines/{timeline_id}/restore": {
            "patch": _operation(
                components,
                path="/trash/timelines/{timeline_id}/restore",
                summary="還原專案",
                response_model=MessageResponse,
            )
        },
        "/trash/timelines/{timeline_id}": {
            "delete": _operation(
                components,
                path="/trash/timelines/{timeline_id}",
                summary="永久刪除專案",
                response_model=MessageResponse,
            )
        },
        "/copilot/mcp/execute": {
            "post": _operation(
                components,
                path="/copilot/mcp/execute",
                summary="執行 Copilot MCP 請求",
                request_body={
                    "required": True,
                    "content": _json_content(
                        _register_inline_schema(components, "CopilotMcpExecuteRequest", components["CopilotMcpExecuteRequest"])
                    ),
                },
                responses={
                    "200": _response_entry(
                        components,
                        "Copilot MCP 執行結果",
                        content=_json_content(
                            _register_inline_schema(components, "CopilotGenericResponse", components["CopilotGenericResponse"])
                        ),
                    )
                },
            )
        },
        "/copilot/agent/tools": {
            "get": _operation(
                components,
                path="/copilot/agent/tools",
                summary="取得 Copilot agent 工具清單",
                response_model=ToolsListResponse,
            )
        },
        "/copilot/agent/plan": {
            "post": _operation(
                components,
                path="/copilot/agent/plan",
                summary="建立 Copilot agent 計畫",
                request_body={
                    "required": True,
                    "content": _json_content(
                        _register_inline_schema(components, "CopilotAgentPlanRequest", components["CopilotAgentPlanRequest"])
                    ),
                },
                responses={
                    "200": _response_entry(
                        components,
                        "Agent 規劃結果",
                        content=_json_content(
                            _register_inline_schema(components, "CopilotGenericResponse", components["CopilotGenericResponse"])
                        ),
                    )
                },
            )
        },
        "/copilot/agent/execute": {
            "post": _operation(
                components,
                path="/copilot/agent/execute",
                summary="執行 Copilot agent 計畫",
                request_body={
                    "required": True,
                    "content": _json_content(
                        _register_inline_schema(components, "CopilotAgentExecuteRequest", components["CopilotAgentExecuteRequest"])
                    ),
                },
                responses={
                    "200": _response_entry(
                        components,
                        "Agent 執行結果",
                        content=_json_content(
                            _register_inline_schema(components, "CopilotGenericResponse", components["CopilotGenericResponse"])
                        ),
                    )
                },
            )
        },
        "/copilot/agent/reject": {
            "post": _operation(
                components,
                path="/copilot/agent/reject",
                summary="拒絕 Copilot agent 計畫",
                request_body={
                    "required": True,
                    "content": _json_content(
                        _register_inline_schema(components, "CopilotAgentRejectRequest", components["CopilotAgentRejectRequest"])
                    ),
                },
                responses={
                    "200": _response_entry(
                        components,
                        "Agent 拒絕結果",
                        content=_json_content(
                            _register_inline_schema(components, "CopilotGenericResponse", components["CopilotGenericResponse"])
                        ),
                    )
                },
            )
        },
        "/copilot/agent/replan": {
            "post": _operation(
                components,
                path="/copilot/agent/replan",
                summary="重新規劃 Copilot agent 計畫",
                request_body={
                    "required": True,
                    "content": _json_content(
                        _register_inline_schema(components, "CopilotAgentReplanRequest", components["CopilotAgentReplanRequest"])
                    ),
                },
                responses={
                    "200": _response_entry(
                        components,
                        "Agent 重規劃結果",
                        content=_json_content(
                            _register_inline_schema(components, "CopilotGenericResponse", components["CopilotGenericResponse"])
                        ),
                    )
                },
            )
        },
    }

    return {
        "openapi": OPENAPI_VERSION,
        "info": {
            "title": "Learnlink Backend API",
            "version": API_VERSION,
        },
        "servers": [{"url": "/api"}],
        "tags": [
            {"name": "health"},
            {"name": "auth"},
            {"name": "profile"},
            {"name": "tasks"},
            {"name": "timelines"},
            {"name": "knowledge"},
            {"name": "groups"},
            {"name": "messages"},
            {"name": "notifications"},
            {"name": "todos"},
            {"name": "trash"},
            {"name": "copilot"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            },
            "schemas": components,
        },
        "paths": paths,
    }


def export_openapi_document(output_path: str | Path = DEFAULT_OUTPUT_PATH) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_openapi_document(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
