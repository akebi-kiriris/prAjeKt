import hashlib
import os
import uuid
from io import BytesIO
from typing import Any

from flask import current_app

from repositories.knowledge_repository import (
    count_knowledge_chunks_for_document,
    create_knowledge_document,
    create_knowledge_document_event,
    delete_knowledge_document as delete_knowledge_document_record,
    delete_knowledge_document_for_user,
    get_knowledge_document_by_id,
    get_knowledge_document_by_project_id,
    get_knowledge_document_by_sha256,
    list_knowledge_document_events,
    list_knowledge_documents_for_user,
    replace_knowledge_chunks_for_document,
    soft_delete_knowledge_document,
    update_knowledge_document_status,
    update_knowledge_document_status_by_id,
)
from repositories.timeline_repository import get_active_timeline_by_id, get_timeline_member
from services.embedding_service import EmbeddingOperationError, GeminiEmbeddingService
from services.text_splitter_service import TextSplitterOperationError, TextSplitterService
from services.transactions import transaction


class KnowledgeOperationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _validate_project_knowledge_membership(user_id: int, project_id: int | None) -> None:
    if project_id is None:
        return

    timeline = get_active_timeline_by_id(project_id)
    if timeline is None:
        raise KnowledgeOperationError("找不到該專案", 404)

    member = get_timeline_member(project_id, user_id)
    if timeline.user_id != user_id and member is None:
        raise KnowledgeOperationError("你沒有權限存取此專案知識", 403)


def _max_upload_bytes() -> int:
    max_mb = int(os.getenv("KNOWLEDGE_UPLOAD_MAX_MB", "10"))
    return max(1, max_mb) * 1024 * 1024


def _allowed_extensions() -> set[str]:
    raw = os.getenv("KNOWLEDGE_ALLOWED_EXTENSIONS", "md,txt,pdf")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _extract_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower().strip()


def _read_uploaded_file(file_storage: Any) -> bytes:
    if not file_storage or not getattr(file_storage, "filename", ""):
        raise KnowledgeOperationError("請提供檔案", 400)

    filename = str(file_storage.filename).strip()
    extension = _extract_extension(filename)
    if extension not in _allowed_extensions():
        raise KnowledgeOperationError("不支援的檔案格式，僅允許 md/txt/pdf", 400)

    file_storage.stream.seek(0, 2)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)

    if file_size <= 0:
        raise KnowledgeOperationError("檔案內容為空", 400)
    if file_size > _max_upload_bytes():
        raise KnowledgeOperationError("檔案超過大小上限", 413)

    payload = file_storage.read()
    if not payload:
        raise KnowledgeOperationError("檔案內容為空", 400)

    return payload


def _decode_text_content(filename: str, payload: bytes) -> str:
    extension = _extract_extension(filename)
    if extension in {"md", "txt"}:
        for encoding in ("utf-8", "utf-8-sig", "big5", "cp950", "latin-1"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise KnowledgeOperationError("文字檔編碼無法解析", 422)

    if extension == "pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise KnowledgeOperationError("缺少 pypdf 套件，暫時無法解析 PDF", 422) from exc

        try:
            reader = PdfReader(BytesIO(payload))
            text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        except Exception as exc:
            raise KnowledgeOperationError("PDF 解析失敗", 422) from exc

        if not text:
            raise KnowledgeOperationError("PDF 沒有可解析文字內容", 422)
        return text

    raise KnowledgeOperationError("不支援的檔案格式", 400)


def _doc_to_dict(document: Any, chunk_count: int | None = None) -> dict[str, Any]:
    return {
        "id": document.id,
        "filename": document.filename,
        "project_id": getattr(document, "project_id", None),
        "mime_type": document.mime_type,
        "file_path": document.file_path,
        "storage_key": document.storage_key,
        "original_filename": document.original_filename,
        "size_bytes": document.size_bytes,
        "has_source_text": bool(document.source_text),
        "chunk_count": chunk_count,
        "sha256": document.sha256,
        "status": document.status,
        "error_message": document.error_message,
        "created_at": document.created_at.isoformat() + "Z" if document.created_at else None,
        "updated_at": document.updated_at.isoformat() + "Z" if document.updated_at else None,
    }


def _event_to_dict(event: Any) -> dict[str, Any]:
    return {
        "id": event.id,
        "document_id": event.document_id,
        "project_id": event.project_id,
        "actor_user_id": event.actor_user_id,
        "event_type": event.event_type,
        "event_payload": event.event_payload or {},
        "created_at": event.created_at.isoformat() + "Z" if event.created_at else None,
    }


def _resolve_project_storage_path(project_id: int, filename: str) -> tuple[str, str]:
    upload_root = current_app.config.get("UPLOAD_FOLDER") or os.path.join(os.path.dirname(__file__), "..", "uploads")
    ext = _extract_extension(filename)
    token = uuid.uuid4().hex
    safe_name = f"{token}.{ext}" if ext else token
    storage_key = f"project_knowledge/{project_id}/{safe_name}"
    abs_path = os.path.join(upload_root, "project_knowledge", str(project_id), safe_name)
    return storage_key, abs_path


def _save_project_file(project_id: int, filename: str, payload: bytes) -> tuple[str, str]:
    storage_key, abs_path = _resolve_project_storage_path(project_id=project_id, filename=filename)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as fh:
        fh.write(payload)
    return storage_key, abs_path


def _delete_physical_file(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def _record_project_document_event(
    document_id: int,
    project_id: int | None,
    actor_user_id: int | None,
    event_type: str,
    event_payload: dict[str, Any] | None = None,
    error_message: str = "建立專案檔案操作紀錄失敗",
) -> None:
    if project_id is None:
        return
    with transaction(KnowledgeOperationError, error_message):
        create_knowledge_document_event(
            document_id=document_id,
            project_id=project_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            event_payload=event_payload or {},
        )


def _create_uploaded_document(
    user_id: int,
    project_id: int | None,
    filename: str,
    sha256: str,
    mime_type: str | None,
    content_size: int,
    text_content: str,
    file_path: str | None = None,
    storage_key: str | None = None,
) -> Any:
    try:
        with transaction(KnowledgeOperationError, "建立知識文件失敗"):
            document = create_knowledge_document(
                user_id=user_id,
                project_id=project_id,
                filename=filename,
                sha256=sha256,
                status="uploaded",
                mime_type=mime_type,
                size_bytes=content_size,
                source_text=text_content,
                file_path=file_path,
                storage_key=storage_key,
                original_filename=filename,
            )
            if project_id is not None:
                create_knowledge_document_event(
                    document_id=document.id,
                    project_id=project_id,
                    actor_user_id=user_id,
                    event_type="upload",
                    event_payload={"filename": filename, "size_bytes": content_size},
                )
            return document
    except KnowledgeOperationError:
        _delete_physical_file(file_path)
        raise


def _mark_document_indexing(user_id: int, document_id: int) -> None:
    with transaction(KnowledgeOperationError, "更新知識文件狀態失敗"):
        update_knowledge_document_status(user_id=user_id, document_id=document_id, status="indexing")


def _mark_document_indexing_by_id(document_id: int) -> None:
    with transaction(KnowledgeOperationError, "更新知識文件狀態失敗"):
        update_knowledge_document_status_by_id(document_id=document_id, status="indexing")


def _build_chunk_rows(chunks: list[dict[str, Any]], embeddings: list[list[float]]) -> list[dict[str, Any]]:
    chunk_rows = []
    for chunk, embedding in zip(chunks, embeddings):
        metadata = dict(chunk.get("metadata") or {})
        token_count = int(metadata.get("token_count") or 0)
        chunk_rows.append(
            {
                "chunk_index": int(chunk.get("chunk_index") or 0),
                "token_count": token_count,
                "content": chunk["content"],
                "embedding": embedding,
                "metadata": metadata,
            }
        )
    return chunk_rows


def _replace_chunks_and_mark_ready(
    user_id: int,
    document_id: int,
    chunk_rows: list[dict[str, Any]],
    project_id: int | None = None,
) -> None:
    with transaction(KnowledgeOperationError, "索引流程失敗"):
        replace_knowledge_chunks_for_document(
            user_id=user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
            project_id=project_id,
        )
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="ready",
            error_message=None,
        )


def _replace_chunks_and_mark_ready_by_id(
    user_id: int,
    document_id: int,
    chunk_rows: list[dict[str, Any]],
    project_id: int | None = None,
) -> None:
    with transaction(KnowledgeOperationError, "重建索引失敗"):
        replace_knowledge_chunks_for_document(
            user_id=user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
            project_id=project_id,
        )
        update_knowledge_document_status_by_id(
            document_id=document_id,
            status="ready",
            error_message=None,
        )


def _mark_document_failed(user_id: int, document_id: int, error_message: str) -> None:
    with transaction(KnowledgeOperationError, "更新知識文件失敗狀態失敗"):
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="failed",
            error_message=error_message,
        )


def _mark_document_failed_by_id(document_id: int, error_message: str) -> None:
    with transaction(KnowledgeOperationError, "更新知識文件失敗狀態失敗"):
        update_knowledge_document_status_by_id(
            document_id=document_id,
            status="failed",
            error_message=error_message,
        )


def upload_and_index_knowledge_document(
    user_id: int,
    file_storage: Any,
    project_id: int | None = None,
) -> dict[str, Any]:
    """上傳單一知識文件並完成切塊、向量化與索引入庫。

    參數:
        user_id: 擁有者使用者 id。
        file_storage: 上傳檔案物件。
        project_id: 可選的專案範圍知識 id。

    回傳:
        含文件資訊與切塊數量的回應資料。

    例外:
        KnowledgeOperationError: 驗證失敗、解析失敗、向量化失敗或資料寫入失敗。
    """
    _validate_project_knowledge_membership(user_id=user_id, project_id=project_id)
    content_bytes = _read_uploaded_file(file_storage)
    filename = str(file_storage.filename).strip()
    mime_type = getattr(file_storage, "mimetype", None)
    sha256 = hashlib.sha256(content_bytes).hexdigest()

    if project_id is None and get_knowledge_document_by_sha256(user_id=user_id, sha256=sha256):
        raise KnowledgeOperationError("相同內容的文件已存在", 409)

    text_content = _decode_text_content(filename, content_bytes)
    storage_key = None
    file_path = None
    if project_id is not None:
        storage_key, file_path = _save_project_file(project_id=project_id, filename=filename, payload=content_bytes)

    splitter = TextSplitterService()
    embedder = GeminiEmbeddingService()

    document = _create_uploaded_document(
        user_id=user_id,
        project_id=project_id,
        filename=filename,
        sha256=sha256,
        mime_type=mime_type,
        content_size=len(content_bytes),
        text_content=text_content,
        file_path=file_path,
        storage_key=storage_key,
    )

    document_id = document.id
    try:
        _mark_document_indexing(user_id=user_id, document_id=document_id)

        chunks = splitter.split_document_content(
            user_id=user_id,
            document_id=document_id,
            raw_text=text_content,
        )
        embeddings = embedder.embed_documents([item["content"] for item in chunks])
        chunk_rows = _build_chunk_rows(chunks=chunks, embeddings=embeddings)

        _replace_chunks_and_mark_ready(
            user_id=user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
            project_id=project_id,
        )
    except (TextSplitterOperationError, EmbeddingOperationError, KnowledgeOperationError) as exc:
        _mark_document_failed(user_id=user_id, document_id=document_id, error_message=str(exc))
        _record_project_document_event(
            document_id=document_id,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="index_failed",
            event_payload={"error_message": str(exc)},
        )
        raise KnowledgeOperationError(str(exc), getattr(exc, "status_code", 422))
    except Exception as exc:
        _mark_document_failed(user_id=user_id, document_id=document_id, error_message="索引流程失敗")
        _record_project_document_event(
            document_id=document_id,
            project_id=project_id,
            actor_user_id=user_id,
            event_type="index_failed",
            event_payload={"error_message": "索引流程失敗"},
        )
        raise KnowledgeOperationError("索引流程失敗", 500) from exc

    _record_project_document_event(
        document_id=document_id,
        project_id=project_id,
        actor_user_id=user_id,
        event_type="indexed",
        event_payload={"chunk_count": len(chunks)},
    )

    refreshed = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    return {
        "message": "文件上傳與索引完成",
        "document": _doc_to_dict(refreshed),
        "chunk_count": count_knowledge_chunks_for_document(user_id=user_id, document_id=document_id, project_id=project_id),
    }


def list_knowledge_documents(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    project_id: int | None = None,
    q: str | None = None,
    sort: str = "created_desc",
    status: str | None = None,
) -> dict[str, Any]:
    """列出知識文件，支援查詢與排序選項。"""
    _validate_project_knowledge_membership(user_id=user_id, project_id=project_id)
    docs = list_knowledge_documents_for_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
        query_text=q,
        sort=sort,
        status=status,
    )
    return {
        "message": "知識文件列表",
        "documents": [
            _doc_to_dict(
                document,
                chunk_count=count_knowledge_chunks_for_document(
                    user_id=user_id,
                    document_id=document.id,
                    project_id=project_id,
                ),
            )
            for document in docs
        ],
        "meta": {
            "limit": limit,
            "offset": offset,
            "count": len(docs),
        },
    }


def _resolve_document_for_operation(
    user_id: int,
    document_id: int,
    project_id: int | None = None,
) -> Any:
    if project_id is not None:
        return get_knowledge_document_by_project_id(document_id=document_id, project_id=project_id)
    return get_knowledge_document_by_id(user_id=user_id, document_id=document_id)


def delete_knowledge_document(user_id: int, document_id: int, project_id: int | None = None) -> dict[str, Any]:
    """刪除單一知識文件（個人文件為硬刪除、專案文件為軟刪除）。

    例外:
        KnowledgeOperationError: 文件不存在或刪除失敗。
    """
    _validate_project_knowledge_membership(user_id=user_id, project_id=project_id)
    document = _resolve_document_for_operation(user_id=user_id, document_id=document_id, project_id=project_id)
    if document is None:
        raise KnowledgeOperationError("找不到知識文件", 404)

    with transaction(KnowledgeOperationError, "刪除知識文件失敗"):
        if project_id is not None:
            soft_delete_knowledge_document(document)
            _delete_physical_file(document.file_path)
            create_knowledge_document_event(
                document_id=document.id,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="delete",
                event_payload={"filename": document.filename},
            )
        else:
            delete_knowledge_document_for_user(user_id=user_id, document_id=document_id)

    return {"message": "知識文件已刪除", "document_id": document_id}


def reindex_knowledge_document(user_id: int, document_id: int, project_id: int | None = None) -> dict[str, Any]:
    """針對既有文件重建切塊與向量索引。

    例外:
        KnowledgeOperationError: 來源文字無效或重建索引失敗。
    """
    _validate_project_knowledge_membership(user_id=user_id, project_id=project_id)
    document = _resolve_document_for_operation(user_id=user_id, document_id=document_id, project_id=project_id)
    if document is None:
        raise KnowledgeOperationError("找不到知識文件", 404)

    raw_text = (document.source_text or "").strip()
    if not raw_text:
        raise KnowledgeOperationError("文件缺少原始內容，請重新上傳後再重建索引", 400)

    owner_user_id = int(document.user_id)
    resolved_project_id = getattr(document, "project_id", None)
    splitter = TextSplitterService()
    embedder = GeminiEmbeddingService()

    try:
        _mark_document_indexing_by_id(document_id=document_id)

        chunks = splitter.split_document_content(
            user_id=owner_user_id,
            document_id=document_id,
            raw_text=raw_text,
        )
        embeddings = embedder.embed_documents([item["content"] for item in chunks])
        chunk_rows = _build_chunk_rows(chunks=chunks, embeddings=embeddings)

        _replace_chunks_and_mark_ready_by_id(
            user_id=owner_user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
            project_id=resolved_project_id,
        )
    except (TextSplitterOperationError, EmbeddingOperationError, KnowledgeOperationError) as exc:
        _mark_document_failed_by_id(document_id=document_id, error_message=str(exc))
        raise KnowledgeOperationError(str(exc), getattr(exc, "status_code", 422))
    except Exception as exc:
        _mark_document_failed_by_id(document_id=document_id, error_message="重建索引失敗")
        raise KnowledgeOperationError("重建索引失敗", 500) from exc

    _record_project_document_event(
        document_id=document_id,
        project_id=project_id,
        actor_user_id=user_id,
        event_type="reindex",
        event_payload={"chunk_count": len(chunks)},
    )

    return {
        "message": "文件已重新建立索引",
        "document_id": document_id,
        "chunk_count": count_knowledge_chunks_for_document(
            user_id=owner_user_id,
            document_id=document_id,
            project_id=resolved_project_id,
        ),
    }


def batch_delete_knowledge_documents(
    user_id: int,
    project_id: int,
    document_ids: list[int],
) -> dict[str, Any]:
    """批次刪除專案知識文件，並回傳逐筆結果摘要。"""
    results = []
    for raw_id in document_ids:
        document_id = int(raw_id)
        try:
            delete_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
            results.append({"document_id": document_id, "success": True})
        except KnowledgeOperationError as err:
            results.append({"document_id": document_id, "success": False, "error": err.message})
    success_count = len([item for item in results if item["success"]])
    return {
        "message": "批次刪除完成",
        "project_id": project_id,
        "results": results,
        "meta": {"total": len(results), "success": success_count, "failed": len(results) - success_count},
    }


def batch_reindex_knowledge_documents(
    user_id: int,
    project_id: int,
    document_ids: list[int],
) -> dict[str, Any]:
    """批次重建專案知識文件索引，並回傳逐筆結果摘要。"""
    results = []
    for raw_id in document_ids:
        document_id = int(raw_id)
        try:
            payload = reindex_knowledge_document(user_id=user_id, document_id=document_id, project_id=project_id)
            _record_project_document_event(
                document_id=document_id,
                project_id=project_id,
                actor_user_id=user_id,
                event_type="reindex",
                event_payload={"chunk_count": payload.get("chunk_count", 0)},
                error_message="建立重建索引紀錄失敗",
            )
            results.append({"document_id": document_id, "success": True, "chunk_count": payload.get("chunk_count", 0)})
        except KnowledgeOperationError as err:
            results.append({"document_id": document_id, "success": False, "error": err.message})
    success_count = len([item for item in results if item["success"]])
    return {
        "message": "批次重建完成",
        "project_id": project_id,
        "results": results,
        "meta": {"total": len(results), "success": success_count, "failed": len(results) - success_count},
    }


def get_project_knowledge_document_file(
    user_id: int,
    project_id: int,
    document_id: int,
    event_type: str = "download",
) -> Any:
    """解析專案知識檔案供下載/開啟流程使用。"""
    _validate_project_knowledge_membership(user_id=user_id, project_id=project_id)
    document = _resolve_document_for_operation(user_id=user_id, document_id=document_id, project_id=project_id)
    if document is None or document.deleted_at is not None:
        raise KnowledgeOperationError("找不到知識文件", 404)
    if not document.file_path or not os.path.exists(document.file_path):
        raise KnowledgeOperationError("檔案不存在", 404)
    _record_project_document_event(
        document_id=document.id,
        project_id=project_id,
        actor_user_id=user_id,
        event_type=event_type,
        event_payload={"filename": document.filename},
        error_message="建立檔案操作紀錄失敗",
    )
    return document


def list_project_knowledge_events(project_id: int, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """列出專案知識操作事件。"""
    events = list_knowledge_document_events(project_id=project_id, limit=limit, offset=offset)
    return {
        "message": "專案檔案操作紀錄",
        "events": [_event_to_dict(event) for event in events],
        "meta": {"limit": limit, "offset": offset, "count": len(events)},
    }


