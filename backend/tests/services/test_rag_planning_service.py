from types import SimpleNamespace

import pytest

from services.rag_planning_service import (
    RAGPlanningOperationError,
    _build_history_references,
    suggest_plan_with_rag,
)


def test_suggest_plan_with_rag_uses_retrieval_and_returns_structure(monkeypatch):
    monkeypatch.setattr(
        "services.rag_planning_service._build_history_references",
        lambda user_id, user_request, limit: [
            {
                "source_type": "timeline_task",
                "source_id": "11",
                "title": "Task#11 API 設計",
                "snippet": "先定義契約",
                "score": 0.9,
            }
        ],
    )
    monkeypatch.setattr(
        "services.rag_planning_service._build_knowledge_references",
        lambda user_id, user_request, limit: [
            {
                "source_type": "knowledge_chunk",
                "source_id": "21",
                "title": "Document#2 Chunk#1",
                "snippet": "RAG 檢索流程",
                "score": 0.7,
            }
        ],
    )
    monkeypatch.setattr(
        "services.rag_planning_service.get_default_llm",
        lambda provider: SimpleNamespace(name="fake-llm"),
    )
    monkeypatch.setattr(
        "services.rag_planning_service.generate_rag_plan_suggestion",
        lambda llm, user_request, retrieval_context: {
            "suggested_timeline": {"name": "RAG 專案", "objective": "完成 7.3"},
            "suggested_tasks": [
                {
                    "name": "完成 API",
                    "reason": "需要先接前後端",
                    "priority": "HIGH",
                    "estimated_days": 3,
                    "depends_on": [],
                }
            ],
            "source_references": [],
            "summary": "先做資料層，再做服務層",
        },
    )

    payload = suggest_plan_with_rag(
        user_id=1,
        payload={"request": "請規劃 7.3 後端", "use_personal_knowledge": True, "max_sources": 5},
    )
    assert payload["message"] == "AI 規劃建議完成"
    assert payload["suggested_timeline"]["name"] == "RAG 專案"
    assert payload["meta"]["fallback_used"] is False
    assert len(payload["source_references"]) == 2


def test_suggest_plan_with_rag_requires_references(monkeypatch):
    monkeypatch.setattr("services.rag_planning_service._build_history_references", lambda *args, **kwargs: [])
    monkeypatch.setattr("services.rag_planning_service._build_knowledge_references", lambda *args, **kwargs: [])

    with pytest.raises(RAGPlanningOperationError) as exc:
        suggest_plan_with_rag(user_id=1, payload={"request": "請規劃"})
    assert exc.value.status_code == 422


def test_build_history_references_parses_string_tags(monkeypatch):
    fake_timeline = SimpleNamespace(id=100)
    fake_task = SimpleNamespace(
        task_id=77,
        name="RAG API",
        task_remark="完成規劃接口",
        tags="後端,API,測試",
        completed=False,
        status="doing",
    )

    monkeypatch.setattr(
        "services.rag_planning_service.get_timeline_memberships_for_user",
        lambda _user_id: [(fake_timeline, "owner")],
    )
    monkeypatch.setattr(
        "services.rag_planning_service.get_active_tasks_by_timeline_ids",
        lambda _ids: [fake_task],
    )

    refs = _build_history_references(user_id=1, user_request="想做 API", limit=5)
    assert len(refs) == 1
    assert refs[0]["source_id"] == "77"
    assert refs[0]["score"] > 0
