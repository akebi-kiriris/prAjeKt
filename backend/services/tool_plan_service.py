from __future__ import annotations

import json
import re
from typing import Any

from prompts.tool_planner import build_tool_planner_prompt

MAX_PLAN_STEPS = 6
PROTECTED_PAYLOAD_KEYS = {
    "user_id",
    "actor_user_id",
    "created_by",
    "timeline_id",
    "task_id",
    "group_id",
}


class ToolPlanError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _coerce_llm_text(value: Any) -> str:
    content = getattr(value, "content", value)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "\n".join(part for part in parts if part).strip()

    return str(content or "").strip()


def _strip_markdown_fence(text: Any) -> str:
    stripped = _coerce_llm_text(text)
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_first_json_object(text: str) -> str | None:
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


def _parse_proposal(raw: str) -> dict[str, Any]:
    cleaned = _strip_markdown_fence(raw)
    if not cleaned:
        raise ToolPlanError("模型未回傳可解析內容")
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_object(cleaned)
        if not extracted:
            raise ToolPlanError("模型回傳非 JSON 格式")
        parsed = json.loads(extracted)
    if not isinstance(parsed, dict):
        raise ToolPlanError("模型提案格式錯誤")
    return parsed


def _validate_steps(
    proposal: dict[str, Any],
    available_tool_names: set[str],
) -> tuple[list[str], dict[str, dict[str, Any]], str, str]:
    supported = bool(proposal.get("supported", True))
    if not supported:
        raise ToolPlanError(str(proposal.get("reason") or "模型判定目前需求不支援"))

    raw_steps = proposal.get("steps")
    if not isinstance(raw_steps, list) or len(raw_steps) == 0:
        raise ToolPlanError("模型未提出有效步驟")

    steps: list[str] = []
    for step in raw_steps:
        step_name = str(step or "").strip()
        if not step_name:
            continue
        if step_name not in available_tool_names:
            raise ToolPlanError(f"模型提案包含未註冊工具：{step_name}")
        steps.append(step_name)
    if not steps:
        raise ToolPlanError("模型提案步驟為空")
    if len(steps) > MAX_PLAN_STEPS:
        raise ToolPlanError(f"模型提案步驟過多，最多只允許 {MAX_PLAN_STEPS} 步")

    payload_draft = proposal.get("payload_draft", {})
    if not isinstance(payload_draft, dict):
        payload_draft = {}
    normalized_payload: dict[str, dict[str, Any]] = {}
    for key, value in payload_draft.items():
        tool_name = str(key or "").strip()
        if tool_name not in available_tool_names or not isinstance(value, dict):
            continue
        normalized_payload[tool_name] = value

    reason = str(proposal.get("reason") or "").strip()
    planning_mode = str(proposal.get("planning_mode") or "").strip().lower()
    if planning_mode not in {"create_project_only", "plan_tasks_only", "plan_and_create_tasks"}:
        planning_mode = "plan_tasks_only"
    return steps, normalized_payload, reason, planning_mode


def propose_plan_with_llm(
    *,
    user_message: str,
    context: dict[str, Any],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    """使用模型提案工具步驟（僅提案，不執行）。"""
    if not tools:
        raise ToolPlanError("可用工具清單為空")

    available_tool_names = {str(item.get("name") or "").strip() for item in tools if str(item.get("name") or "").strip()}
    tool_lines: list[str] = []
    for item in tools:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        description = str(item.get("description") or "").strip()
        side_effect_level = str(item.get("side_effect_level") or "").strip()
        permission_note = str(item.get("permission_note") or "").strip()
        planner_role = str(item.get("planner_role") or "").strip()
        workflow_group = str(item.get("workflow_group") or "").strip()
        completes_after = str(item.get("completes_after") or "").strip()
        input_schema = item.get("input_schema")
        tool_lines.append(
            f"- name={name}\n"
            f"  description={description}\n"
            f"  side_effect_level={side_effect_level}\n"
            f"  permission_note={permission_note}\n"
            f"  planner_role={planner_role}\n"
            f"  workflow_group={workflow_group}\n"
            f"  completes_after={completes_after}\n"
            f"  input_schema={json.dumps(input_schema, ensure_ascii=False)}"
        )

    prompt = build_tool_planner_prompt(
        user_message=user_message,
        context=context,
        tool_lines=tool_lines,
        protected_payload_keys=PROTECTED_PAYLOAD_KEYS,
    )

    try:
        from chains import get_default_llm

        llm = get_default_llm(provider="google-generativeai")
        raw = llm.invoke(prompt)
        raw_text = _coerce_llm_text(raw)
    except Exception as exc:
        raise ToolPlanError(f"模型提案失敗：{exc}") from exc

    proposal = _parse_proposal(raw_text)
    steps, payload_draft, reason, planning_mode = _validate_steps(proposal, available_tool_names)
    return {
        "planning_mode": planning_mode,
        "steps": steps,
        "payload_draft": payload_draft,
        "reason": reason,
    }
