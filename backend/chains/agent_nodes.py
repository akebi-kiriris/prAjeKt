from __future__ import annotations

from typing import Any

from chains.agent_state import AgentState
from services.tools.error_mapper import route_from_tool_error
from services.tools.registry import execute_registered_tool

PROTECTED_CONTEXT_KEYS = {
    "user_id",
    "actor_user_id",
    "created_by",
    "timeline_id",
    "task_id",
    "group_id",
}


def _sanitize_user_payload(raw_payload: dict[str, Any]) -> dict[str, Any]:
    """移除不可由外部覆蓋的敏感欄位。"""
    sanitized = dict(raw_payload)
    for key in PROTECTED_CONTEXT_KEYS:
        sanitized.pop(key, None)
    return sanitized


def _build_payload(tool_name: str, state: AgentState) -> dict[str, Any]:
    context = state.get("context", {})
    payloads = state.get("tool_payloads", {})
    payload = _sanitize_user_payload(dict(payloads.get(tool_name, {})))

    created_timeline_id = state.get("created_timeline_id")
    effective_timeline_id = created_timeline_id or context.get("timeline_id")

    if tool_name == "list_tasks_for_user":
        payload.setdefault("user_id", context.get("user_id"))
    elif tool_name == "create_task_for_user":
        payload.setdefault("user_id", context.get("user_id"))
    elif tool_name == "check_timeline_task_conflicts":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault("actor_user_id", context.get("user_id"))
    elif tool_name == "generate_timeline_tasks_with_ai":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault("project_name", context.get("timeline_name", ""))
        payload.setdefault("description", state.get("user_message", ""))
    elif tool_name == "create_timeline_for_user":
        payload.setdefault("user_id", context.get("user_id"))
        payload.setdefault(
            "data",
            {
                "name": _extract_project_name(state.get("user_message", "")),
                "remark": state.get("user_message", ""),
                "start_date": "",
                "end_date": "",
            },
        )
    elif tool_name == "batch_create_tasks_for_timeline":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault("user_id", context.get("user_id"))
        payload.setdefault("tasks", _extract_generated_tasks_from_state(state))
    elif tool_name == "generate_group_snapshot":
        payload.setdefault("group_id", context.get("group_id"))
        payload.setdefault("created_by", context.get("user_id"))
    elif tool_name == "upload_and_index_knowledge_document":
        payload.setdefault("user_id", context.get("user_id"))
    elif tool_name == "list_knowledge_documents":
        payload.setdefault("user_id", context.get("user_id"))
    elif tool_name == "summarize_task_comments_for_member":
        payload.setdefault("task_id", context.get("task_id"))

    return payload


def build_pending_tools(user_message: str) -> list[str]:
    text = (user_message or "").lower()

    if ("專案" in text) and any(token in text for token in ("建立", "新增", "創建")):
        return [
            "create_timeline_for_user",
            "generate_timeline_tasks_with_ai",
            "batch_create_tasks_for_timeline",
        ]

    if any(token in text for token in ("建立", "新增", "創建")) and "任務" in text:
        return ["list_tasks_for_user", "create_task_for_user"]
    if any(token in text for token in ("更新", "修改")) and "任務" in text and "衝突" in text:
        return [
            "list_tasks_for_user",
            "check_timeline_task_conflicts",
            "update_task_for_member",
        ]
    if any(token in text for token in ("更新", "修改")) and "任務" in text:
        return ["list_tasks_for_user", "update_task_for_member"]
    if "衝突" in text:
        return ["list_tasks_for_user", "check_timeline_task_conflicts"]
    if any(token in text for token in ("留言", "摘要")):
        return ["list_tasks_for_user", "summarize_task_comments_for_member"]
    if any(token in text for token in ("知識", "文件")) and any(token in text for token in ("上傳", "索引")):
        return ["upload_and_index_knowledge_document", "list_knowledge_documents"]
    if "快照" in text and "群組" in text:
        return ["generate_group_snapshot"]
    return []


def _requires_write_operation(user_message: str) -> bool:
    text = (user_message or "").lower()
    return any(token in text for token in ("建立", "新增", "創建", "更新", "修改", "刪除", "指派"))


def _is_unsupported_goal(user_message: str) -> bool:
    text = (user_message or "").strip().lower()
    if not text:
        return True
    supported_keywords = (
        "任務",
        "專案",
        "時間軸",
        "衝突",
        "留言",
        "摘要",
        "群組",
        "快照",
        "知識",
        "文件",
    )
    return not any(keyword in text for keyword in supported_keywords)


def _extract_project_name(user_message: str) -> str:
    text = user_message.strip()
    if not text:
        return "新專案"
    marker = "叫做"
    if marker in text:
        after = text.split(marker, 1)[1].strip()
        for stop in ("的專案", "專案", "，", ",", "並且", "並"):
            if stop in after:
                name = after.split(stop, 1)[0].strip()
                if name:
                    return name
        if after:
            return after
    return "新專案"


def _extract_generated_tasks_from_state(state: AgentState) -> list[dict[str, Any]]:
    steps = state.get("steps", [])
    for step in reversed(steps):
        if step["tool_name"] != "generate_timeline_tasks_with_ai":
            continue
        output = step.get("output", {})
        data = output.get("data", {}) if isinstance(output, dict) else {}
        tasks = data.get("tasks", []) if isinstance(data, dict) else []
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
    return []


def intent_parse_node(state: AgentState) -> AgentState:
    user_message = state.get("user_message", "")
    unsupported_goal = _is_unsupported_goal(user_message)
    if unsupported_goal:
        return {
            "pending_tools": [],
            "executed_tools": state.get("executed_tools", []),
            "steps": state.get("steps", []),
            "retry_count": state.get("retry_count", 0),
            "loop_count": state.get("loop_count", 0),
            "max_loops": state.get("max_loops", 6),
            "requires_write": _requires_write_operation(user_message),
            "unsupported_goal": True,
            "route": "stop",
            "ask_user_message": "目前尚未支援此類需求，請改為任務/專案/群組/知識庫相關操作。",
        }

    pending = state.get("pending_tools") or build_pending_tools(user_message)
    if not pending:
        return {
            "pending_tools": [],
            "executed_tools": state.get("executed_tools", []),
            "steps": state.get("steps", []),
            "retry_count": state.get("retry_count", 0),
            "loop_count": state.get("loop_count", 0),
            "max_loops": state.get("max_loops", 6),
            "requires_write": _requires_write_operation(user_message),
            "unsupported_goal": False,
            "route": "stop",
            "ask_user_message": "目前白名單尚未提供這個操作，請改述為可用工具範圍或擴充工具。",
        }
    return {
        "pending_tools": pending,
        "executed_tools": state.get("executed_tools", []),
        "steps": state.get("steps", []),
        "retry_count": state.get("retry_count", 0),
        "loop_count": state.get("loop_count", 0),
        "max_loops": state.get("max_loops", 6),
        "requires_write": _requires_write_operation(user_message),
        "unsupported_goal": unsupported_goal,
        "route": "continue",
    }


def tool_select_node(state: AgentState) -> AgentState:
    if state.get("route") == "stop":
        return {"route": "stop", "ask_user_message": state.get("ask_user_message", "執行中止。")}

    pending = state.get("pending_tools", [])
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", 6)
    if loop_count >= max_loops:
        return {"route": "stop", "ask_user_message": "超過最大執行步數，已停止。"}
    if not pending:
        return {"route": "finalize"}
    return {"route": "continue"}


def tool_execute_node(state: AgentState) -> AgentState:
    pending = list(state.get("pending_tools", []))
    if not pending:
        return {"route": "finalize"}

    tool_name = pending.pop(0)
    payload = _build_payload(tool_name, state)
    result = execute_registered_tool(tool_name, payload)

    step = {
        "tool_name": tool_name,
        "input": payload,
        "output": result,
    }
    steps = list(state.get("steps", []))
    steps.append(step)
    executed_tools = list(state.get("executed_tools", []))
    executed_tools.append(tool_name)

    if result.get("ok") is True:
        created_timeline_id = state.get("created_timeline_id")
        if tool_name == "create_timeline_for_user":
            payload_data = result.get("data", {})
            if isinstance(payload_data, dict):
                created_timeline_id = payload_data.get("timeline_id")
        return {
            "pending_tools": pending,
            "executed_tools": executed_tools,
            "steps": steps,
            "last_result": result,
            "last_error": {},
            "route": "continue",
            "loop_count": state.get("loop_count", 0) + 1,
            "retry_count": 0,
            "created_timeline_id": created_timeline_id,
        }

    error = result.get("error", {})
    return {
        "pending_tools": [tool_name] + pending,
        "executed_tools": executed_tools,
        "steps": steps,
        "last_error": error,
        "route": "continue",
        "loop_count": state.get("loop_count", 0) + 1,
    }


def route_by_error_node(state: AgentState) -> AgentState:
    last_error = state.get("last_error") or {}
    if not last_error:
        return {"route": "continue"}

    retry_count = state.get("retry_count", 0)
    route = route_from_tool_error(error=last_error, retry_count=retry_count, retry_limit=2)
    if route == "retry":
        return {"route": "continue", "retry_count": retry_count + 1}
    if route == "ask_user":
        return {"route": "ask_user", "ask_user_message": last_error.get("hint", "請補充必要資訊。")}
    return {"route": "stop", "ask_user_message": last_error.get("message", "系統暫停執行。")}


def finalize_node(state: AgentState) -> AgentState:
    steps = state.get("steps", [])
    if state.get("route") == "ask_user":
        return {"final_answer": state.get("ask_user_message", "請補充資訊後再試。")}
    if state.get("route") == "stop":
        return {"final_answer": state.get("ask_user_message", "執行中止。")}
    if not steps:
        return {"final_answer": "目前沒有可執行的工具步驟。"}

    last = steps[-1]["output"]
    if state.get("unsupported_goal"):
        return {"final_answer": "目前工具白名單尚未支援此目標（例如建立專案或依賴鍊規劃）。請先改為可用工具範圍，或擴充對應工具後再試。"}
    if state.get("requires_write"):
        has_write_tool = any(
            step["tool_name"] in {
                "create_task_for_user",
                "update_task_for_member",
                "upload_and_index_knowledge_document",
                "generate_group_snapshot",
                "create_timeline_for_user",
                "batch_create_tasks_for_timeline",
            }
            for step in steps
        )
        if not has_write_tool:
            return {"final_answer": "目前只完成查詢工具，尚未執行任何寫入操作；請補充可建立/更新所需資訊。"}
    if last.get("ok"):
        return {"final_answer": "任務已完成，已依序執行工具流程。"}
    error = last.get("error", {})
    return {"final_answer": error.get("message", "執行未完成。")}
