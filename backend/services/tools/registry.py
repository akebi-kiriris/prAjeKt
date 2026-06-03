from dataclasses import dataclass
import os
import warnings
from typing import Any, Callable

from services.contracts.tool_envelopes import make_failure
from services.tools.error_mapper import map_exception_to_tool_error
from services.contracts.tool_inputs import (
    CreateTimelineToolInput,
    CreateTaskToolInput,
    GroupSnapshotToolInput,
    KnowledgeListToolInput,
    KnowledgeUploadToolInput,
    ListTasksToolInput,
    TaskCommentSummaryToolInput,
    TimelineConflictCheckToolInput,
    TimelineBatchCreateTasksToolInput,
    TimelineGenerateTasksToolInput,
    UpdateTaskToolInput,
)
from services.tools.handlers import (
    handle_check_timeline_task_conflicts,
    handle_batch_create_tasks_for_timeline,
    handle_create_timeline_for_user,
    handle_create_task_for_user,
    handle_generate_group_snapshot,
    handle_generate_timeline_tasks_with_ai,
    handle_list_knowledge_documents,
    handle_list_tasks_for_user,
    handle_summarize_task_comments_for_member,
    handle_update_task_for_member,
    handle_upload_and_index_knowledge_document,
)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str | None
    input_model: type
    handler: Callable[[Any], dict[str, Any]]
    side_effects: str
    side_effect_level: str
    user_visible_label: str
    requires_confirmation: bool
    permission_note: str


def _derive_description(handler: Callable[[dict[str, Any]], dict[str, Any]], override: str | None = None) -> str:
    """推導工具描述文字。

    Args:
        handler: 工具對應的處理函式。
        override: 可選的覆寫描述。

    Returns:
        str: 最終描述文字。
    """
    if isinstance(override, str) and override.strip():
        return override.strip()
    doc = (handler.__doc__ or "").strip()
    if not doc:
        return "（未提供工具描述）"
    return doc.split("\n\n", 1)[0].strip()


def _is_strict_docstring_mode() -> bool:
    """判斷是否啟用 docstring 嚴格模式。"""
    value = str(os.getenv("PRAJEKT_TOOL_DOCSTRING_STRICT", "")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _ensure_tool_docstring_quality() -> None:
    """檢查工具處理函式 docstring 是否符合最小契約。

    規則:
        1. 缺 docstring 時：
           - strict mode: 拋出 ValueError
           - 非 strict mode: 發出 warning
    """
    missing: list[str] = []
    for name, definition in TOOL_REGISTRY.items():
        if isinstance(definition.description, str) and definition.description.strip():
            continue
        doc = (definition.handler.__doc__ or "").strip()
        if not doc:
            missing.append(name)

    if not missing:
        return

    joined = ", ".join(missing)
    message = f"以下工具缺少 docstring 描述：{joined}"
    if _is_strict_docstring_mode():
        raise ValueError(message)
    warnings.warn(message, UserWarning, stacklevel=2)


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "create_task_for_user": ToolDefinition(
        name="create_task_for_user",
        description=None,
        input_model=CreateTaskToolInput,
        handler=handle_create_task_for_user,
        side_effects="write_db, notify",
        side_effect_level="high",
        user_visible_label="建立任務",
        requires_confirmation=True,
        permission_note="需可建立任務的使用者身分。",
    ),
    "update_task_for_member": ToolDefinition(
        name="update_task_for_member",
        description=None,
        input_model=UpdateTaskToolInput,
        handler=handle_update_task_for_member,
        side_effects="write_db",
        side_effect_level="high",
        user_visible_label="更新任務",
        requires_confirmation=True,
        permission_note="需具備任務更新權限。",
    ),
    "list_tasks_for_user": ToolDefinition(
        name="list_tasks_for_user",
        description=None,
        input_model=ListTasksToolInput,
        handler=handle_list_tasks_for_user,
        side_effects="read_db",
        side_effect_level="low",
        user_visible_label="查詢任務清單",
        requires_confirmation=False,
        permission_note="需為登入使用者本人上下文。",
    ),
    "generate_timeline_tasks_with_ai": ToolDefinition(
        name="generate_timeline_tasks_with_ai",
        description=None,
        input_model=TimelineGenerateTasksToolInput,
        handler=handle_generate_timeline_tasks_with_ai,
        side_effects="call_ai",
        side_effect_level="medium",
        user_visible_label="AI 生成任務草案",
        requires_confirmation=True,
        permission_note="需可讀取該專案脈絡。",
    ),
    "create_timeline_for_user": ToolDefinition(
        name="create_timeline_for_user",
        description=None,
        input_model=CreateTimelineToolInput,
        handler=handle_create_timeline_for_user,
        side_effects="write_db",
        side_effect_level="high",
        user_visible_label="建立專案",
        requires_confirmation=True,
        permission_note="需登入使用者身份。",
    ),
    "batch_create_tasks_for_timeline": ToolDefinition(
        name="batch_create_tasks_for_timeline",
        description=None,
        input_model=TimelineBatchCreateTasksToolInput,
        handler=handle_batch_create_tasks_for_timeline,
        side_effects="write_db",
        side_effect_level="high",
        user_visible_label="批次建立任務",
        requires_confirmation=True,
        permission_note="需專案成員權限。",
    ),
    "check_timeline_task_conflicts": ToolDefinition(
        name="check_timeline_task_conflicts",
        description=None,
        input_model=TimelineConflictCheckToolInput,
        handler=handle_check_timeline_task_conflicts,
        side_effects="read_db, optional_call_ai",
        side_effect_level="low",
        user_visible_label="檢查任務衝突",
        requires_confirmation=False,
        permission_note="需專案成員身份。",
    ),
    "generate_group_snapshot": ToolDefinition(
        name="generate_group_snapshot",
        description=None,
        input_model=GroupSnapshotToolInput,
        handler=handle_generate_group_snapshot,
        side_effects="read_db, write_db, call_ai",
        side_effect_level="high",
        user_visible_label="產生群組快照",
        requires_confirmation=True,
        permission_note="需具備群組成員權限。",
    ),
    "upload_and_index_knowledge_document": ToolDefinition(
        name="upload_and_index_knowledge_document",
        description=None,
        input_model=KnowledgeUploadToolInput,
        handler=handle_upload_and_index_knowledge_document,
        side_effects="write_db, call_embedding",
        side_effect_level="high",
        user_visible_label="上傳並索引知識文件",
        requires_confirmation=True,
        permission_note="需文件擁有者或專案授權。",
    ),
    "list_knowledge_documents": ToolDefinition(
        name="list_knowledge_documents",
        description=None,
        input_model=KnowledgeListToolInput,
        handler=handle_list_knowledge_documents,
        side_effects="read_db",
        side_effect_level="low",
        user_visible_label="查詢知識文件",
        requires_confirmation=False,
        permission_note="需文件讀取權限。",
    ),
    "summarize_task_comments_for_member": ToolDefinition(
        name="summarize_task_comments_for_member",
        description=None,
        input_model=TaskCommentSummaryToolInput,
        handler=handle_summarize_task_comments_for_member,
        side_effects="read_db, call_ai",
        side_effect_level="medium",
        user_visible_label="摘要任務留言",
        requires_confirmation=False,
        permission_note="需任務可見權限。",
    ),
}


def get_tool_definition(tool_name: str) -> ToolDefinition | None:
    """取得工具定義。"""
    return TOOL_REGISTRY.get(tool_name)


def list_registered_tools() -> list[dict[str, Any]]:
    """列出可提供給 agent 的工具白名單與契約摘要。

    Returns:
        list[dict[str, Any]]: 工具中繼資料清單（含描述、副作用、輸入 schema）。

    Raises:
        ValueError: strict mode 下發現缺少 docstring 的工具。
    """
    _ensure_tool_docstring_quality()
    return [
        {
            "name": tool.name,
            "description": _derive_description(tool.handler, tool.description),
            "side_effects": tool.side_effects,
            "side_effect_level": tool.side_effect_level,
            "user_visible_label": tool.user_visible_label,
            "requires_confirmation": tool.requires_confirmation,
            "permission_note": tool.permission_note,
            "input_schema": tool.input_model.model_json_schema(),
        }
        for tool in TOOL_REGISTRY.values()
    ]


def execute_registered_tool(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """執行單一註冊工具。

    Args:
        tool_name: 工具名稱。
        payload: 工具輸入參數。

    Returns:
        dict[str, Any]: 統一的工具回傳 envelope。
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {
            "ok": False,
            "error": {
                "error_code": "NOT_FOUND",
                "message": f"找不到工具：{tool_name}",
                "retryable": False,
                "hint": "請改用已註冊的工具名稱。",
            },
        }
    try:
        validated_payload = tool.input_model.model_validate(payload) if hasattr(tool.input_model, "model_validate") else payload
    except Exception as exc:
        return make_failure(map_exception_to_tool_error(exc))
    return tool.handler(validated_payload)
