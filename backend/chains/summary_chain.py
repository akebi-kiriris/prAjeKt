"""摘要生成鏈

為任務摘要和群組快照建立 LangChain 鏈。
"""

import json
import re
from typing import Any, Dict, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.summary_templates import TASK_SUMMARY_PROMPT, GROUP_SNAPSHOT_PROMPT
from chains.prompt_manager import PromptManager


def _strip_markdown_fence(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_first_json_object(text: str) -> str | None:
    if not isinstance(text, str):
        return None

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


def _parse_json_object(raw_text: str) -> Dict[str, Any]:
    cleaned = _strip_markdown_fence(raw_text)
    if not cleaned:
        raise ValueError("AI summary output is empty")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_object(cleaned)
        if not extracted:
            raise ValueError("Failed to parse summary JSON")
        parsed = json.loads(extracted)

    if not isinstance(parsed, dict):
        raise ValueError("Summary output must be a JSON object")

    return parsed


def _bind_llm_config(llm: Any, config: Dict[str, Any]) -> Any:
    if hasattr(llm, "bind"):
        return llm.bind(
            temperature=config.get("temperature", 0.2),
            max_output_tokens=config.get("max_tokens", 2000),
        )
    return llm


def create_task_summary_chain(llm: Any) -> RunnableSequence:
    """
    建立任務摘要生成鏈。

    Args:
        llm: LangChain LLM 實例

    Returns:
        RunnableSequence configured for task summary generation
    """
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("task_summary")
    llm_for_call = _bind_llm_config(llm, config)

    parser = StrOutputParser()
    chain = TASK_SUMMARY_PROMPT | llm_for_call | parser
    return chain


def create_group_snapshot_chain(llm: Any) -> RunnableSequence:
    """
    Create a group snapshot generation chain.

    Args:
        llm: LangChain LLM instance

    Returns:
        RunnableSequence configured for group snapshot generation
    """
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("group_snapshot")
    llm_for_call = _bind_llm_config(llm, config)

    parser = StrOutputParser()
    chain = GROUP_SNAPSHOT_PROMPT | llm_for_call | parser
    return chain


def generate_task_summary(
    llm: Any,
    task_title: str,
    task_description: str,
    subtasks_completed: int = 0,
    subtasks_total: int = 0,
    progress_percentage: float = 0.0,
    fallback_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a summary for a task using LangChain.

    Args:
        llm: LangChain LLM instance
        task_title: Title of the task
        task_description: Description of the task
        subtasks_completed: Number of completed subtasks
        subtasks_total: Total number of subtasks
        progress_percentage: Task progress percentage (0-100)
        fallback_summary: Fallback summary if generation fails

    Returns:
        Dictionary containing task summary with 'summary' and 'ai_insights' keys

    Raises:
        ValueError: If LLM output is not valid JSON and no fallback provided
    """
    chain = create_task_summary_chain(llm)

    try:
        raw_result = chain.invoke(
            {
                "task_title": task_title,
                "task_description": task_description,
                "subtasks_completed": subtasks_completed,
                "subtasks_total": subtasks_total,
                "progress_percentage": progress_percentage,
            }
        )
        return _parse_json_object(raw_result)
    except (json.JSONDecodeError, ValueError) as e:
        if fallback_summary:
            return {
                "summary": fallback_summary,
                "ai_insights": "Generation failed, using fallback",
            }
        raise ValueError(f"Failed to generate task summary: {str(e)}")


def generate_group_snapshot(
    llm: Any,
    group_name: str,
    members_count: int,
    active_tasks: int,
    completed_tasks: int,
    pending_tasks: int,
    activities_summary: str = "",
    fallback_snapshot: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a group snapshot using LangChain.

    Args:
        llm: LangChain LLM instance
        group_name: Name of the group
        members_count: Number of group members
        active_tasks: Number of active tasks
        completed_tasks: Number of completed tasks
        pending_tasks: Number of pending tasks
        activities_summary: Summary of recent group activities
        fallback_snapshot: Fallback snapshot if generation fails

    Returns:
        Dictionary containing group snapshot with health status and insights

    Raises:
        ValueError: If LLM output is not valid JSON and no fallback provided
    """
    chain = create_group_snapshot_chain(llm)

    try:
        raw_result = chain.invoke(
            {
                "group_name": group_name,
                "members_count": members_count,
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "activities_summary": activities_summary,
            }
        )
        return _parse_json_object(raw_result)
    except (json.JSONDecodeError, ValueError) as e:
        if fallback_snapshot:
            return {
                "snapshot": fallback_snapshot,
                "health_status": "unknown",
                "recommendations": [],
            }
        raise ValueError(f"Failed to generate group snapshot: {str(e)}")
