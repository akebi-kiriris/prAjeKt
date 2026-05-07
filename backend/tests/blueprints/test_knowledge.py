from io import BytesIO

from werkzeug.security import generate_password_hash

from models import db
from models.user import User


def _create_user(email: str, password: str, username: str) -> User:
    user = User(
        name="Knowledge Blueprint User",
        username=username,
        email=email,
        password=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def _get_auth_headers(client, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_knowledge_documents_blueprint_flow(client, monkeypatch):
    _create_user(
        email="knowledge-blueprint@example.com",
        password="Password123!",
        username="knowledge_blueprint_user",
    )
    headers = _get_auth_headers(client, "knowledge-blueprint@example.com", "Password123!")

    monkeypatch.setattr(
        "blueprints.knowledge.upload_and_index_knowledge_document",
        lambda user_id, file_storage, project_id=None: {
            "message": "文件上傳與索引完成",
            "document": {"id": 10, "status": "ready", "filename": file_storage.filename},
            "chunk_count": 1,
        },
    )
    monkeypatch.setattr(
        "blueprints.knowledge.list_knowledge_documents",
        lambda user_id, limit, offset, project_id=None, q=None, sort="created_desc", status=None: {
            "message": "知識文件列表",
            "documents": [{"id": 10, "filename": "doc.md", "status": "ready"}],
            "meta": {"limit": limit, "offset": offset, "count": 1},
        },
    )
    monkeypatch.setattr(
        "blueprints.knowledge.delete_knowledge_document",
        lambda user_id, document_id, project_id=None: {
            "message": "知識文件已刪除",
            "document_id": document_id,
        },
    )
    monkeypatch.setattr(
        "blueprints.knowledge.reindex_knowledge_document",
        lambda user_id, document_id, project_id=None: {
            "message": "文件已重新建立索引",
            "document_id": document_id,
            "chunk_count": 2,
        },
    )

    upload = client.post(
        "/api/knowledge/documents",
        headers=headers,
        data={"file": (BytesIO(b"hello"), "doc.md")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 201
    assert upload.get_json()["chunk_count"] == 1

    listed = client.get("/api/knowledge/documents?limit=20&offset=0", headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()["meta"]["count"] == 1

    reindex = client.post("/api/knowledge/documents/10/reindex", headers=headers)
    assert reindex.status_code == 200
    assert reindex.get_json()["chunk_count"] == 2

    deleted = client.delete("/api/knowledge/documents/10", headers=headers)
    assert deleted.status_code == 200
    assert deleted.get_json()["document_id"] == 10
