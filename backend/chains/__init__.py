"""
PrAjeKt AI 模組的 LangChain 鏈實現

本模組包含可重用的 LLM 鏈以支援常見的 AI 工作流。
每個鏈封裝了完整的 LLM 互動模式。
"""

from chains.prompt_manager import PromptManager
from chains.task_generation_chain import (
    create_task_generation_chain,
    generate_tasks,
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

__all__ = [
    "PromptManager",
    "create_task_generation_chain",
    "generate_tasks",
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
]
