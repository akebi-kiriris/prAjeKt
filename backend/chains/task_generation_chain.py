"""任務生成鏈

為自然語言輸入建立 LangChain 鏈以生成結構化任務。
"""

import json
import re
from typing import Any, Dict, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.task_generator import TASK_GENERATOR_PROMPT
from chains.prompt_manager import PromptManager


def _strip_markdown_fence(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _extract_first_json_array(text: str) -> str | None:
    if not isinstance(text, str):
        return None

    start = text.find("[")
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

        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start: idx + 1]

    return None


def _parse_tasks(raw_text: str) -> List[Dict[str, Any]]:
    cleaned = _strip_markdown_fence(raw_text)
    if not cleaned:
        raise ValueError("AI 回應為空")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_array(cleaned)
        if not extracted:
            raise ValueError("AI 回應解析失敗")
        parsed = json.loads(extracted)

    if not isinstance(parsed, list):
        raise ValueError(f"Expected list of tasks, got {type(parsed)}")

    return parsed


def _bind_llm_config(llm: Any, config: Dict[str, Any]) -> Any:
    if hasattr(llm, "bind"):
        return llm.bind(
            temperature=config.get("temperature", 0.7),
            max_output_tokens=config.get("max_tokens", 2048),
        )
    return llm


def create_task_generation_chain(llm: Any) -> RunnableSequence:
    """
    建立任務生成鏈。

    Args:
        llm: LangChain LLM 實例（例如 GoogleGenerativeAI）

    Returns:
        RunnableSequence for task generation with string output parsing
    """
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("task_generation")
    llm_for_call = _bind_llm_config(llm, config)

    chain = TASK_GENERATOR_PROMPT | llm_for_call | StrOutputParser()

    return chain


def generate_tasks(
    llm: Any,
    project_name: str,
    project_description: str,
    user_input: str,
    user_name: str = "User",
) -> List[Dict[str, Any]]:
    """
    Generate tasks from user input using LangChain.

    Args:
        llm: LangChain LLM instance
        project_name: Name of the project
        project_description: Project description for context
        user_input: Natural language task requirements
        user_name: Name of the user requesting task generation

    Returns:
        List of generated task dictionaries

    Raises:
        ValueError: If LLM output is not valid JSON
    """
    chain = create_task_generation_chain(llm)

    raw_text = chain.invoke(
        {
            "project_name": project_name,
            "project_description": project_description,
            "user_input": user_input,
            "user_name": user_name,
        }
    )

    return _parse_tasks(raw_text)
