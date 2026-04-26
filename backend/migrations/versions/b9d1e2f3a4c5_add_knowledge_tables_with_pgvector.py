"""add knowledge tables with pgvector support (idempotent)

Revision ID: b9d1e2f3a4c5
Revises: a7e1c4d5b6f7
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b9d1e2f3a4c5"
down_revision = "a7e1c4d5b6f7"
branch_labels = None
depends_on = None


class VectorType(sa.types.UserDefinedType):
    def __init__(self, dimension):
        self.dimension = dimension

    def get_col_spec(self, **_kwargs):
        return f"vector({self.dimension})"


def _create_extension_if_needed(bind):
    if bind.dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    dialect_name = bind.dialect.name

    _create_extension_if_needed(bind)

    if not inspector.has_table("knowledge_documents"):
        op.create_table(
            "knowledge_documents",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(
                "status IN ('uploaded', 'indexing', 'ready', 'failed')",
                name="ck_knowledge_documents_status",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sha256", name="uq_knowledge_documents_sha256"),
        )

    if not inspector.has_table("knowledge_chunks"):
        metadata_type = postgresql.JSONB(astext_type=sa.Text()) if dialect_name == "postgresql" else sa.JSON()
        embedding_type = VectorType(3072) if dialect_name == "postgresql" else sa.JSON()

        op.create_table(
            "knowledge_chunks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("embedding", embedding_type, nullable=False),
            sa.Column("metadata", metadata_type, nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    inspector = sa.inspect(bind)

    doc_index_names = set()
    if inspector.has_table("knowledge_documents"):
        doc_index_names = {idx["name"] for idx in inspector.get_indexes("knowledge_documents")}

    if "ix_knowledge_documents_user_id" not in doc_index_names:
        op.create_index("ix_knowledge_documents_user_id", "knowledge_documents", ["user_id"], unique=False)

    if "ix_knowledge_documents_created_at" not in doc_index_names:
        op.create_index("ix_knowledge_documents_created_at", "knowledge_documents", ["created_at"], unique=False)

    chunk_index_names = set()
    if inspector.has_table("knowledge_chunks"):
        chunk_index_names = {idx["name"] for idx in inspector.get_indexes("knowledge_chunks")}

    if "ix_knowledge_chunks_document_id" not in chunk_index_names:
        op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"], unique=False)

    if "ix_knowledge_chunks_user_id" not in chunk_index_names:
        op.create_index("ix_knowledge_chunks_user_id", "knowledge_chunks", ["user_id"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("knowledge_chunks"):
        index_names = {idx["name"] for idx in inspector.get_indexes("knowledge_chunks")}
        if "ix_knowledge_chunks_user_id" in index_names:
            op.drop_index("ix_knowledge_chunks_user_id", table_name="knowledge_chunks")
        if "ix_knowledge_chunks_document_id" in index_names:
            op.drop_index("ix_knowledge_chunks_document_id", table_name="knowledge_chunks")
        op.drop_table("knowledge_chunks")

    inspector = sa.inspect(bind)
    if inspector.has_table("knowledge_documents"):
        index_names = {idx["name"] for idx in inspector.get_indexes("knowledge_documents")}
        if "ix_knowledge_documents_created_at" in index_names:
            op.drop_index("ix_knowledge_documents_created_at", table_name="knowledge_documents")
        if "ix_knowledge_documents_user_id" in index_names:
            op.drop_index("ix_knowledge_documents_user_id", table_name="knowledge_documents")
        op.drop_table("knowledge_documents")
