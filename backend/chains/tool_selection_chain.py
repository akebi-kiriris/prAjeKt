"""工具選擇鏈

根據使用者輸入為 MCP 工具選擇建立 LangChain 鏈。
"""

import json
import re
from typing import Any, Dict, Optional, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.tool_selector import TOOL_SELECTOR_PROMPT
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


def _parse_tool_selection(raw_result: str) -> Dict[str, Any]:
    cleaned = _strip_markdown_fence(raw_result)
    if not cleaned:
        raise ValueError("Tool selection output is empty")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_object(cleaned)
        if not extracted:
            raise ValueError("Failed to parse tool selection JSON")
        parsed = json.loads(extracted)

    if not isinstance(parsed, dict):
        raise ValueError("Tool selection output must be a JSON object")

    return parsed


def _bind_llm_config(llm: Any, config: Dict[str, Any]) -> Any:
    if hasattr(llm, "bind"):
        return llm.bind(
            temperature=config.get("temperature", 0.2),
            max_output_tokens=config.get("max_tokens", 500),
        )
    return llm


def create_tool_selection_chain(llm: Any) -> RunnableSequence:
    """
    建立工具選擇鏈。

    Args:
        llm: LangChain LLM 實例

    Returns:
        RunnableSequence for tool selection with string output parsing
    """
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("tool_selection")
    llm_for_call = _bind_llm_config(llm, config)

    parser = StrOutputParser()
    chain = TOOL_SELECTOR_PROMPT | llm_for_call | parser
    return chain


def select_tools(
    llm: Any,
    user_input: str,
    available_tools: List[Dict[str, str]],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Select appropriate tools for user input using LangChain.

    Args:
        llm: LangChain LLM instance
        user_input: User's natural language request
        available_tools: List of available tool descriptions
        context: Additional context for tool selection

    Returns:
        Dictionary with selected tools and reasoning

    Raises:
        ValueError: If tool selection fails
    """
    chain = create_tool_selection_chain(llm)

    # Format tools for the prompt
    tools_str = "\n".join(
        [
            f"- {str(tool.get('name') or '').strip()}: {str(tool.get('description') or '').strip()}"
            for tool in available_tools
            if str(tool.get('name') or '').strip()
        ]
    )

    context_dict = context if isinstance(context, dict) else {}
    context_str = (
        f"timeline_id={context_dict.get('timeline_id')}, "
        f"timeline_name={context_dict.get('timeline_name')}, "
        f"task_id={context_dict.get('task_id')}, "
        f"group_id={context_dict.get('group_id')}"
    )

    try:
        raw_result = chain.invoke(
            {
                "user_input": user_input,
                "available_tools": tools_str,
                "context": context_str,
            }
        )

        return _parse_tool_selection(raw_result)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to select tools: {str(e)}")


def parse_tool_selection_result(raw_result: str) -> Dict[str, Any]:
    """
    Parse raw LLM output for tool selection.

    Args:
        raw_result: Raw string output from LLM

    Returns:
        Parsed dictionary with selected tools
    """
    try:
        return _parse_tool_selection(raw_result)
    except ValueError:
        # Fallback: return empty selection
        return {"tools": [], "reasoning": "Unable to parse tool selection"}
