from __future__ import annotations

import json
import re
from typing import Any

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

    prompt = (
        "你是後端工具規劃器。請根據使用者需求與工具清單，輸出 JSON 提案。\n"
        "限制：只能挑選清單中工具，不可發明新工具，不可直接執行。\n"
        f"不可在 payload_draft 中填入 {', '.join(sorted(PROTECTED_PAYLOAD_KEYS))}；這些 scope 欄位由系統 context 注入。\n"
        "你必須自行判斷使用者意圖，不要假設所有提到『規劃』『學習計畫』的需求都要直接建立任務。\n"
        "你還必須輸出 planning_mode，且只能是 create_project_only / plan_tasks_only / plan_and_create_tasks 其中之一。\n"
        "請善用每個工具的 planner_role / workflow_group / completes_after 來判斷流程，而不是只看工具名稱。\n"
        "規則：\n"
        "- planner_role=read / analysis：偏查詢或分析。\n"
        "- planner_role=suggestion：代表只產生建議或草案，通常不會真的把資料寫入系統。\n"
        "- planner_role=apply_suggestion：代表把前一步 suggestion 的結果正式寫入系統。\n"
        "- planner_role=direct_write：代表直接對系統做建立/更新/寫入。\n"
        "如果使用者要求的是『實際把結果建立/更新到系統內』，且某個 workflow_group 同時存在 suggestion 與 apply_suggestion 工具，請規劃完整流程，不要停在 suggestion。\n"
        "如果使用者只是想先看建議、先看規劃、先看草案，才停在 suggestion。\n"
        "如果只是要建立專案：planning_mode=create_project_only，且只輸出 create_timeline_for_user。\n"
        "如果是建立專案後先產生任務建議、讓使用者看規劃：planning_mode=plan_tasks_only，可輸出 create_timeline_for_user + generate_timeline_tasks_with_ai，但不要加入 batch_create_tasks_for_timeline。\n"
        "如果使用者要你把規劃結果直接建立成任務、安排成可執行學習步驟、或直接落到專案中：planning_mode=plan_and_create_tasks，應輸出 create_timeline_for_user + generate_timeline_tasks_with_ai + batch_create_tasks_for_timeline。\n"
        "如果你選擇 create_timeline_for_user，請盡量在 payload_draft.create_timeline_for_user.data 中提供 name 與 remark。\n"
        "若使用者沒有明講專案名稱，請根據主題自行生成一個簡潔、自然的專案名稱，不要使用『新專案』這種空泛名稱。\n"
        "例如：\n"
        "- 使用者說『幫我建立一個專案，主要為我學習 LangGraph 的計畫，先幫我好好規劃』：planning_mode=plan_tasks_only，可輸出 create_timeline_for_user + generate_timeline_tasks_with_ai。\n"
        "- 使用者說『幫我建立一個專案，主要為我學習 LangGraph 的計畫，幫我好好規劃怎麼學，最後直接幫我安排成任務』：planning_mode=plan_and_create_tasks，應輸出 create_timeline_for_user + generate_timeline_tasks_with_ai + batch_create_tasks_for_timeline。\n"
        "輸出格式：\n"
        "{\n"
        '  "supported": true,\n'
        '  "planning_mode": "plan_tasks_only",\n'
        '  "steps": ["tool_a", "tool_b"],\n'
        '  "payload_draft": {"tool_a": {"key": "value"}},\n'
        '  "reason": "一句話說明規劃理由"\n'
        "}\n\n"
        f"使用者需求：{user_message}\n"
        f"上下文：{json.dumps(context, ensure_ascii=False)}\n"
        f"可用工具：\n{chr(10).join(tool_lines)}"
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
