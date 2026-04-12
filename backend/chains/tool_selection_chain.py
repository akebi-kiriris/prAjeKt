"""工具選擇鏈

根據使用者輸入為 MCP 工具選擇建立 LangChain 鏈。
支持 Pydantic v2 驗證層，帶有優雅降級到現有 JSON 提取函數。
"""

import json
import re
import logging
from typing import Any, Dict, Optional, List
from pydantic import ValidationError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.tool_selector import TOOL_SELECTOR_PROMPT
from chains.prompt_manager import PromptManager
from chains.schemas import ToolSelection

logger = logging.getLogger(__name__)


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
    """使用 Pydantic 驗證來解析和驗證工具選擇結果
    
    驗證策略（優先順序）:
    1. 清理 markdown 圍欄 → JSON 解析 → Pydantic 驗證
    2. JSON 提取失敗時 → 使用 _extract_first_json_object()
    3. Pydantic 驗證失敗時 → 記錄並降級到原始 JSON 字典
    
    Args:
        raw_result: 原始 LLM 文本輸出
        
    Returns:
        經過驗證的工具選擇字典（含 tool_name、arguments、reason）
        
    Raises:
        ValueError: 文本為空或完全無法解析
    """
    cleaned = _strip_markdown_fence(raw_result)
    if not cleaned:
        raise ValueError("工具選擇輸出為空")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_object(cleaned)
        if not extracted:
            raise ValueError("無法解析工具選擇 JSON")
        parsed = json.loads(extracted)

    if not isinstance(parsed, dict):
        raise ValueError("工具選擇輸出必須是 JSON 物件")

    # Pydantic 驗證層
    try:
        # 試圖用 Pydantic 驗證工具選擇
        tool_obj = ToolSelection.model_validate(parsed)
        return tool_obj.model_dump()
    except ValidationError as e:
        # 記錄驗證錯誤但不終止 - 降級到原始字典
        logger.warning(f"工具選擇 Pydantic 驗證失敗: {e}")
        logger.warning(f"降級使用原始工具選擇字典: {parsed}")
        # 檢查最少必需欄位
        if not all(key in parsed for key in ["tool_name", "arguments", "reason"]):
            raise ValueError(f"工具選擇缺少必需欄位: {parsed}")
        return parsed
    except Exception as e:
        logger.error(f"工具選擇驗證期間發生意外錯誤: {e}，原始結果: {parsed}")
        # 最後降級檢查
        if not all(key in parsed for key in ["tool_name", "arguments", "reason"]):
            raise ValueError(f"工具選擇無效: {parsed}")
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
        選擇工具的 RunnableSequence
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
    使用 LangChain 為使用者輸入選擇適當的工具。

    Args:
        llm: LangChain LLM 實例
        user_input: 使用者的自然語言要求
        available_tools: 可用工具的描述列表
        context: 工具選擇的附加上下文

    Returns:
        包含選中工具及理由的字典

    Raises:
        ValueError: 工具選擇失敗時
    """
    chain = create_tool_selection_chain(llm)

    # 整理工具描述供 prompt 使用
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
        raise ValueError(f"工具選擇失敗：{str(e)}")


def parse_tool_selection_result(raw_result: str) -> Dict[str, Any]:
    """
    解析 LLM 輸出的工具選擇結果。

    Args:
        raw_result: LLM 的原始字串輸出

    Returns:
        解析後的工具選擇字典
    """
    try:
        return _parse_tool_selection(raw_result)
    except ValueError:
        # Fallback: 回傳空的選擇
        return {"tools": [], "reasoning": "無法解析工具選擇"}
