import hashlib
import os
from io import BytesIO
from typing import Any

from models import db
from repositories.knowledge_repository import (
    count_knowledge_chunks_for_document,
    create_knowledge_document,
    delete_knowledge_document_for_user,
    get_knowledge_document_by_id,
    get_knowledge_document_by_sha256,
    list_knowledge_documents_for_user,
    replace_knowledge_chunks_for_document,
    update_knowledge_document_status,
)
from services.embedding_service import EmbeddingOperationError, GeminiEmbeddingService
from services.text_splitter_service import TextSplitterOperationError, TextSplitterService


class KnowledgeOperationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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


def _doc_to_dict(document):
    return {
        "id": document.id,
        "filename": document.filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "has_source_text": bool(document.source_text),
        "sha256": document.sha256,
        "status": document.status,
        "error_message": document.error_message,
        "created_at": document.created_at.isoformat() + "Z" if document.created_at else None,
        "updated_at": document.updated_at.isoformat() + "Z" if document.updated_at else None,
    }


def upload_and_index_knowledge_document(user_id, file_storage):
    content_bytes = _read_uploaded_file(file_storage)
    filename = str(file_storage.filename).strip()
    mime_type = getattr(file_storage, "mimetype", None)
    sha256 = hashlib.sha256(content_bytes).hexdigest()

    if get_knowledge_document_by_sha256(user_id=user_id, sha256=sha256):
        raise KnowledgeOperationError("相同內容的文件已存在", 409)

    text_content = _decode_text_content(filename, content_bytes)

    splitter = TextSplitterService()
    embedder = GeminiEmbeddingService()

    try:
        document = create_knowledge_document(
            user_id=user_id,
            filename=filename,
            sha256=sha256,
            status="uploaded",
            mime_type=mime_type,
            size_bytes=len(content_bytes),
            source_text=text_content,
        )
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise KnowledgeOperationError("建立知識文件失敗", 500) from exc

    document_id = document.id
    try:
        update_knowledge_document_status(user_id=user_id, document_id=document_id, status="indexing")
        db.session.commit()

        chunks = splitter.split_document_content(
            user_id=user_id,
            document_id=document_id,
            raw_text=text_content,
        )
        embeddings = embedder.embed_documents([item["content"] for item in chunks])

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

        replace_knowledge_chunks_for_document(
            user_id=user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
        )
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="ready",
            error_message=None,
        )
        db.session.commit()
    except (TextSplitterOperationError, EmbeddingOperationError, KnowledgeOperationError) as exc:
        db.session.rollback()
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="failed",
            error_message=str(exc),
        )
        db.session.commit()
        raise KnowledgeOperationError(str(exc), getattr(exc, "status_code", 422))
    except Exception as exc:
        db.session.rollback()
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="failed",
            error_message="索引流程失敗",
        )
        db.session.commit()
        raise KnowledgeOperationError("索引流程失敗", 500) from exc

    refreshed = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    return {
        "message": "文件上傳與索引完成",
        "document": _doc_to_dict(refreshed),
        "chunk_count": count_knowledge_chunks_for_document(user_id=user_id, document_id=document_id),
    }


def list_knowledge_documents(user_id, limit=50, offset=0):
    docs = list_knowledge_documents_for_user(user_id=user_id, limit=limit, offset=offset)
    return {
        "message": "知識文件列表",
        "documents": [_doc_to_dict(document) for document in docs],
        "meta": {
            "limit": limit,
            "offset": offset,
            "count": len(docs),
        },
    }


def delete_knowledge_document(user_id, document_id):
    if not get_knowledge_document_by_id(user_id=user_id, document_id=document_id):
        raise KnowledgeOperationError("找不到知識文件", 404)

    try:
        delete_knowledge_document_for_user(user_id=user_id, document_id=document_id)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        raise KnowledgeOperationError("刪除知識文件失敗", 500) from exc

    return {"message": "知識文件已刪除", "document_id": document_id}


def reindex_knowledge_document(user_id, document_id):
    document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    if document is None:
        raise KnowledgeOperationError("找不到知識文件", 404)

    raw_text = (document.source_text or "").strip()
    if not raw_text:
        raise KnowledgeOperationError("文件缺少原始內容，請重新上傳後再重建索引", 400)

    splitter = TextSplitterService()
    embedder = GeminiEmbeddingService()

    try:
        update_knowledge_document_status(user_id=user_id, document_id=document_id, status="indexing")
        db.session.commit()

        chunks = splitter.split_document_content(
            user_id=user_id,
            document_id=document_id,
            raw_text=raw_text,
        )
        embeddings = embedder.embed_documents([item["content"] for item in chunks])
        chunk_rows = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = dict(chunk.get("metadata") or {})
            chunk_rows.append(
                {
                    "chunk_index": int(chunk.get("chunk_index") or 0),
                    "token_count": int(metadata.get("token_count") or 0),
                    "content": chunk["content"],
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )

        replace_knowledge_chunks_for_document(
            user_id=user_id,
            document_id=document_id,
            chunk_rows=chunk_rows,
        )
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="ready",
            error_message=None,
        )
        db.session.commit()
    except (TextSplitterOperationError, EmbeddingOperationError, KnowledgeOperationError) as exc:
        db.session.rollback()
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="failed",
            error_message=str(exc),
        )
        db.session.commit()
        raise KnowledgeOperationError(str(exc), getattr(exc, "status_code", 422))
    except Exception as exc:
        db.session.rollback()
        update_knowledge_document_status(
            user_id=user_id,
            document_id=document_id,
            status="failed",
            error_message="重建索引失敗",
        )
        db.session.commit()
        raise KnowledgeOperationError("重建索引失敗", 500) from exc

    return {
        "message": "文件已重新建立索引",
        "document_id": document_id,
        "chunk_count": count_knowledge_chunks_for_document(user_id=user_id, document_id=document_id),
    }
