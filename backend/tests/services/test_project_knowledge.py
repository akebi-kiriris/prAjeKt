from io import BytesIO
from types import SimpleNamespace

import pytest
from werkzeug.datastructures import FileStorage

from models import db
from models.user import User
from services.knowledge_service import upload_and_index_knowledge_document, list_knowledge_documents
from services.timeline_service import create_timeline_for_user, add_timeline_member_for_owner
from services.rag_planning_service import suggest_plan_with_rag



class _FakeEmbedder:
    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, _text):
        return [0.1, 0.2, 0.3]


class _FakeSplitter:
    def split_document_content(self, user_id, document_id, raw_text):
        content = (raw_text or "").strip()
        return [
            {
                "chunk_index": 0,
                "content": content,
                "metadata": {"token_count": 5},
            }
        ]


def test_project_upload_and_listing_by_member(app, monkeypatch, user_factory):
    monkeypatch.setattr("services.knowledge_service.GeminiEmbeddingService", lambda: _FakeEmbedder())
    monkeypatch.setattr("services.knowledge_service.TextSplitterService", lambda: _FakeSplitter())

    owner = user_factory("proj-owner@example.com", "proj_owner")
    member = user_factory("proj-member@example.com", "proj_member")

    timeline_id = create_timeline_for_user(owner.id, {"name": "Test Project"})
    add_timeline_member_for_owner(timeline_id, member.id, role=1, actor_user_id=owner.id)

    file_obj = FileStorage(
        stream=BytesIO("專案共用文件內容".encode("utf-8")),
        filename="project_notes.md",
        content_type="text/markdown",
    )

    uploaded = upload_and_index_knowledge_document(owner.id, file_obj, project_id=timeline_id)
    assert uploaded["document"]["status"] == "ready"
    assert uploaded["chunk_count"] == 1

    listed = list_knowledge_documents(member.id, project_id=timeline_id)
    assert listed["meta"]["count"] == 1
    assert listed["documents"][0]["project_id"] == timeline_id


def test_suggest_plan_with_project_knowledge_passes_project_id(app, monkeypatch, user_factory):
    owner = user_factory("rag-owner@example.com", "rag_owner")
    member = user_factory("rag-member@example.com", "rag_member")

    timeline_id = create_timeline_for_user(owner.id, {"name": "RAG Project"})
    add_timeline_member_for_owner(timeline_id, member.id, role=1, actor_user_id=owner.id)

    # create a project document as owner
    monkeypatch.setattr("services.knowledge_service.GeminiEmbeddingService", lambda: _FakeEmbedder())
    monkeypatch.setattr("services.knowledge_service.TextSplitterService", lambda: _FakeSplitter())
    upload_and_index_knowledge_document(owner.id, FileStorage(stream=BytesIO("內容".encode("utf-8")), filename="p.md", content_type="text/markdown"), project_id=timeline_id)

    # intercept search to verify project_id passed
    captured = {"project_id": None}

    def fake_search(user_id, query_embedding, limit, project_id=None):
        captured["project_id"] = project_id
        # return a fake chunk row
        return [{"chunk": SimpleNamespace(id=1, document_id=1, chunk_index=0, content="x"), "distance": 0.05}]

    monkeypatch.setattr("services.rag_planning_service.search_knowledge_chunks_with_scores", fake_search)
    monkeypatch.setattr("services.rag_planning_service.GeminiEmbeddingService", lambda: _FakeEmbedder())
    monkeypatch.setattr("services.rag_planning_service.get_default_llm", lambda provider: SimpleNamespace(name="fake"))
    monkeypatch.setattr(
        "services.rag_planning_service.generate_rag_plan_suggestion",
        lambda llm, user_request, retrieval_context: {
            "suggested_timeline": {"name": "fake"},
            "suggested_tasks": [],
            "source_references": [],
            "summary": "ok",
        },
    )

    payload = suggest_plan_with_rag(member.id, {"request": "請做規劃", "use_project_knowledge": True, "project_id": timeline_id})
    assert payload["message"].startswith("AI 規劃建議完成")
    assert captured["project_id"] == timeline_id
