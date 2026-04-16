"""
PrAjeKt 提示詞模板

本模組透過 LangChain 的 PromptTemplate 管理所有 LLM 提示詞。
提示詞集中管理便於版本控制與 A/B 測試。
"""

from prompts.tool_selector import TOOL_SELECTOR_PROMPT
from prompts.task_generator import TASK_GENERATOR_PROMPT
from prompts.timeline_task_request import (
    TIMELINE_TASK_REQUEST_PROMPT,
    build_timeline_task_request,
)
from prompts.summary_templates import (
    TASK_SUMMARY_PROMPT,
    GROUP_SNAPSHOT_PROMPT,
)
from prompts.timeline_insights import (
    WEEKLY_REPORT_SUMMARY_PROMPT,
    CONFLICT_SUGGESTION_PROMPT,
)

__all__ = [
    "TOOL_SELECTOR_PROMPT",
    "TASK_GENERATOR_PROMPT",
    "TIMELINE_TASK_REQUEST_PROMPT",
    "build_timeline_task_request",
    "TASK_SUMMARY_PROMPT",
    "GROUP_SNAPSHOT_PROMPT",
    "WEEKLY_REPORT_SUMMARY_PROMPT",
    "CONFLICT_SUGGESTION_PROMPT",
]
