import os
from collections import Counter
from datetime import datetime, timezone

from chains import generate_rag_plan_suggestion, get_default_llm
from repositories.knowledge_repository import (
    search_knowledge_chunks_with_scores,
)
from repositories.timeline_repository import (
    get_active_tasks_by_timeline_ids,
    get_timeline_memberships_for_user,
)
from services.embedding_service import EmbeddingOperationError, GeminiEmbeddingService


class RAGPlanningOperationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _normalize_text(value):
    if not isinstance(value, str):
        return ""
    return value.strip()


def _extract_query_terms(text):
    separators = ["\n", ",", "，", "。", ".", "、", " ", "\t"]
    normalized = text
    for separator in separators:
        normalized = normalized.replace(separator, "|")
    terms = [item.strip().lower() for item in normalized.split("|") if item.strip()]
    return [item for item in terms if len(item) >= 2]


def _normalize_task_tags(tags):
    if not tags:
        return []
    if isinstance(tags, str):
        return [item.strip() for item in tags.replace("，", ",").split(",") if item.strip()]
    if isinstance(tags, (list, tuple, set)):
        return [str(item).strip() for item in tags if str(item).strip()]
    return [str(tags).strip()] if str(tags).strip() else []


def _build_history_references(user_id, user_request, limit):
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


def _build_knowledge_references(user_id, user_request, limit):
    try:
        embedder = GeminiEmbeddingService()
        query_embedding = embedder.embed_query(user_request)
    except EmbeddingOperationError:
        return []
    except Exception:
        return []

    rows = search_knowledge_chunks_with_scores(
        user_id=user_id,
        query_embedding=query_embedding,
        limit=limit,
    )
    references = []
    for row in rows:
        chunk = row["chunk"]
        distance = float(row["distance"])
        score = 1.0 / (1.0 + max(distance, 0.0))
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


def _merge_references(history_refs, knowledge_refs, max_sources):
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


def _build_retrieval_context(references):
    if not references:
        return "無可用來源"
    lines = []
    for index, item in enumerate(references, start=1):
        lines.append(
            f"{index}. [{item['source_type']}] ({item['source_id']}) "
            f"{item['title']} | score={item['score']}\n{item['snippet']}"
        )
    return "\n\n".join(lines)


def _fallback_suggestion(user_request, references):
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


def suggest_plan_with_rag(user_id, payload):
    if not isinstance(payload, dict):
        raise RAGPlanningOperationError("請提供正確的 JSON 物件", 400)

    user_request = _normalize_text(payload.get("request") or payload.get("description") or "")
    if not user_request:
        raise RAGPlanningOperationError("request 不可為空", 400)

    use_personal_knowledge = bool(payload.get("use_personal_knowledge", True))
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
        ai_result = generate_rag_plan_suggestion(
            llm=llm,
            user_request=user_request,
            retrieval_context=retrieval_context,
        )
        ai_result["source_references"] = merged_refs
        ai_result["meta"] = {
            "fallback_used": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "use_personal_knowledge": use_personal_knowledge,
            "retrieved_history_count": len(history_refs),
            "retrieved_knowledge_count": len(knowledge_refs),
        }
        return {
            "message": "AI 規劃建議完成",
            **ai_result,
        }
    except Exception:
        fallback = _fallback_suggestion(user_request=user_request, references=merged_refs)
        fallback["meta"].update(
            {
                "use_personal_knowledge": use_personal_knowledge,
                "retrieved_history_count": len(history_refs),
                "retrieved_knowledge_count": len(knowledge_refs),
            }
        )
        return {
            "message": "AI 規劃建議完成（降級模式）",
            **fallback,
        }
