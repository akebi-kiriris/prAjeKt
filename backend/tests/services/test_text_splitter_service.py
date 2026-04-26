import pytest

from models import db
from models.knowledge import KnowledgeDocument
from models.user import User
from services.text_splitter_service import TextSplitterOperationError, TextSplitterService


def _create_user(email: str, username: str) -> User:
    user = User(
        name="Splitter User",
        username=username,
        email=email,
        password="hashed-password",
    )
    db.session.add(user)
    db.session.commit()
    return user


def _create_document(user_id: int, filename: str, sha_seed: str = "a") -> KnowledgeDocument:
    document = KnowledgeDocument(
        user_id=user_id,
        filename=filename,
        sha256=sha_seed * 64,
        status="uploaded",
    )
    db.session.add(document)
    db.session.commit()
    return document


def test_text_splitter_splits_markdown_heading_then_sentence_level(app):
    user = _create_user("splitter-1@example.com", "splitter_user_1")
    document = _create_document(user.id, "note.md", "c")

    service = TextSplitterService(target_min_tokens=20, target_max_tokens=40, overlap_tokens=8)
    text = (
        "## 章節一\n"
        + "這是一段很長的描述。" * 16
        + "\n### 子章節\n"
        + "這是第二段描述。" * 16
    )

    chunks = service.split_document_content(user_id=user.id, document_id=document.id, raw_text=text)

    assert len(chunks) >= 2
    assert chunks[0]["content"].startswith("## 章節一")
    assert all(item["metadata"]["token_count"] > 0 for item in chunks)

    # 驗證 overlap：第二塊應包含第一塊尾端片段。
    overlap_tail = service._extract_tail_for_overlap(chunks[0]["content"])
    assert overlap_tail
    assert overlap_tail.splitlines()[0] in chunks[1]["content"]


def test_text_splitter_marks_document_failed_on_parse_error(app):
    user = _create_user("splitter-2@example.com", "splitter_user_2")
    document = _create_document(user.id, "broken.md", "d")

    service = TextSplitterService(target_min_tokens=20, target_max_tokens=40, overlap_tokens=8)

    with pytest.raises(TextSplitterOperationError) as exc:
        service.split_document_content(user_id=user.id, document_id=document.id, raw_text="   ")

    db.session.refresh(document)
    assert exc.value.status_code == 422
    assert document.status == "failed"
