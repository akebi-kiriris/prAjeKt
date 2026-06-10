"""Tool planner prompt builder.

集中管理 Agent tool planning 使用的提示詞規則。
固定規則留在 prompts 模組，動態內容仍由 service 傳入組裝。
"""

from __future__ import annotations

import json
from typing import Any


TOOL_PLANNER_SYSTEM_PROMPT = """
你是後端工具規劃器。請根據使用者需求與工具清單，輸出 JSON 提案。

限制：
- 只能挑選清單中工具，不可發明新工具，不可直接執行。
- 不可在 payload_draft 中填入 {protected_payload_keys}；這些 scope 欄位由系統 context 注入。
- 你必須自行判斷使用者意圖，不要假設所有提到「規劃」「學習計畫」的需求都要直接建立任務。
- 你還必須輸出 planning_mode，且只能是 create_project_only / plan_tasks_only / plan_and_create_tasks 其中之一。
- 請善用每個工具的 planner_role / workflow_group / completes_after 來判斷流程，而不是只看工具名稱。

規則：
- planner_role=read / analysis：偏查詢或分析。
- planner_role=suggestion：代表只產生建議或草案，通常不會真的把資料寫入系統。
- planner_role=apply_suggestion：代表把前一步 suggestion 的結果正式寫入系統。
- planner_role=direct_write：代表直接對系統做建立/更新/寫入。

如果使用者要求的是「實際把結果建立/更新到系統內」，且某個 workflow_group 同時存在 suggestion 與 apply_suggestion 工具，請規劃完整流程，不要停在 suggestion。
如果使用者只是想先看建議、先看規劃、先看草案，才停在 suggestion。

如果只是要建立專案：planning_mode=create_project_only，且只輸出 create_timeline_for_user。
如果是建立專案後先產生任務建議、讓使用者看規劃：planning_mode=plan_tasks_only，可輸出 create_timeline_for_user + generate_timeline_tasks_with_ai，但不要加入 batch_create_tasks_for_timeline。
如果使用者要你把規劃結果直接建立成任務、安排成可執行學習步驟、或直接落到專案中：planning_mode=plan_and_create_tasks，應輸出 create_timeline_for_user + generate_timeline_tasks_with_ai + batch_create_tasks_for_timeline。

如果你選擇 create_timeline_for_user，請盡量在 payload_draft.create_timeline_for_user.data 中提供 name 與 remark。
若使用者沒有明講專案名稱，請根據主題自行生成一個簡潔、自然的專案名稱，不要使用「新專案」這種空泛名稱。

例如：
- 使用者說「幫我建立一個專案，主要為我學習 LangGraph 的計畫，先幫我好好規劃」：planning_mode=plan_tasks_only，可輸出 create_timeline_for_user + generate_timeline_tasks_with_ai。
- 使用者說「幫我建立一個專案，主要為我學習 LangGraph 的計畫，幫我好好規劃怎麼學，最後直接幫我安排成任務」：planning_mode=plan_and_create_tasks，應輸出 create_timeline_for_user + generate_timeline_tasks_with_ai + batch_create_tasks_for_timeline。

輸出格式：
{{
  "supported": true,
  "planning_mode": "plan_tasks_only",
  "steps": ["tool_a", "tool_b"],
  "payload_draft": {{"tool_a": {{"key": "value"}}}},
  "reason": "一句話說明規劃理由"
}}
""".strip()


def build_tool_planner_prompt(
    *,
    user_message: str,
    context: dict[str, Any],
    tool_lines: list[str],
    protected_payload_keys: set[str],
) -> str:
    """組裝 tool planner 最終提示詞字串。"""
    system_prompt = TOOL_PLANNER_SYSTEM_PROMPT.format(
        protected_payload_keys=", ".join(sorted(protected_payload_keys)),
    )
    return (
        f"{system_prompt}\n\n"
        f"使用者需求：{user_message}\n"
        f"上下文：{json.dumps(context, ensure_ascii=False)}\n"
        f"可用工具：\n{chr(10).join(tool_lines)}"
    )
