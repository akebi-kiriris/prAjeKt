"""任務生成鏈

為自然語言輸入建立 LangChain 鏈以生成結構化任務。
支持 Pydantic v2 驗證層，帶有優雅降級到現有 JSON 提取函數。
"""

import json
import re
import logging
from typing import Any, Dict, List
from pydantic import ValidationError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.task_generator import TASK_GENERATOR_PROMPT
from chains.prompt_manager import PromptManager
from chains.schemas import Task

logger = logging.getLogger(__name__)


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
    """使用 Pydantic 驗證來解析和驗證任務列表
    
    驗證策略（優先順序）:
    1. 清理 markdown 圍欄 → JSON 解析 → Pydantic 驗證
    2. JSON 提取失敗時 → 使用 _extract_first_json_array()
    3. Pydantic 驗證失敗時 → 記錄並降級到原始 JSON 字典
    
    Args:
        raw_text: 原始 LLM 文本輸出
        
    Returns:
        經過驗證的任務字典列表
        
    Raises:
        ValueError: 文本為空或完全無法解析
    """
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
        raise ValueError(f"預期是任務列表，得到 {type(parsed)}")

    # Pydantic 驗證層：驗證每個任務
    validated_tasks = []
    for idx, task_dict in enumerate(parsed):
        try:
            # 試圖用 Pydantic 驗證該任務
            task_obj = Task.model_validate(task_dict)
            # 轉換回字典以保持向後相容性
            validated_tasks.append(task_obj.model_dump())
        except ValidationError as e:
            # 記錄驗證錯誤但不終止 - 降級到原始字典
            logger.warning(f"任務 #{idx} Pydantic 驗證失敗: {e}")
            logger.warning(f"降級使用原始任務字典: {task_dict}")
            # 檢查最少必需欄位
            if not all(key in task_dict for key in ["name", "priority", "estimated_days", "task_remark"]):
                logger.error(f"任務 #{idx} 缺少必需欄位，跳過: {task_dict}")
                continue
            validated_tasks.append(task_dict)
        except Exception as e:
            logger.error(f"任務 #{idx} 驗證期間發生意外錯誤: {e}，原始任務: {task_dict}")
            continue

    if not validated_tasks:
        raise ValueError("沒有有效的任務可解析")

    return validated_tasks


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
        配置完成的任務生成 RunnableSequence
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
    使用 LangChain 從使用者輸入生成任務。

    Args:
        llm: LangChain LLM 實例
        project_name: 專案名稱
        project_description: 專案描述（用於上下文）
        user_input: 自然語言任務需求
        user_name: 要求生成任務的使用者名稱

    Returns:
        生成的任務字典列表

    Raises:
        ValueError: LLM 輸出不是有效的 JSON 時
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
