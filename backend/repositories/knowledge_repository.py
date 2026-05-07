from sqlalchemy import func, or_

from models import db
from models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentEvent


def create_knowledge_document(
    user_id,
    filename,
    sha256,
    project_id=None,
    status="uploaded",
    mime_type=None,
    size_bytes=None,
    source_text=None,
    error_message=None,
    file_path=None,
    storage_key=None,
    original_filename=None,
):
    document = KnowledgeDocument(
        user_id=user_id,
        project_id=project_id,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        source_text=source_text,
        sha256=sha256,
        status=status,
        error_message=error_message,
        file_path=file_path,
        storage_key=storage_key,
        original_filename=original_filename,
    )
    db.session.add(document)
    db.session.flush()
    return document


def get_knowledge_document_by_id(user_id, document_id):
    query = KnowledgeDocument.query.filter_by(id=document_id, user_id=user_id)
    return query.first()


def get_knowledge_document_by_project_id(document_id, project_id):
    if project_id is None:
        return None
    return KnowledgeDocument.query.filter_by(id=document_id, project_id=project_id).first()


def get_knowledge_document_by_sha256(user_id, sha256):
    return KnowledgeDocument.query.filter_by(user_id=user_id, sha256=sha256).first()


def list_knowledge_documents_for_user(
    user_id,
    limit=50,
    offset=0,
    project_id=None,
    query_text=None,
    sort="created_desc",
    status=None,
):
    if project_id is not None:
        query = KnowledgeDocument.query.filter_by(project_id=project_id)
    else:
        query = KnowledgeDocument.query.filter_by(user_id=user_id)
    query = query.filter(KnowledgeDocument.deleted_at.is_(None))
    if query_text:
        query = query.filter(KnowledgeDocument.filename.ilike(f"%{query_text.strip()}%"))
    if status:
        query = query.filter(KnowledgeDocument.status == status)

    if sort == "created_asc":
        query = query.order_by(KnowledgeDocument.created_at.asc())
    elif sort == "name_asc":
        query = query.order_by(KnowledgeDocument.filename.asc(), KnowledgeDocument.created_at.desc())
    elif sort == "name_desc":
        query = query.order_by(KnowledgeDocument.filename.desc(), KnowledgeDocument.created_at.desc())
    elif sort == "status_asc":
        query = query.order_by(KnowledgeDocument.status.asc(), KnowledgeDocument.created_at.desc())
    else:
        query = query.order_by(KnowledgeDocument.created_at.desc())
    return query.offset(offset).limit(limit).all()


def update_knowledge_document_status(user_id, document_id, status, error_message=None):
    document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    if document is None:
        return None
    document.status = status
    document.error_message = error_message
    return document


def update_knowledge_document_status_by_id(document_id, status, error_message=None):
    document = KnowledgeDocument.query.filter_by(id=document_id).first()
    if document is None:
        return None
    document.status = status
    document.error_message = error_message
    return document


def soft_delete_knowledge_document(document):
    if document is None:
        return False
    document.deleted_at = func.now()
    return True


def delete_knowledge_document_for_user(user_id, document_id):
    document = get_knowledge_document_by_id(user_id=user_id, document_id=document_id)
    if document is None:
        return False
    db.session.delete(document)
    return True


def delete_knowledge_document(document):
    if document is None:
        return False
    db.session.delete(document)
    return True


def replace_knowledge_chunks_for_document(user_id, document_id, chunk_rows, project_id=None):
    if project_id is not None:
        q = KnowledgeChunk.query.filter_by(document_id=document_id, project_id=project_id)
    else:
        q = KnowledgeChunk.query.filter_by(user_id=user_id, document_id=document_id)
    q.delete(synchronize_session="fetch")
    db.session.flush()

    objects = []
    for row in chunk_rows:
        chunk = KnowledgeChunk(
            document_id=document_id,
            user_id=user_id,
            project_id=row.get("project_id", project_id) if project_id is not None else row.get("project_id"),
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


def list_knowledge_chunks_for_document(user_id, document_id, project_id=None):
    if project_id is not None:
        query = KnowledgeChunk.query.filter_by(document_id=document_id, project_id=project_id)
    else:
        query = KnowledgeChunk.query.filter_by(user_id=user_id, document_id=document_id)
    return query.order_by(KnowledgeChunk.id.asc()).all()


def search_knowledge_chunks_by_l2_distance(user_id, query_embedding, limit=8, project_id=None):
    if project_id is not None:
        base_query = KnowledgeChunk.query.filter(KnowledgeChunk.project_id == project_id)
    else:
        base_query = KnowledgeChunk.query.filter(KnowledgeChunk.user_id == user_id)
    distance_fn = getattr(KnowledgeChunk.embedding, "l2_distance", None)

    if not callable(distance_fn):
        return []

    return base_query.order_by(distance_fn(query_embedding)).limit(limit).all()


def search_knowledge_chunks_with_scores(user_id, query_embedding, limit=8, project_id=None):
    distance_fn = getattr(KnowledgeChunk.embedding, "l2_distance", None)
    if not callable(distance_fn):
        return []

    distance_expr = distance_fn(query_embedding).label("distance")
    q = (
        db.session.query(KnowledgeChunk, distance_expr)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .filter(KnowledgeDocument.status == "ready", KnowledgeDocument.deleted_at.is_(None))
    )
    if project_id is not None:
        q = q.filter(KnowledgeChunk.project_id == project_id)
    else:
        q = q.filter(KnowledgeChunk.user_id == user_id, KnowledgeChunk.project_id.is_(None))
    rows = q.order_by(distance_expr.asc()).limit(limit).all()
    return [{"chunk": chunk, "distance": float(distance)} for chunk, distance in rows]


def search_knowledge_chunks_by_text(user_id, query_text, limit=8, project_id=None):
    text = (query_text or "").strip()
    query = (
        KnowledgeChunk.query
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .filter(KnowledgeDocument.status == "ready", KnowledgeDocument.deleted_at.is_(None))
    )
    if project_id is not None:
        query = query.filter(KnowledgeChunk.project_id == project_id)
    else:
        query = query.filter(KnowledgeChunk.user_id == user_id, KnowledgeChunk.project_id.is_(None))

    if text:
        normalized = text
        for separator in ("\n", ",", "，", "。", ".", "、", " ", "\t"):
            normalized = normalized.replace(separator, "|")
        terms = [term.strip() for term in normalized.split("|") if len(term.strip()) >= 2]
        if terms:
            term_filters = [KnowledgeChunk.content.ilike(f"%{term}%") for term in terms[:8]]
            matched = (
                query.filter(or_(*term_filters))
                .order_by(KnowledgeChunk.id.desc())
                .limit(limit)
                .all()
            )
            if matched:
                return matched

    return query.order_by(KnowledgeChunk.id.desc()).limit(limit).all()


def count_knowledge_chunks_for_document(user_id, document_id, project_id=None):
    q = db.session.query(func.count(KnowledgeChunk.id)).filter(
        KnowledgeChunk.document_id == document_id,
    )
    if project_id is not None:
        q = q.filter(KnowledgeChunk.project_id == project_id)
    else:
        q = q.filter(KnowledgeChunk.user_id == user_id)
    return q.scalar() or 0


def create_knowledge_document_event(
    document_id,
    project_id,
    actor_user_id,
    event_type,
    event_payload=None,
):
    event = KnowledgeDocumentEvent(
        document_id=document_id,
        project_id=project_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        event_payload=event_payload or {},
    )
    db.session.add(event)
    db.session.flush()
    return event


def list_knowledge_document_events(project_id, limit=50, offset=0):
    return (
        KnowledgeDocumentEvent.query.filter_by(project_id=project_id)
        .order_by(KnowledgeDocumentEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
