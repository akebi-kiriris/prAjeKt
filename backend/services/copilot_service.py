import json
import re
from typing import Any

from services.ai_provider import get_ai_provider
from services.mcp_bridge_service import MCPBridgeError, execute_mcp_tool, list_mcp_tools


class CopilotOperationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _strip_markdown_fence(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_first_json_object(text: str) -> str | None:
    if not isinstance(text, str):
        return None

    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        ch = text[idx]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start: idx + 1]

    return None


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fence(raw_text)
    if not cleaned:
        raise CopilotOperationError("AI 規劃結果為空，請再試一次。", 500)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    extracted = _extract_first_json_object(cleaned)
    if not extracted:
        raise CopilotOperationError("AI 規劃結果無法解析為 JSON。", 500)

    try:
        parsed = json.loads(extracted)
    except json.JSONDecodeError as exc:
        raise CopilotOperationError("AI 規劃結果格式錯誤。", 500) from exc

    if not isinstance(parsed, dict):
        raise CopilotOperationError("AI 規劃結果格式錯誤。", 500)

    return parsed


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
    tool_descriptions = []
    for tool in tools:
        name = str(tool.get("name") or "").strip()
        desc = str(tool.get("description") or "").strip()
        if name:
            tool_descriptions.append(f"- {name}: {desc}")

    if not tool_descriptions:
        raise CopilotOperationError("MCP 工具清單為空。", 500)

    system_prompt = (
        "你是 PrAjeKt 的工具路由器。"
        "你只能從提供的工具中選一個最適合的工具，"
        "輸出必須是 JSON 物件。"
    )

    user_prompt = f"""
可用工具：
{chr(10).join(tool_descriptions)}

目前上下文（可能有部分為 null）：
- timeline_id: {context.get('timeline_id')}
- timeline_name: {context.get('timeline_name')}
- task_id: {context.get('task_id')}
- group_id: {context.get('group_id')}

使用者需求：
{user_message}

請只輸出 JSON 物件，格式：
{{
  "tool_name": "工具名稱",
  "arguments": {{ "參數": "值" }},
  "reason": "20字內說明"
}}
""".strip()

    try:
        provider = get_ai_provider()
        raw_text = provider.generate_content(system_prompt, user_prompt, response_format="json")
        parsed = _parse_json_object(raw_text)

        tool_name = str(parsed.get("tool_name") or "").strip()
        arguments = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}

        if not tool_name:
            raise CopilotOperationError("AI 沒有選出工具。", 500)

        return tool_name, arguments, "ai_planner"
    except Exception:
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
