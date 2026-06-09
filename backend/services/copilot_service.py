import logging
from typing import Any

from services.agent_plan_service import AgentPlanRecord, agent_plan_store
from services.mcp_bridge_service import MCPBridgeError, execute_mcp_tool, list_mcp_tools
from services.tool_plan_service import MAX_PLAN_STEPS, ToolPlanError, propose_plan_with_llm
from services.tools.registry import get_tool_definition
from services.tools.registry import list_registered_tools

logger = logging.getLogger(__name__)


class CopilotOperationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _serialize_plan(record: AgentPlanRecord) -> dict[str, Any]:
    return {
        "ok": True,
        "plan_id": record.plan_id,
        "status": record.status,
        "pending_tools": record.pending_tools,
        "summary": record.summary,
        "steps_preview": record.steps_preview,
        "risk_notes": record.risk_notes,
        "expires_at": record.expires_at.isoformat(),
        "proposal_source": record.proposal_source,
        "proposal_reason": record.proposal_reason,
    }


def _build_plan_preview(pending_tools: list[str]) -> tuple[list[str], list[str]]:
    steps_preview: list[str] = []
    risk_notes: list[str] = []

    for tool_name in pending_tools:
        tool = get_tool_definition(tool_name)
        if tool is None:
            steps_preview.append(f"執行工具：{tool_name}")
            risk_notes.append("包含未標註契約工具，請先確認流程。")
            continue
        steps_preview.append(tool.user_visible_label)
        if tool.requires_confirmation:
            risk_notes.append(f"包含可能改動資料的步驟：{tool.user_visible_label}")

    return steps_preview, list(dict.fromkeys(risk_notes))


def _build_plan_summary(user_message: str, steps_preview: list[str]) -> str:
    if not steps_preview:
        return "目前沒有可執行的步驟。"
    return f"目標「{user_message}」將依序執行：{', '.join(steps_preview)}。"


def _sanitize_tool_payloads(tool_payloads: dict[str, dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(tool_payloads, dict):
        return {}
    protected = {"user_id", "actor_user_id", "created_by", "timeline_id", "task_id", "group_id"}

    def _sanitize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: _sanitize_value(item)
                for key, item in value.items()
                if key not in protected
            }
        if isinstance(value, list):
            return [_sanitize_value(item) for item in value]
        return value

    sanitized: dict[str, dict[str, Any]] = {}
    for tool_name, payload in tool_payloads.items():
        if not isinstance(payload, dict):
            continue
        sanitized[tool_name] = _sanitize_value(dict(payload))
    return sanitized


def _merge_tool_payloads(
    *,
    incoming: dict[str, dict[str, Any]] | None,
    draft: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    merged = _sanitize_tool_payloads(incoming)
    if not isinstance(draft, dict):
        return merged
    for tool_name, payload in draft.items():
        if not isinstance(payload, dict):
            continue
        merged.setdefault(tool_name, {})
        merged[tool_name] = _deep_merge(
            merged[tool_name],
            _sanitize_tool_payloads({tool_name: payload}).get(tool_name, {}),
        )
    return merged


def _propose_pending_tools(
    *,
    user_message: str,
    context: dict[str, Any],
    force_model_proposal: bool,
) -> tuple[list[str], dict[str, dict[str, Any]], str, str | None]:
    available_tools = list_registered_tools()
    try:
        proposal = propose_plan_with_llm(
            user_message=user_message,
            context=context,
            tools=available_tools,
        )
        steps = [str(item).strip() for item in proposal.get("steps", []) if str(item).strip()]
        if not steps:
            raise ToolPlanError("模型未產出可執行步驟")
        planning_mode = str(proposal.get("planning_mode") or "").strip().lower()
        if (
            planning_mode == "plan_and_create_tasks"
            and "generate_timeline_tasks_with_ai" in steps
            and "batch_create_tasks_for_timeline" not in steps
        ):
            generate_index = steps.index("generate_timeline_tasks_with_ai")
            steps.insert(generate_index + 1, "batch_create_tasks_for_timeline")
        payload_draft = proposal.get("payload_draft", {})
        if not isinstance(payload_draft, dict):
            payload_draft = {}
        reason = str(proposal.get("reason") or "").strip() or None
        return steps, payload_draft, "llm_proposal", reason
    except ToolPlanError as exc:
        if force_model_proposal:
            raise CopilotOperationError(f"模型重規劃失敗：{exc.message}", 409) from exc
        from chains.agent_nodes import build_pending_tools

        fallback = build_pending_tools(user_message)
        return fallback, {}, "rule_fallback", f"模型提案失敗，改用規則：{exc.message}"


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
        from chains import get_default_llm, select_tools

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
    """Plan and execute one MCP tool call for copilot workflow.

    參數:
        user_message: End-user natural language instruction.
        context: 可選的執行期上下文（timeline/task/group ids）。
        preferred_tool: 可選的強制工具名稱。
        tool_arguments: 可選的明確工具參數。
        auto_create_generated_tasks: Whether to auto call batch-create after generation.
        access_token: 可選的 MCP 驗證轉傳權杖。

    回傳:
        Tool selection/execution payload including result and applied arguments.

    例外:
        CopilotOperationError: Tool selection, argument validation, or MCP execution failure.
    """
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


def create_copilot_agent_plan(
    user_message: str,
    *,
    user_id: int,
    context: dict[str, Any] | None = None,
    tool_payloads: dict[str, dict[str, Any]] | None = None,
    force_model_proposal: bool = False,
) -> dict[str, Any]:
    """建立 agent 執行計畫（不執行工具）。"""
    message = (user_message or "").strip()
    if not message:
        raise CopilotOperationError("message 不可為空。", 400)

    normalized_context = _normalize_context(context)
    pending_tools, payload_draft, proposal_source, proposal_reason = _propose_pending_tools(
        user_message=message,
        context=normalized_context,
        force_model_proposal=force_model_proposal,
    )
    if len(pending_tools) > MAX_PLAN_STEPS:
        raise CopilotOperationError(f"模型提案步驟不可超過 {MAX_PLAN_STEPS} 步。", 409)
    steps_preview, risk_notes = _build_plan_preview(pending_tools)
    summary = _build_plan_summary(message, steps_preview)

    record = agent_plan_store.create_plan(
        user_id=user_id,
        goal=message,
        context=normalized_context,
        approved_tool_payloads=_merge_tool_payloads(incoming=tool_payloads, draft=payload_draft),
        pending_tools=pending_tools,
        summary=summary,
        steps_preview=steps_preview,
        risk_notes=risk_notes,
        proposal_source=proposal_source,
        proposal_reason=proposal_reason,
    )
    logger.info(
        "copilot_agent_plan_created user_id=%s proposal_source=%s pending_tools=%s proposal_reason=%s",
        user_id,
        proposal_source,
        pending_tools,
        proposal_reason,
    )
    return _serialize_plan(record)


def reject_copilot_agent_plan(
    plan_id: str,
    *,
    user_id: int,
    reason: str | None = None,
) -> dict[str, Any]:
    """拒絕既有 agent 計畫。"""
    safe_plan_id = (plan_id or "").strip()
    if not safe_plan_id:
        raise CopilotOperationError("plan_id 不可為空。", 400)
    record = agent_plan_store.reject_plan(safe_plan_id, user_id=user_id, reason=reason)
    if record is None:
        raise CopilotOperationError("找不到對應計畫。", 404)
    if record.status == "expired":
        raise CopilotOperationError("計畫已過期，請重新規劃。", 409)
    return {
        "ok": True,
        "plan_id": record.plan_id,
        "status": record.status,
    }


def execute_copilot_agent_plan(
    *,
    plan_id: str,
    user_id: int,
    confirm: bool,
    tool_payloads: dict[str, dict[str, Any]] | None = None,
    max_loops: int = 6,
) -> dict[str, Any]:
    """執行已核准計畫。"""
    safe_plan_id = (plan_id or "").strip()
    if not safe_plan_id:
        raise CopilotOperationError("plan_id 不可為空。", 400)
    if not confirm:
        raise CopilotOperationError("未確認執行，請先確認。", 400)
    if isinstance(tool_payloads, dict) and len(tool_payloads) > 0:
        raise CopilotOperationError("已確認計畫不可再覆寫執行參數，請改用 replan。", 409)

    current = agent_plan_store.get_plan(safe_plan_id, user_id=user_id)
    if current is None:
        raise CopilotOperationError("找不到對應計畫。", 404)
    if current.status == "expired":
        raise CopilotOperationError("計畫已過期，請重新規劃。", 409)
    if current.status == "rejected":
        raise CopilotOperationError("此計畫已被拒絕，請重新規劃。", 409)
    if current.status == "succeeded":
        raise CopilotOperationError("此計畫已執行完成，不可重複執行。", 409)
    if current.status == "failed":
        raise CopilotOperationError("此計畫已執行失敗，請重新規劃後再試。", 409)
    if current.status == "executing":
        raise CopilotOperationError("此計畫正在執行中，請勿重複送出。", 409)

    record = agent_plan_store.mark_executing(safe_plan_id, user_id=user_id)
    if record is None:
        raise CopilotOperationError("計畫狀態不允許執行，請重新規劃。", 409)

    agent_payload = execute_copilot_agent_request(
        user_message=record.goal,
        context=record.context,
        tool_payloads=record.approved_tool_payloads,
        max_loops=max_loops,
        approved_pending_tools=record.pending_tools,
    )

    succeeded = agent_payload.get("route") == "finalize"
    if succeeded:
        steps = agent_payload.get("steps", [])
        if isinstance(steps, list) and steps:
            succeeded = bool(steps[-1].get("output", {}).get("ok", False))
    agent_plan_store.mark_executed(record.plan_id, user_id=user_id, succeeded=succeeded)

    executed_tools = agent_payload.get("executed_tools", [])
    diff_from_plan = []
    if isinstance(executed_tools, list):
        if executed_tools != record.pending_tools:
            diff_from_plan.append("實際執行順序與計畫預覽不同。")
    logger.info(
        "copilot_agent_plan_executed plan_id=%s approved_pending_tools=%s executed_tools=%s status=%s diff_from_plan=%s",
        record.plan_id,
        record.pending_tools,
        executed_tools,
        "succeeded" if succeeded else "failed",
        diff_from_plan,
    )
    return {
        "ok": True,
        "plan_id": record.plan_id,
        "execution_id": record.execution_id,
        "status": "succeeded" if succeeded else "failed",
        "approved_pending_tools": record.pending_tools,
        "executed_tools": executed_tools,
        "summary": agent_payload.get("final_answer", ""),
        "diff_from_plan": diff_from_plan,
        "steps_result": agent_payload.get("steps", []),
        "agent_result": agent_payload,
    }


def execute_copilot_agent_request(
    user_message: str,
    context: dict[str, Any] | None = None,
    tool_payloads: dict[str, dict[str, Any]] | None = None,
    max_loops: int = 6,
    approved_pending_tools: list[str] | None = None,
) -> dict[str, Any]:
    """以單體 Tool Registry + LangGraph ReAct 流程執行使用者需求。"""
    message = (user_message or "").strip()
    if not message:
        raise CopilotOperationError("message 不可為空。", 400)

    normalized_context = _normalize_context(context)
    safe_tool_payloads = _sanitize_tool_payloads(tool_payloads)

    try:
        from chains.agent_graph import run_react_agent

        return run_react_agent(
            user_message=message,
            context=normalized_context,
            tool_payloads=safe_tool_payloads,
            max_loops=max_loops,
            pending_tools=approved_pending_tools,
        )
    except Exception as exc:
        raise CopilotOperationError(f"Agent 執行失敗：{exc}", 500) from exc


