"""Phase 7 專案洞察鏈。"""

from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence

from chains.prompt_manager import PromptManager
from prompts.timeline_insights import (
    CONFLICT_SUGGESTION_PROMPT,
    WEEKLY_REPORT_SUMMARY_PROMPT,
)


def _bind_llm_config(llm: Any, config: Dict[str, Any]) -> Any:
    if hasattr(llm, "bind"):
        return llm.bind(
            temperature=config.get("temperature", 0.2),
            max_output_tokens=config.get("max_tokens", 1000),
        )
    return llm


def create_weekly_report_summary_chain(llm: Any) -> RunnableSequence:
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("summary")
    llm_for_call = _bind_llm_config(llm, config)
    return WEEKLY_REPORT_SUMMARY_PROMPT | llm_for_call | StrOutputParser()


def create_conflict_suggestion_chain(llm: Any) -> RunnableSequence:
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("summary")
    llm_for_call = _bind_llm_config(llm, config)
    return CONFLICT_SUGGESTION_PROMPT | llm_for_call | StrOutputParser()


def generate_weekly_report_summary(llm: Any, status_text: str) -> str:
    chain = create_weekly_report_summary_chain(llm)
    result = chain.invoke({"status_text": status_text})
    return str(result).strip()


def generate_conflict_suggestion(
    llm: Any,
    conflict_text: str,
    suggestion_date_range: str,
    risk_context_text: str = "無",
) -> str:
    chain = create_conflict_suggestion_chain(llm)
    result = chain.invoke(
        {
            "conflict_text": conflict_text,
            "suggestion_date_range": suggestion_date_range,
            "risk_context_text": risk_context_text,
        }
    )
    return str(result).strip()
