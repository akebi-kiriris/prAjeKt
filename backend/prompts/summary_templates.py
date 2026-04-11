"""Summary Generation Prompt Templates

This module contains prompts for AI-powered summaries:
- Task Comment Summary: Extracts decisions, risks, next actions from task comments
- Group Snapshot: Creates action-oriented digest from group conversations
"""

from langchain_core.prompts import PromptTemplate

TASK_SUMMARY_PROMPT = PromptTemplate.from_template("""
You are an AI assistant summarizing task discussions.

## Task Context
Task: {task_title}
Description: {task_description}
Progress: {progress_percentage}%
Subtasks: {subtasks_completed}/{subtasks_total}

## Summarization Rules
1. **Decisions**: Extract explicit decisions made (e.g., "We decided to use Redis")
2. **Risks**: Identify potential blockers or concerns (e.g., "Performance might degrade")
3. **Next Actions**: Extract next steps or action items (e.g., "Need to set up staging")

## Output Format
Output ONLY a JSON object with no markdown fence:
{{
  "summary": "one concise paragraph",
  "ai_insights": "2-3 key insights for the assignee"
}}

Now analyze and output the JSON.
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
