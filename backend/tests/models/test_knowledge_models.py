import pytest
from sqlalchemy.exc import IntegrityError

from models import db
from models.knowledge import KnowledgeChunk, KnowledgeDocument
from models.user import User


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Knowledge Model User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_knowledge_document_sha256_unique_constraint(app):
    owner = _create_user("knowledge-model-owner@example.com", "knowledge_model_owner")

    first = KnowledgeDocument(
        user_id=owner.id,
        filename="a.md",
        sha256="a" * 64,
        status="uploaded",
    )
    db.session.add(first)
    db.session.commit()

    duplicated = KnowledgeDocument(
        user_id=owner.id,
        filename="b.md",
        sha256="a" * 64,
        status="uploaded",
    )
    db.session.add(duplicated)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_delete_knowledge_document_cascades_chunks(app):
    owner = _create_user("knowledge-model-cascade@example.com", "knowledge_model_cascade")

    document = KnowledgeDocument(
        user_id=owner.id,
        filename="plan.md",
        sha256="b" * 64,
        status="ready",
    )
    db.session.add(document)
    db.session.commit()

    chunk = KnowledgeChunk(
        document_id=document.id,
        user_id=owner.id,
        content="這是一段測試內容。",
        embedding=[0.1, 0.2, 0.3],
        chunk_metadata={"chunk_index": 0},
    )
    db.session.add(chunk)
    db.session.commit()

    chunk_id = chunk.id

    db.session.delete(document)
    db.session.commit()

    assert KnowledgeChunk.query.filter_by(id=chunk_id).first() is None


def test_knowledge_document_same_sha256_allowed_for_different_users(app):
    owner_a = _create_user("knowledge-sha-owner-a@example.com", "knowledge_sha_owner_a")
    owner_b = _create_user("knowledge-sha-owner-b@example.com", "knowledge_sha_owner_b")

    first = KnowledgeDocument(
        user_id=owner_a.id,
        filename="a.md",
        sha256="c" * 64,
        status="uploaded",
    )
    second = KnowledgeDocument(
        user_id=owner_b.id,
        filename="b.md",
        sha256="c" * 64,
        status="uploaded",
    )
    db.session.add_all([first, second])
    db.session.commit()

    assert first.id is not None
    assert second.id is not None
