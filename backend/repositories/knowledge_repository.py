from sqlalchemy import func

from models import db
from models.knowledge import KnowledgeChunk, KnowledgeDocument


def create_knowledge_document(
    user_id,
    filename,
    sha256,
    status="uploaded",
    mime_type=None,
    size_bytes=None,
    source_text=None,
    error_message=None,
):
    document = KnowledgeDocument(
        user_id=user_id,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        source_text=source_text,
        sha256=sha256,
        status=status,
        error_message=error_message,
    )
    db.session.add(document)
    db.session.flush()
    return document


def get_knowledge_document_by_id(user_id, document_id):
    return KnowledgeDocument.query.filter_by(id=document_id, user_id=user_id).first()


def get_knowledge_document_by_sha256(user_id, sha256):
    return KnowledgeDocument.query.filter_by(user_id=user_id, sha256=sha256).first()


def list_knowledge_documents_for_user(user_id, limit=50, offset=0):
    return (
        KnowledgeDocument.query
        .filter_by(user_id=user_id)
        .order_by(KnowledgeDocument.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_knowledge_document_status(user_id, document_id, status, error_message=None):
    document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    if document is None:
        return None
    document.status = status
    document.error_message = error_message
    return document


def delete_knowledge_document_for_user(user_id, document_id):
    document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    if document is None:
        return False
    db.session.delete(document)
    return True


def replace_knowledge_chunks_for_document(user_id, document_id, chunk_rows):
    KnowledgeChunk.query.filter_by(user_id=user_id, document_id=document_id).delete(
        synchronize_session="fetch"
    )
    db.session.flush()

    objects = []
    for row in chunk_rows:
        chunk = KnowledgeChunk(
            document_id=document_id,
            user_id=user_id,
            chunk_index=int(row.get("chunk_index", 0)),
            token_count=int(row.get("token_count", 0)),
            content=row["content"],
            embedding=row["embedding"],
            chunk_metadata=row.get("metadata") or {},
        )
        objects.append(chunk)

    if objects:
        db.session.add_all(objects)
    return objects


def list_knowledge_chunks_for_document(user_id, document_id):
    return (
        KnowledgeChunk.query
        .filter_by(user_id=user_id, document_id=document_id)
        .order_by(KnowledgeChunk.id.asc())
        .all()
    )


def search_knowledge_chunks_by_l2_distance(user_id, query_embedding, limit=8):
    base_query = KnowledgeChunk.query.filter(KnowledgeChunk.user_id == user_id)
    distance_fn = getattr(KnowledgeChunk.embedding, "l2_distance", None)

    if not callable(distance_fn):
        return []

    return base_query.order_by(distance_fn(query_embedding)).limit(limit).all()


def search_knowledge_chunks_with_scores(user_id, query_embedding, limit=8):
    distance_fn = getattr(KnowledgeChunk.embedding, "l2_distance", None)
    if not callable(distance_fn):
        return []

    distance_expr = distance_fn(query_embedding).label("distance")
    rows = (
        db.session.query(KnowledgeChunk, distance_expr)
        .filter(KnowledgeChunk.user_id == user_id)
        .order_by(distance_expr.asc())
        .limit(limit)
        .all()
    )
    return [{"chunk": chunk, "distance": float(distance)} for chunk, distance in rows]


def count_knowledge_chunks_for_document(user_id, document_id):
    return (
        db.session.query(func.count(KnowledgeChunk.id))
        .filter(
            KnowledgeChunk.user_id == user_id,
            KnowledgeChunk.document_id == document_id,
        )
        .scalar()
    ) or 0
