import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from typing import Any

from chains import generate_rag_plan_suggestion, get_default_llm
from contracts.response_helpers import build_response_payload
from contracts.timeline_contracts import TimelinePlanSuggestionResponse
from repositories.knowledge_repository import (
    search_knowledge_chunks_by_text,
    search_knowledge_chunks_with_scores,
)
from repositories.timeline_repository import (
    get_active_tasks_by_timeline_ids,
    get_timeline_memberships_for_user,
)
from services.embedding_service import EmbeddingOperationError, GeminiEmbeddingService


class RAGPlanningOperationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RAGPlanningTimeoutError(Exception):
    pass


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _extract_query_terms(text: str) -> list[str]:
    separators = ["\n", ",", "，", "。", ".", "、", " ", "\t"]
    normalized = text
    for separator in separators:
        normalized = normalized.replace(separator, "|")
    terms = [item.strip().lower() for item in normalized.split("|") if item.strip()]
    return [item for item in terms if len(item) >= 2]


def _normalize_task_tags(tags: Any) -> list[str]:
    if not tags:
        return []
    if isinstance(tags, str):
        return [item.strip() for item in tags.replace("，", ",").split(",") if item.strip()]
    if isinstance(tags, (list, tuple, set)):
        return [str(item).strip() for item in tags if str(item).strip()]
    return [str(tags).strip()] if str(tags).strip() else []


def _build_history_references(user_id: int, user_request: str, limit: int) -> list[dict[str, Any]]:
    memberships = get_timeline_memberships_for_user(user_id)
    timeline_ids = [timeline.id for timeline, _role in memberships]
    if not timeline_ids:
        return []

    tasks = get_active_tasks_by_timeline_ids(timeline_ids)
    if not tasks:
        return []

    terms = _extract_query_terms(user_request)
    references = []
    for task in tasks:
        normalized_tags = _normalize_task_tags(task.tags)
        haystack = " ".join(
            [
                str(task.name or ""),
                str(task.task_remark or ""),
                " ".join(normalized_tags),
            ]
        ).lower()
        score = 0.0
        if terms:
            match_count = sum(1 for term in terms if term in haystack)
            score = min(1.0, match_count / max(1, len(terms)))
        elif task.completed:
            score = 0.2

        if score <= 0:
            continue

        title = f"Task#{task.task_id} {task.name or '未命名任務'}"
        snippet = (task.task_remark or "").strip()
        if not snippet:
            snippet = f"狀態: {task.status or 'unknown'}，完成: {'是' if task.completed else '否'}"

        references.append(
            {
                "source_type": "timeline_task",
                "source_id": str(task.task_id),
                "title": title[:180],
                "snippet": snippet[:600],
                "score": round(float(score), 4),
            }
        )

    references.sort(key=lambda item: item["score"], reverse=True)
    return references[:limit]


def _build_knowledge_references(
    user_id: int,
    user_request: str,
    limit: int,
    project_id: int | None = None,
) -> list[dict[str, Any]]:
    rows = []
    try:
        embedder = GeminiEmbeddingService()
        query_embedding = embedder.embed_query(user_request)
        rows = search_knowledge_chunks_with_scores(
            user_id=user_id,
            query_embedding=query_embedding,
            limit=limit,
            project_id=project_id,
        )
    except EmbeddingOperationError:
        rows = []
    except Exception:
        rows = []

    if not rows:
        fallback_chunks = search_knowledge_chunks_by_text(
            user_id=user_id,
            query_text=user_request,
            limit=limit,
            project_id=project_id,
        )
        rows = [
            {
                "chunk": chunk,
                "distance": index / max(1, len(fallback_chunks)),
                "retrieval_mode": "text",
            }
            for index, chunk in enumerate(fallback_chunks)
        ]

    references = []
    for row in rows:
        chunk = row["chunk"]
        distance = float(row["distance"])
        score = 1.0 / (1.0 + max(distance, 0.0))
        if row.get("retrieval_mode") == "text":
            score = max(score, 0.5)
        title = f"Document#{chunk.document_id} Chunk#{chunk.chunk_index}"
        references.append(
            {
                "source_type": "knowledge_chunk",
                "source_id": str(chunk.id),
                "title": title[:180],
                "snippet": str(chunk.content or "")[:600],
                "score": round(score, 4),
            }
        )
    return references


def _merge_references(
    history_refs: list[dict[str, Any]],
    knowledge_refs: list[dict[str, Any]],
    max_sources: int,
) -> list[dict[str, Any]]:
    merged = []
    seen = set()

    history_weight = 0.6
    knowledge_weight = 0.4
    for item in history_refs:
        key = (item["source_type"], item["source_id"])
        if key in seen:
            continue
        seen.add(key)
        weighted = dict(item)
        weighted["score"] = round(min(1.0, item["score"] * history_weight), 4)
        merged.append(weighted)

    for item in knowledge_refs:
        key = (item["source_type"], item["source_id"])
        if key in seen:
            continue
        seen.add(key)
        weighted = dict(item)
        weighted["score"] = round(min(1.0, item["score"] * knowledge_weight), 4)
        merged.append(weighted)

    merged.sort(key=lambda item: item["score"], reverse=True)
    return merged[:max_sources]


def _build_retrieval_context(references: list[dict[str, Any]]) -> str:
    if not references:
        return "無可用來源"
    lines = []
    for index, item in enumerate(references, start=1):
        lines.append(
            f"{index}. [{item['source_type']}] ({item['source_id']}) "
            f"{item['title']} | score={item['score']}\n{item['snippet']}"
        )
    return "\n\n".join(lines)


def _fallback_suggestion(user_request: str, references: list[dict[str, Any]]) -> dict[str, Any]:
    reference_titles = [item["title"] for item in references[:3]]
    tag_counter = Counter()
    for item in references:
        title_text = item["title"].lower()
        if "api" in title_text:
            tag_counter["API 設計"] += 1
        if "test" in title_text:
            tag_counter["測試驗證"] += 1
        if "db" in title_text or "document" in title_text:
            tag_counter["資料設計"] += 1

    suggested_tasks = []
    default_task_names = [
        "需求拆解與里程碑定義",
        "核心功能實作",
        "測試驗證與上線準備",
    ]
    for index, task_name in enumerate(default_task_names):
        suggested_tasks.append(
            {
                "name": task_name,
                "reason": f"根據需求「{user_request[:80]}」與歷史來源推估。",
                "priority": "HIGH" if index == 0 else "MEDIUM",
                "estimated_days": 3 + index,
                "depends_on": [default_task_names[index - 1]] if index > 0 else [],
            }
        )

    return {
        "suggested_timeline": {
            "name": "AI 建議專案",
            "objective": f"依據歷史資料與知識庫，完成需求：{user_request[:120]}",
        },
        "suggested_tasks": suggested_tasks,
        "source_references": references,
        "summary": f"主要參考來源：{', '.join(reference_titles) if reference_titles else '無'}",
        "meta": {
            "fallback_used": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signal_tags": list(tag_counter.keys()),
        },
    }


def _generate_rag_plan_with_timeout(llm: Any, user_request: str, retrieval_context: str) -> dict[str, Any]:
    timeout_sec = float(os.getenv("RAG_PLANNING_AI_TIMEOUT_SEC", "25"))
    if timeout_sec <= 0:
        return generate_rag_plan_suggestion(
            llm=llm,
            user_request=user_request,
            retrieval_context=retrieval_context,
        )

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        generate_rag_plan_suggestion,
        llm=llm,
        user_request=user_request,
        retrieval_context=retrieval_context,
    )
    try:
        return future.result(timeout=timeout_sec)
    except FutureTimeoutError as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise RAGPlanningTimeoutError("RAG 規劃生成逾時，已改用降級模式") from exc
    finally:
        if future.done():
            executor.shutdown(wait=False, cancel_futures=True)


def suggest_plan_with_rag(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """使用歷史資料與知識檢索生成規劃建議。

    參數:
        user_id: Request user id.
        payload: RAG request payload including request text and retrieval options.

    回傳:
        AI suggestion payload with source references and metadata.

    例外:
        RAGPlanningOperationError: payload 無效、權限不足或缺少參考資料。
    """
    if not isinstance(payload, dict):
        raise RAGPlanningOperationError("請提供正確的 JSON 物件", 400)

    user_request = _normalize_text(payload.get("request") or payload.get("description") or "")
    if not user_request:
        raise RAGPlanningOperationError("request 不可為空", 400)

    use_personal_knowledge = bool(payload.get("use_personal_knowledge", True))
    use_project_knowledge = bool(payload.get("use_project_knowledge", False))
    project_id = payload.get("project_id")
    if project_id is not None:
        try:
            project_id = int(project_id)
        except (TypeError, ValueError):
            raise RAGPlanningOperationError("project_id 必須為整數", 400)
    max_sources = payload.get("max_sources", 8)
    try:
        max_sources = int(max_sources)
    except (TypeError, ValueError):
        max_sources = 8
    max_sources = min(max(1, max_sources), 20)

    retrieval_top_k = int(os.getenv("RAG_RETRIEVAL_TOP_K", "12"))
    history_refs = _build_history_references(
        user_id=user_id,
        user_request=user_request,
        limit=max(retrieval_top_k // 2, 4),
    )
    knowledge_refs = []
    if use_personal_knowledge:
        knowledge_refs = _build_knowledge_references(
            user_id=user_id,
            user_request=user_request,
            limit=max(retrieval_top_k // 2, 4),
        )

    # project-scoped knowledge
    if use_project_knowledge:
        # 驗證使用者是否為該 project(timeline) 成員
        memberships = get_timeline_memberships_for_user(user_id)
        timeline_ids = [timeline.id for timeline, _role in memberships]
        if not project_id or project_id not in timeline_ids:
            raise RAGPlanningOperationError("沒有權限存取該專案知識或 project_id 錯誤", 403)
        project_refs = _build_knowledge_references(
            user_id=user_id,
            user_request=user_request,
            limit=max(retrieval_top_k // 2, 4),
            project_id=project_id,
        )
        # 標記來源為 project（後端 repository search 會根據 project_id 做篩選）
        # 目前 repository search 已支援 project_id 參數
        # 將 project_refs 併入 knowledge_refs（避免重複）
        existing_keys = {(r['source_type'], r['source_id']) for r in knowledge_refs}
        for r in project_refs:
            key = (r['source_type'], r['source_id'])
            if key not in existing_keys:
                knowledge_refs.append(r)

    merged_refs = _merge_references(
        history_refs=history_refs,
        knowledge_refs=knowledge_refs,
        max_sources=max_sources,
    )
    if not merged_refs:
        raise RAGPlanningOperationError("找不到可用來源，請先補充任務歷史或上傳知識文件", 422)

    retrieval_context = _build_retrieval_context(merged_refs)

    try:
        provider = os.getenv("LLM_PROVIDER", "google-generativeai")
        llm = get_default_llm(provider=provider)
        ai_result = _generate_rag_plan_with_timeout(
            llm=llm,
            user_request=user_request,
            retrieval_context=retrieval_context,
        )
        ai_result["source_references"] = merged_refs
        ai_result["meta"] = {
            "fallback_used": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "use_personal_knowledge": use_personal_knowledge,
            "use_project_knowledge": use_project_knowledge,
            "project_id": project_id,
            "retrieved_history_count": len(history_refs),
            "retrieved_knowledge_count": len(knowledge_refs),
        }
        return build_response_payload(TimelinePlanSuggestionResponse, {
            "message": "AI 規劃建議完成",
            **ai_result,
        }, exclude_none=True)
    except Exception:
        fallback = _fallback_suggestion(user_request=user_request, references=merged_refs)
        fallback["meta"].update(
            {
                "use_personal_knowledge": use_personal_knowledge,
                "use_project_knowledge": use_project_knowledge,
                "project_id": project_id,
                "retrieved_history_count": len(history_refs),
                "retrieved_knowledge_count": len(knowledge_refs),
            }
        )
        return build_response_payload(TimelinePlanSuggestionResponse, {
            "message": "AI 規劃建議完成（降級模式）",
            **fallback,
        }, exclude_none=True)


