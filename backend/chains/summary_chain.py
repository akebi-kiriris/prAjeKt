"""摘要生成鏈

為任務摘要和群組快照建立 LangChain 鏈。
支持 Pydantic v2 驗證層，帶有優雅降級到現有 JSON 提取函數。
"""

import json
import re
import logging
from typing import Any, Dict, Optional
from pydantic import ValidationError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence
from prompts.summary_templates import TASK_SUMMARY_PROMPT, GROUP_SNAPSHOT_PROMPT
from chains.prompt_manager import PromptManager
from chains.schemas import TaskSummary, GroupSnapshot

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


def _parse_json_object(raw_text: str) -> Dict[str, Any]:
    """通用 JSON 物件解析（向後相容用）"""
    cleaned = _strip_markdown_fence(raw_text)
    if not cleaned:
        raise ValueError("AI 摘要輸出為空")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        extracted = _extract_first_json_object(cleaned)
        if not extracted:
            raise ValueError("無法解析摘要 JSON")
        parsed = json.loads(extracted)

    if not isinstance(parsed, dict):
        raise ValueError("摘要輸出必須是 JSON 物件")

    return parsed


def _parse_task_summary(raw_text: str) -> Dict[str, Any]:
    """使用 Pydantic 驗證來解析和驗證任務摘要結果
    
    驗證策略（優先順序）:
    1. 清理 markdown 圍欄 → JSON 解析 → Pydantic 驗證
    2. JSON 提取失敗時 → 使用 _extract_first_json_object()
    3. Pydantic 驗證失敗時 → 記錄並降級到原始 JSON 字典
    
    Args:
        raw_text: 原始 LLM 文本輸出
        
    Returns:
        經過驗證的任務摘要字典
        
    Raises:
        ValueError: 文本為空或完全無法解析
    """
    parsed = _parse_json_object(raw_text)
    
    # Pydantic 驗證層
    try:
        # 試圖用 Pydantic 驗證任務摘要
        summary_obj = TaskSummary.model_validate(parsed)
        return summary_obj.model_dump()
    except ValidationError as e:
        # 記錄驗證錯誤但不終止 - 降級到原始字典
        logger.warning(f"任務摘要 Pydantic 驗證失敗: {e}")
        logger.warning(f"降級使用原始任務摘要字典: {parsed}")
        # 檢查最少必需欄位
        if not all(key in parsed for key in ["decisions", "next_actions"]):
            raise ValueError(f"任務摘要缺少必需欄位: {parsed}")
        return parsed
    except Exception as e:
        logger.error(f"任務摘要驗證期間發生意外錯誤: {e}，原始結果: {parsed}")
        # 最後降級檢查
        if not all(key in parsed for key in ["decisions", "next_actions"]):
            raise ValueError(f"任務摘要無效: {parsed}")
        return parsed


def _parse_group_snapshot(raw_text: str) -> Dict[str, Any]:
    """使用 Pydantic 驗證來解析和驗證群組快照結果
    
    驗證策略（優先順序）:
    1. 清理 markdown 圍欄 → JSON 解析 → Pydantic 驗證
    2. JSON 提取失敗時 → 使用 _extract_first_json_object()
    3. Pydantic 驗證失敗時 → 記錄並降級到原始 JSON 字典
    
    Args:
        raw_text: 原始 LLM 文本輸出
        
    Returns:
        經過驗證的群組快照字典
        
    Raises:
        ValueError: 文本為空或完全無法解析
    """
    parsed = _parse_json_object(raw_text)
    
    # Pydantic 驗證層
    try:
        # 試圖用 Pydantic 驗證群組快照
        snapshot_obj = GroupSnapshot.model_validate(parsed)
        return snapshot_obj.model_dump()
    except ValidationError as e:
        # 記錄驗證錯誤但不終止 - 降級到原始字典
        logger.warning(f"群組快照 Pydantic 驗證失敗: {e}")
        logger.warning(f"降級使用原始群組快照字典: {parsed}")
        # 檢查最少必需欄位
        if not all(key in parsed for key in ["health_status", "key_activities", "recommendations"]):
            raise ValueError(f"群組快照缺少必需欄位: {parsed}")
        return parsed
    except Exception as e:
        logger.error(f"群組快照驗證期間發生意外錯誤: {e}，原始結果: {parsed}")
        # 最後降級檢查
        if not all(key in parsed for key in ["health_status", "key_activities", "recommendations"]):
            raise ValueError(f"群組快照無效: {parsed}")
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
        配置完成的任務摘要生成 RunnableSequence
    """
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("task_summary")
    llm_for_call = _bind_llm_config(llm, config)

    parser = StrOutputParser()
    chain = TASK_SUMMARY_PROMPT | llm_for_call | parser
    return chain


def create_group_snapshot_chain(llm: Any) -> RunnableSequence:
    """
    建立群組快照生成鏈。

    Args:
        llm: LangChain LLM 實例

    Returns:
        配置完成的群組快照生成 RunnableSequence
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
    使用 LangChain 生成任務摘要。

    Args:
        llm: LangChain LLM 實例
        task_title: 任務標題
        task_description: 任務描述
        subtasks_completed: 已完成子任務數
        subtasks_total: 子任務總數
        progress_percentage: 任務進度百分比 (0-100)
        fallback_summary: 生成失敗時的備用摘要

    Returns:
        包含 'summary' 和 'ai_insights' 鍵的字典

    Raises:
        ValueError: LLM 輸出不是有效 JSON 且無備用摘要時
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
        return _parse_task_summary(raw_result)
    except (json.JSONDecodeError, ValueError) as e:
        if fallback_summary:
            return {
                "decisions": ["使用備用摘要" if not fallback_summary else fallback_summary],
                "risks": [],
                "next_actions": [],
            }
        raise ValueError(f"任務摘要生成失敗：{str(e)}")


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
    使用 LangChain 生成群組快照。

    Args:
        llm: LangChain LLM 實例
        group_name: 群組名稱
        members_count: 群組成員數
        active_tasks: 進行中的任務數
        completed_tasks: 已完成的任務數
        pending_tasks: 待辦的任務數
        activities_summary: 最近群組活動摘要
        fallback_snapshot: 生成失敗時的備用快照

    Returns:
        包含群組快照、健康狀態及建議的字典

    Raises:
        ValueError: LLM 輸出不是有效 JSON 且無備用快照時
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
        return _parse_group_snapshot(raw_result)
    except (json.JSONDecodeError, ValueError) as e:
        if fallback_snapshot:
            return {
                "health_status": "AT_RISK",
                "key_activities": ["使用備用快照" if not fallback_snapshot else fallback_snapshot],
                "recommendations": ["檢查系統日誌"],
            }
        raise ValueError(f"群組快照生成失敗：{str(e)}")
