from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from models import db
from models.knowledge import KnowledgeDocument
from models.user import User
from services.knowledge_service import (
    KnowledgeOperationError,
    delete_knowledge_document,
    list_knowledge_documents,
    reindex_knowledge_document,
    upload_and_index_knowledge_document,
)


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Knowledge Service User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


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


def test_upload_and_reindex_and_delete_knowledge_document(app, monkeypatch):
    monkeypatch.setattr("services.knowledge_service.GeminiEmbeddingService", lambda: _FakeEmbedder())
    monkeypatch.setattr("services.knowledge_service.TextSplitterService", lambda: _FakeSplitter())

    owner = _create_user("knowledge-service-owner@example.com", "knowledge_service_owner")
    file_obj = FileStorage(
        stream=BytesIO("這是測試文件內容".encode("utf-8")),
        filename="notes.md",
        content_type="text/markdown",
    )

    uploaded = upload_and_index_knowledge_document(owner.id, file_obj)
    assert uploaded["document"]["status"] == "ready"
    assert uploaded["chunk_count"] == 1

    listed = list_knowledge_documents(owner.id)
    assert listed["meta"]["count"] == 1
    document_id = listed["documents"][0]["id"]

    reindexed = reindex_knowledge_document(owner.id, document_id)
    assert reindexed["chunk_count"] == 1

    deleted = delete_knowledge_document(owner.id, document_id)
    assert deleted["document_id"] == document_id

    listed_after_delete = list_knowledge_documents(owner.id)
    assert listed_after_delete["meta"]["count"] == 0


def test_upload_knowledge_document_deduplicates_by_user(app, monkeypatch):
    monkeypatch.setattr("services.knowledge_service.GeminiEmbeddingService", lambda: _FakeEmbedder())
    monkeypatch.setattr("services.knowledge_service.TextSplitterService", lambda: _FakeSplitter())

    owner = _create_user("knowledge-dedupe-owner@example.com", "knowledge_dedupe_owner")
    same_content = "同一份內容"

    upload_and_index_knowledge_document(
        owner.id,
        FileStorage(stream=BytesIO(same_content.encode("utf-8")), filename="a.md", content_type="text/markdown"),
    )

    with pytest.raises(KnowledgeOperationError) as exc:
        upload_and_index_knowledge_document(
            owner.id,
            FileStorage(stream=BytesIO(same_content.encode("utf-8")), filename="b.md", content_type="text/markdown"),
        )
    assert exc.value.status_code == 409


def test_reindex_requires_source_text(app):
    owner = _create_user("knowledge-reindex-source@example.com", "knowledge_reindex_source")
    document = KnowledgeDocument(
        user_id=owner.id,
        filename="legacy.md",
        sha256="d" * 64,
        status="ready",
        source_text=None,
    )
    db.session.add(document)
    db.session.commit()

    with pytest.raises(KnowledgeOperationError) as exc:
        reindex_knowledge_document(owner.id, document.id)

    assert exc.value.status_code == 400
    assert "請重新上傳" in exc.value.message
