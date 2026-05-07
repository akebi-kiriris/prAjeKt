import os

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from models import db
from models.time_utils import utcnow_naive

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = None


def _resolve_embedding_dim() -> int:
    raw_value = (os.getenv("EMBEDDING_DIM") or "3072").strip()
    try:
        value = int(raw_value)
        return value if value > 0 else 3072
    except ValueError:
        return 3072


def _build_embedding_type():
    base_type = sa.JSON()
    if Vector is None:
        return base_type
    return base_type.with_variant(Vector(_resolve_embedding_dim()), "postgresql")


def _build_metadata_type():
    return sa.JSON().with_variant(JSONB(astext_type=sa.Text()), "postgresql")


class KnowledgeDocument(db.Model):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('uploaded', 'indexing', 'ready', 'failed')",
            name="ck_knowledge_documents_status",
        ),
        db.UniqueConstraint("user_id", "sha256", name="uq_knowledge_documents_user_sha256"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    file_path = db.Column(db.Text, nullable=True)
    storage_key = db.Column(db.String(255), nullable=True, index=True)
    original_filename = db.Column(db.String(255), nullable=True)
    source_text = db.Column(db.Text, nullable=True)
    sha256 = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="uploaded")
    error_message = db.Column(db.Text, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=utcnow_naive,
        onupdate=utcnow_naive,
        nullable=False,
    )

    chunks = db.relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<KnowledgeDocument {self.filename}>"


class KnowledgeChunk(db.Model):
    __tablename__ = "knowledge_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    project_id = db.Column(db.Integer, nullable=True, index=True)
    chunk_index = db.Column(db.Integer, nullable=False, default=0)
    token_count = db.Column(db.Integer, nullable=False, default=0)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(_build_embedding_type(), nullable=False)
    chunk_metadata = db.Column("metadata", _build_metadata_type(), nullable=False, default=dict)

    document = db.relationship("KnowledgeDocument", back_populates="chunks")

    def __repr__(self):
        return f"<KnowledgeChunk {self.id}>"


class KnowledgeDocumentEvent(db.Model):
    __tablename__ = "knowledge_document_events"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("knowledge_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id = db.Column(db.Integer, nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_payload = db.Column(
        _build_metadata_type(),
        nullable=False,
        default=dict,
    )
    created_at = db.Column(db.DateTime, default=utcnow_naive, nullable=False, index=True)

    def __repr__(self):
        return f"<KnowledgeDocumentEvent {self.id} {self.event_type}>"
