import logging
from typing import Any, Dict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from pydantic import ValidationError

from chains.prompt_manager import PromptManager
from chains.schemas import PlanSuggestionOutput
from prompts.rag_planning import RAG_PLAN_SUGGESTION_PROMPT

logger = logging.getLogger(__name__)


def _bind_llm_config(llm: Any, config: Dict[str, Any]) -> Any:
    if hasattr(llm, "bind"):
        return llm.bind(
            temperature=config.get("temperature", 0.2),
            max_output_tokens=config.get("max_tokens", 1500),
        )
    return llm


def create_rag_plan_suggestion_chain(llm: Any) -> RunnableSequence:
    prompt_mgr = PromptManager()
    config = prompt_mgr.get_config("summary")
    llm_for_call = _bind_llm_config(llm, config)
    return RAG_PLAN_SUGGESTION_PROMPT | llm_for_call | JsonOutputParser()


def generate_rag_plan_suggestion(
    llm: Any,
    user_request: str,
    retrieval_context: str,
) -> Dict[str, Any]:
    chain = create_rag_plan_suggestion_chain(llm)
    format_instructions = (
        "輸出 JSON 物件，欄位包含 suggested_timeline, suggested_tasks, source_references, summary。"
    )
    raw_payload = chain.invoke(
        {
            "user_request": user_request,
            "retrieval_context": retrieval_context,
            "format_instructions": format_instructions,
        }
    )
    if not isinstance(raw_payload, dict):
        raise ValueError("AI 回傳格式錯誤，預期為 JSON 物件")

    try:
        validated = PlanSuggestionOutput.model_validate(raw_payload)
        return validated.model_dump()
    except ValidationError as exc:
        logger.warning("RAG 規劃輸出驗證失敗，改採最小降級格式: %s", exc)
        tasks = raw_payload.get("suggested_tasks") if isinstance(raw_payload.get("suggested_tasks"), list) else []
        refs = raw_payload.get("source_references") if isinstance(raw_payload.get("source_references"), list) else []
        timeline = raw_payload.get("suggested_timeline") if isinstance(raw_payload.get("suggested_timeline"), dict) else {}
        fallback = {
            "suggested_timeline": {
                "name": str(timeline.get("name") or "AI 建議專案"),
                "objective": str(timeline.get("objective") or "依據既有知識整理的執行計畫"),
            },
            "suggested_tasks": [],
            "source_references": [],
            "summary": str(raw_payload.get("summary") or "").strip(),
        }

        for task in tasks:
            if not isinstance(task, dict):
                continue
            fallback["suggested_tasks"].append(
                {
                    "name": str(task.get("name") or "未命名任務"),
                    "reason": str(task.get("reason") or "由 AI 推估建議"),
                    "priority": str(task.get("priority") or "MEDIUM").upper(),
                    "estimated_days": int(task.get("estimated_days") or 3),
                    "depends_on": task.get("depends_on") if isinstance(task.get("depends_on"), list) else [],
                }
            )

        for ref in refs:
            if not isinstance(ref, dict):
                continue
            source_type = str(ref.get("source_type") or "").strip()
            if source_type not in {"timeline_task", "knowledge_chunk"}:
                continue
            fallback["source_references"].append(
                {
                    "source_type": source_type,
                    "source_id": str(ref.get("source_id") or "unknown"),
                    "title": str(ref.get("title") or "來源"),
                    "snippet": str(ref.get("snippet") or ""),
                    "score": float(ref.get("score") or 0.0),
                }
            )

        return fallback
