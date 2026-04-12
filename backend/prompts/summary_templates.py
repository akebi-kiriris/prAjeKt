"""Summary Generation Prompt Templates

This module contains prompts for AI-powered summaries:
- Task Comment Summary: Extracts decisions, risks, next actions from task comments
- Group Snapshot: Creates action-oriented digest from group conversations
"""

from langchain_core.prompts import PromptTemplate

TASK_SUMMARY_PROMPT = PromptTemplate.from_template("""
你是一個任務討論摘要助手，負責將討論整理成可執行且清晰的摘要。

## 任務上下文
任務: {task_title}
描述: {task_description}
進度: {progress_percentage}%
子任務已完成/總數: {subtasks_completed}/{subtasks_total}

## 摘要規則
1. 決議 (Decisions): 擷取明確的決議（例如："決定使用 Redis"）
2. 風險 (Risks): 辨識可能的阻礙或風險（例如："效能可能下降"）
3. 後續動作 (Next Actions): 擷取具體的下一步或行動項目（例如："建立 staging 環境"）

## 輸出格式
僅輸出一個 JSON 物件，請勿包含任何 markdown 格式：
{{
  "summary": "一段精簡摘要（1-2 句）",
  "ai_insights": "提供 2-3 個關鍵洞察，給負責人作為注意事項"
}}

請依據上述規則產生 JSON。
""")

GROUP_SNAPSHOT_PROMPT = PromptTemplate.from_template("""
你是一個專案協作助理，負責生成「行動導向 Digest」。

## 群組背景
群組名稱: {group_name}
群組成員: {members_count}
活躍任務: {active_tasks}
完成任務: {completed_tasks}
待辦任務: {pending_tasks}

## 近期訊息與討論
{activities_summary}

## 生成規則
生成一份簡潔的行動導向摘要，包含：
1. **一句重點** - 過去 30 天群組最重要的進展是什麼？
2. **你現在要做什麼** - 針對你（群組擁有者或成員），接下來的具體行動是什麼？
3. **風險與阻塞** - 有什麼阻礙專案推進的因素？
4. **精簡決議** - 群組做出了哪些關鍵決策？

## 輸出格式
輸出 JSON 物件，不含 markdown 標記：
{{
  "snapshot": "這個群組目前狀態的摘要",
  "health_status": "healthy | warning | critical",
  "recommendations": ["建議1", "建議2"]
}}

現在分析並輸出 JSON。
""")
