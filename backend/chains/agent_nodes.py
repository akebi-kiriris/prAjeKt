from __future__ import annotations

import re
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


def _compact_defaults(defaults: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in defaults.items()
        if value is not None and value != ""
    }


def _merge_dict_defaults(existing: Any, defaults: dict[str, Any]) -> Any:
    compact_defaults = _compact_defaults(defaults)
    if isinstance(existing, dict):
        return {**compact_defaults, **existing}
    if existing is None:
        return compact_defaults
    return existing


def _extract_task_name(user_message: str) -> str | None:
    text = user_message.strip()
    if not text:
        return None
    marker = "叫做"
    if marker in text:
        after = text.split(marker, 1)[1].strip()
        for stop in ("的任務", "任務", "，", ",", "並且", "並"):
            if stop in after:
                name = after.split(stop, 1)[0].strip()
                if name:
                    return name
        if after:
            return after
    return None


def _build_create_task_defaults(state: AgentState) -> dict[str, Any]:
    user_message = state.get("user_message", "")
    defaults = {
        "name": _extract_task_name(user_message),
        "task_remark": user_message,
        "priority": 2,
        "status": "pending",
    }
    return _compact_defaults(defaults)


def _build_update_task_defaults(state: AgentState) -> dict[str, Any]:
    payloads = state.get("tool_payloads", {})
    raw_conflict_payload = payloads.get("check_timeline_task_conflicts", {})
    conflict_payload = raw_conflict_payload.get("payload") if isinstance(raw_conflict_payload, dict) else None
    if not isinstance(conflict_payload, dict):
        return {}
    defaults = {
        "name": conflict_payload.get("name"),
        "priority": conflict_payload.get("priority"),
        "start_date": conflict_payload.get("start_date"),
        "end_date": conflict_payload.get("end_date"),
    }
    return _compact_defaults(defaults)


def _build_conflict_payload_defaults(state: AgentState) -> dict[str, Any]:
    context = state.get("context", {})
    payloads = state.get("tool_payloads", {})
    raw_update_payload = payloads.get("update_task_for_member", {})
    update_task_id = raw_update_payload.get("task_id") if isinstance(raw_update_payload, dict) else None
    update_data = raw_update_payload.get("data") if isinstance(raw_update_payload, dict) else None

    defaults = {
        "task_id": update_task_id or context.get("task_id"),
        "name": update_data.get("name") if isinstance(update_data, dict) else None,
        "priority": update_data.get("priority") if isinstance(update_data, dict) else None,
        "start_date": update_data.get("start_date") if isinstance(update_data, dict) else None,
        "end_date": update_data.get("end_date") if isinstance(update_data, dict) else None,
    }
    return _compact_defaults(defaults)


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
        payload["data"] = _merge_dict_defaults(payload.get("data"), _build_create_task_defaults(state))
    elif tool_name == "update_task_for_member":
        payload.setdefault("actor_user_id", context.get("user_id"))
        payload.setdefault("task_id", context.get("task_id"))
        payload["data"] = _merge_dict_defaults(payload.get("data"), _build_update_task_defaults(state))
    elif tool_name == "check_timeline_task_conflicts":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault("actor_user_id", context.get("user_id"))
        payload["payload"] = _merge_dict_defaults(payload.get("payload"), _build_conflict_payload_defaults(state))
    elif tool_name == "generate_timeline_tasks_with_ai":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault(
            "project_name",
            state.get("created_timeline_name")
            or context.get("timeline_name")
            or _extract_project_name(state.get("user_message", "")),
        )
        payload.setdefault("description", state.get("user_message", ""))
    elif tool_name == "create_timeline_for_user":
        payload.setdefault("user_id", context.get("user_id"))
        payload["data"] = _merge_dict_defaults(payload.get("data"), {
            "name": _extract_project_name(state.get("user_message", "")),
            "remark": state.get("user_message", ""),
            "start_date": "",
            "end_date": "",
        })
    elif tool_name == "batch_create_tasks_for_timeline":
        payload.setdefault("timeline_id", effective_timeline_id)
        payload.setdefault("user_id", context.get("user_id"))
        generated_tasks = _extract_generated_tasks_from_state(state)
        existing_tasks = payload.get("tasks")
        if existing_tasks is None:
            payload["tasks"] = generated_tasks
        elif isinstance(existing_tasks, list):
            if len(existing_tasks) == 0 and generated_tasks:
                payload["tasks"] = generated_tasks
        elif generated_tasks:
            payload["tasks"] = generated_tasks
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

    normalized = text.lower()
    if "langgraph" in normalized and any(token in text for token in ("學習", "計畫", "規劃")):
        return "LangGraph 學習計畫"

    learning_plan_match = re.search(
        r"學習\s*([A-Za-z0-9_./+#\-一-龥]+)\s*的?(?:計畫|規劃)",
        text,
        flags=re.IGNORECASE,
    )
    if learning_plan_match:
        topic = learning_plan_match.group(1).strip()
        if topic:
            return f"{topic} 學習計畫"

    topic_match = re.search(
        r"(?:關於|針對)\s*([A-Za-z0-9_./+#\-一-龥]+)\s*的專案",
        text,
        flags=re.IGNORECASE,
    )
    if topic_match:
        topic = topic_match.group(1).strip()
        if topic:
            return f"{topic} 專案"

    return "新專案"


def _extract_generated_tasks_from_state(state: AgentState) -> list[dict[str, Any]]:
    steps = state.get("steps", [])
    for step in reversed(steps):
        if not isinstance(step, dict):
            continue
        if step.get("tool_name") != "generate_timeline_tasks_with_ai":
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


def _extract_new_tasks_from_step(step: dict[str, Any]) -> list[dict[str, Any]]:
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


def _build_success_final_answer(state: AgentState) -> str:
    steps = state.get("steps", [])
    timeline_name = ""
    created_count: int | None = None
    generated_tasks: list[dict[str, Any]] = []

    for step in steps:
        if not isinstance(step, dict):
            continue
        tool_name = step.get("tool_name")
        if tool_name == "create_timeline_for_user":
            input_data = step.get("input", {}).get("data", {}) if isinstance(step.get("input"), dict) else {}
            if isinstance(input_data, dict):
                timeline_name = str(input_data.get("name") or "").strip() or timeline_name
        elif tool_name == "generate_timeline_tasks_with_ai":
            generated_tasks = _extract_new_tasks_from_step(step)
        elif tool_name == "batch_create_tasks_for_timeline":
            output = step.get("output", {})
            data = output.get("data", {}) if isinstance(output, dict) else {}
            result = data.get("result", {}) if isinstance(data, dict) else {}
            if isinstance(result, dict) and isinstance(result.get("created"), int):
                created_count = result.get("created")

    if created_count is not None:
        if timeline_name:
            return f"已建立專案「{timeline_name}」，並批次建立 {created_count} 個任務。"
        return f"已批次建立 {created_count} 個任務。"

    if generated_tasks:
        task_names = [
            str(item.get("name") or "").strip()
            for item in generated_tasks
            if str(item.get("name") or "").strip()
        ]
        preview = "、".join(task_names[:3])
        generated_count = len(task_names)
        if timeline_name and preview:
            return (
                f"已建立專案「{timeline_name}」，AI 另外產生了 {generated_count} 個任務建議，"
                f"例如：{preview}。"
            )
        if timeline_name:
            return f"已建立專案「{timeline_name}」，AI 另外產生了 {generated_count} 個任務建議。"
        if preview:
            return f"AI 已產生 {generated_count} 個任務建議，例如：{preview}。"
        return f"AI 已產生 {generated_count} 個任務建議。"

    if timeline_name:
        return f"已建立專案「{timeline_name}」。"

    return "任務已完成，已依序執行工具流程。"


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
        created_timeline_name = state.get("created_timeline_name")
        if tool_name == "create_timeline_for_user":
            payload_data = result.get("data", {})
            if isinstance(payload_data, dict):
                created_timeline_id = payload_data.get("timeline_id")
            input_data = payload.get("data", {})
            if isinstance(input_data, dict):
                created_timeline_name = str(input_data.get("name") or "").strip() or created_timeline_name
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
            "created_timeline_name": created_timeline_name,
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

    last_step = steps[-1] if isinstance(steps[-1], dict) else {}
    last = last_step.get("output", {}) if isinstance(last_step, dict) else {}
    if state.get("unsupported_goal"):
        return {"final_answer": "目前工具白名單尚未支援此目標（例如建立專案或依賴鍊規劃）。請先改為可用工具範圍，或擴充對應工具後再試。"}
    if state.get("requires_write"):
        has_write_tool = any(
            isinstance(step, dict) and step.get("tool_name") in {
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
        return {"final_answer": _build_success_final_answer(state)}
    error = last.get("error", {})
    return {"final_answer": error.get("message", "執行未完成。")}
