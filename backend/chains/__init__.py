"""
PrAjeKt AI 模組的 LangChain 鏈實現

本模組包含可重用的 LLM 鏈以支援常見的 AI 工作流。
每個鏈封裝了完整的 LLM 互動模式。
"""

from chains.prompt_manager import PromptManager
from chains.task_generation_chain import (
    create_task_generation_chain,
    generate_tasks,
    generate_timeline_tasks_from_context,
)
from chains.summary_chain import (
    create_task_summary_chain,
    create_group_snapshot_chain,
    generate_task_summary,
    generate_group_snapshot,
)
from chains.tool_selection_chain import (
    create_tool_selection_chain,
    select_tools,
    parse_tool_selection_result,
)
from chains.llm_factory import (
    create_google_generative_ai,
    get_default_llm,
)
from chains.workflows import create_tool_routing_workflow
from chains.timeline_insight_chain import (
    create_weekly_report_summary_chain,
    create_conflict_suggestion_chain,
    generate_weekly_report_summary,
    generate_conflict_suggestion,
)
from chains.rag_planning_chain import (
    create_rag_plan_suggestion_chain,
    generate_rag_plan_suggestion,
)

__all__ = [
    "PromptManager",
    "create_task_generation_chain",
    "generate_tasks",
    "generate_timeline_tasks_from_context",
    "create_task_summary_chain",
    "create_group_snapshot_chain",
    "generate_task_summary",
    "generate_group_snapshot",
    "create_tool_selection_chain",
    "select_tools",
    "parse_tool_selection_result",
    "create_google_generative_ai",
    "get_default_llm",
    "create_tool_routing_workflow",
    "create_weekly_report_summary_chain",
    "create_conflict_suggestion_chain",
    "generate_weekly_report_summary",
    "generate_conflict_suggestion",
    "create_rag_plan_suggestion_chain",
    "generate_rag_plan_suggestion",
]
