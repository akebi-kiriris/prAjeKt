from typing import Any

from chains import get_default_llm, select_tools
from services.mcp_bridge_service import MCPBridgeError, execute_mcp_tool, list_mcp_tools


class CopilotOperationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_context(context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(context, dict):
        return {}

    normalized = dict(context)
    for key in ("timeline_id", "task_id", "group_id"):
        converted = _to_int(normalized.get(key))
        if converted is not None:
            normalized[key] = converted
    return normalized


def _keyword_select_tool(
    user_message: str,
    context: dict[str, Any],
    tool_names: set[str],
) -> tuple[str, dict[str, Any], str]:
    message = (user_message or "").lower()

    if "timeline_generate_tasks" in tool_names and any(token in message for token in ("生成", "拆解", "規劃", "任務")):
        timeline_id = _to_int(context.get("timeline_id"))
        if timeline_id is None:
            raise CopilotOperationError("需要 timeline_id 才能生成任務。", 400)
        return (
            "timeline_generate_tasks",
            {
                "timeline_id": timeline_id,
                "project_name": str(context.get("timeline_name") or "").strip(),
                "description": user_message,
            },
            "keyword_fallback",
        )

    if "task_comment_summary" in tool_names and any(token in message for token in ("摘要", "留言", "comment")):
        task_id = _to_int(context.get("task_id"))
        if task_id is None:
            raise CopilotOperationError("需要 task_id 才能做留言摘要。", 400)
        return ("task_comment_summary", {"task_id": task_id}, "keyword_fallback")

    if "group_snapshot" in tool_names and any(token in message for token in ("群組", "快照", "snapshot")):
        group_id = _to_int(context.get("group_id"))
        if group_id is None:
            raise CopilotOperationError("需要 group_id 才能做群組快照。", 400)
        return (
            "group_snapshot",
            {
                "group_id": group_id,
                "window_days": 30,
                "async_mode": False,
                "wait_for_job": True,
            },
            "keyword_fallback",
        )

    raise CopilotOperationError(
        "無法判斷要呼叫哪個工具。請補充需求，或指定 preferred_tool。",
        400,
    )


def _ai_select_tool(
    user_message: str,
    context: dict[str, Any],
    tools: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], str]:
    available_tools: list[dict[str, str]] = []
    for tool in tools:
        name = str(tool.get("name") or "").strip()
        desc = str(tool.get("description") or "").strip()
        if name:
            available_tools.append({"name": name, "description": desc})

    if not available_tools:
        raise CopilotOperationError("MCP 工具清單為空。", 500)

    try:
        llm = get_default_llm(provider="google-generativeai")
        parsed = select_tools(
            llm=llm,
            user_input=user_message,
            available_tools=available_tools,
            context=context,
        )

        tool_name = str(parsed.get("tool_name") or "").strip()
        arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}

        if not tool_name:
            raise CopilotOperationError("AI 沒有選出工具。", 500)

        return tool_name, arguments, "ai_planner"
    except (RuntimeError, ValueError, CopilotOperationError):
        tool_names = {str(tool.get("name") or "") for tool in tools}
        return _keyword_select_tool(user_message, context, tool_names)


def _build_arguments(
    selected_tool: str,
    ai_arguments: dict[str, Any],
    context: dict[str, Any],
    user_message: str,
    preferred_arguments: dict[str, Any],
) -> dict[str, Any]:
    merged = {}
    merged.update(ai_arguments)
    merged.update(preferred_arguments)

    if selected_tool == "task_comment_summary":
        task_id = _to_int(merged.get("task_id")) or _to_int(context.get("task_id"))
        if task_id is None:
            raise CopilotOperationError("缺少 task_id，無法做留言摘要。", 400)
        return {"task_id": task_id}

    if selected_tool == "group_snapshot":
        group_id = _to_int(merged.get("group_id")) or _to_int(context.get("group_id"))
        if group_id is None:
            raise CopilotOperationError("缺少 group_id，無法做群組快照。", 400)

        window_days = _to_int(merged.get("window_days")) or 30
        async_mode = bool(merged.get("async_mode", False))
        wait_for_job = bool(merged.get("wait_for_job", True))
        return {
            "group_id": group_id,
            "window_days": max(window_days, 1),
            "async_mode": async_mode,
            "wait_for_job": wait_for_job,
        }

    if selected_tool == "timeline_generate_tasks":
        timeline_id = _to_int(merged.get("timeline_id")) or _to_int(context.get("timeline_id"))
        if timeline_id is None:
            raise CopilotOperationError("缺少 timeline_id，無法生成任務。", 400)

        project_name = str(
            merged.get("project_name")
            or context.get("timeline_name")
            or ""
        ).strip()
        description = str(
            merged.get("description")
            or user_message
            or ""
        ).strip()

        return {
            "timeline_id": timeline_id,
            "project_name": project_name,
            "description": description,
        }

    if selected_tool == "timeline_batch_create_tasks":
        timeline_id = _to_int(merged.get("timeline_id")) or _to_int(context.get("timeline_id"))
        tasks = merged.get("tasks")
        if timeline_id is None or not isinstance(tasks, list) or len(tasks) == 0:
            raise CopilotOperationError("缺少 timeline_id 或 tasks，無法批次建立任務。", 400)
        return {
            "timeline_id": timeline_id,
            "tasks": tasks,
        }

    return merged


def _normalize_batch_task(task: dict[str, Any]) -> dict[str, Any]:
    if task.get("isExisting") and _to_int(task.get("task_id")):
        return {
            "isExisting": True,
            "task_id": int(task["task_id"]),
        }

    name = str(task.get("name") or "未命名任務").strip() or "未命名任務"
    priority = _to_int(task.get("priority")) or 2
    estimated_days = _to_int(task.get("estimated_days")) or 3
    remark = str(task.get("task_remark") or task.get("remark") or "").strip()

    return {
        "isExisting": False,
        "name": name,
        "priority": min(max(priority, 1), 3),
        "estimated_days": max(estimated_days, 1),
        "task_remark": remark,
    }


def _extract_generate_tasks_payload(tool_result: Any) -> list[dict[str, Any]]:
    if not isinstance(tool_result, dict):
        return []

    tasks = tool_result.get("tasks")
    if not isinstance(tasks, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in tasks:
        if isinstance(item, dict):
            normalized.append(_normalize_batch_task(item))
    return normalized


def _extract_only_generated_tasks(tool_result: Any) -> list[dict[str, Any]]:
    if not isinstance(tool_result, dict):
        return []

    tasks = tool_result.get("tasks")
    if not isinstance(tasks, list):
        return []

    generated: list[dict[str, Any]] = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        if item.get("isExisting"):
            continue
        generated.append(item)
    return generated


def execute_copilot_mcp_request(
    user_message: str,
    context: dict[str, Any] | None = None,
    preferred_tool: str | None = None,
    tool_arguments: dict[str, Any] | None = None,
    auto_create_generated_tasks: bool = False,
    access_token: str | None = None,
) -> dict[str, Any]:
    message = (user_message or "").strip()
    if not message:
        raise CopilotOperationError("message 不可為空。", 400)

    normalized_context = _normalize_context(context)
    preferred_arguments = tool_arguments if isinstance(tool_arguments, dict) else {}

    try:
        tools = list_mcp_tools(access_token=access_token)
    except MCPBridgeError as exc:
        raise CopilotOperationError(f"讀取 MCP 工具失敗：{exc.message}", exc.status_code) from exc

    tool_names = {str(tool.get("name") or "") for tool in tools}

    if preferred_tool:
        selected_tool = str(preferred_tool).strip()
        if selected_tool not in tool_names:
            raise CopilotOperationError(f"找不到指定工具：{selected_tool}", 400)
        selected_arguments = {}
        selection_source = "preferred_tool"
    else:
        selected_tool, selected_arguments, selection_source = _ai_select_tool(message, normalized_context, tools)
        if selected_tool not in tool_names:
            raise CopilotOperationError(f"AI 選擇了不存在的工具：{selected_tool}", 500)

    final_arguments = _build_arguments(
        selected_tool,
        selected_arguments,
        normalized_context,
        message,
        preferred_arguments,
    )

    try:
        execution = execute_mcp_tool(selected_tool, final_arguments, access_token=access_token)
    except MCPBridgeError as exc:
        raise CopilotOperationError(exc.message, exc.status_code) from exc

    result = execution.get("parsed_result")
    response_payload: dict[str, Any] = {
        "message": "Copilot 已透過 MCP 執行工具",
        "selected_tool": selected_tool,
        "selection_source": selection_source,
        "arguments": final_arguments,
        "result": result,
    }

    if selected_tool == "timeline_generate_tasks":
        response_payload["generated_tasks"] = _extract_only_generated_tasks(result)

        if auto_create_generated_tasks:
            batch_payload = _extract_generate_tasks_payload(result)
            if not batch_payload:
                response_payload["auto_create_result"] = {
                    "message": "沒有可建立的新任務。",
                    "created": 0,
                }
                return response_payload

            timeline_id = _to_int(final_arguments.get("timeline_id"))
            if timeline_id is None:
                raise CopilotOperationError("缺少 timeline_id，無法自動建立任務。", 400)

            try:
                auto_created = execute_mcp_tool(
                    "timeline_batch_create_tasks",
                    {
                        "timeline_id": timeline_id,
                        "tasks": batch_payload,
                    },
                    access_token=access_token,
                )
            except MCPBridgeError as exc:
                raise CopilotOperationError(exc.message, exc.status_code) from exc

            response_payload["auto_create_result"] = auto_created.get("parsed_result")

    return response_payload
