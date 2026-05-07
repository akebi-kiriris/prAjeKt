"""add project knowledge storage columns and events table

Revision ID: h_proj_kb_storage_evt
Revises: g_add_project_id_to_knowledge_tables
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa


revision = "h_proj_kb_storage_evt"
down_revision = "g_add_project_id_to_knowledge_tables"
branch_labels = None
depends_on = None


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    try:
        return any(idx.get("name") == index_name for idx in inspector.get_indexes(table_name))
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("knowledge_documents"):
        columns = {col["name"] for col in inspector.get_columns("knowledge_documents")}
        if "file_path" not in columns:
            op.add_column("knowledge_documents", sa.Column("file_path", sa.Text(), nullable=True))
        if "storage_key" not in columns:
            op.add_column("knowledge_documents", sa.Column("storage_key", sa.String(length=255), nullable=True))
        if "original_filename" not in columns:
            op.add_column("knowledge_documents", sa.Column("original_filename", sa.String(length=255), nullable=True))
        if "deleted_at" not in columns:
            op.add_column("knowledge_documents", sa.Column("deleted_at", sa.DateTime(), nullable=True))

        if not _has_index(inspector, "knowledge_documents", "ix_knowledge_documents_storage_key"):
            op.create_index("ix_knowledge_documents_storage_key", "knowledge_documents", ["storage_key"], unique=False)
        if not _has_index(inspector, "knowledge_documents", "ix_knowledge_documents_deleted_at"):
            op.create_index("ix_knowledge_documents_deleted_at", "knowledge_documents", ["deleted_at"], unique=False)
        if not _has_index(inspector, "knowledge_documents", "ix_kd_project_created_at"):
            op.create_index("ix_kd_project_created_at", "knowledge_documents", ["project_id", "created_at"], unique=False)
        if not _has_index(inspector, "knowledge_documents", "ix_kd_project_status"):
            op.create_index("ix_kd_project_status", "knowledge_documents", ["project_id", "status"], unique=False)

    if not inspector.has_table("knowledge_document_events"):
        op.create_table(
            "knowledge_document_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=True),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("event_payload", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    inspector = sa.inspect(bind)
    if inspector.has_table("knowledge_document_events"):
        if not _has_index(inspector, "knowledge_document_events", "ix_knowledge_document_events_document_id"):
            op.create_index("ix_knowledge_document_events_document_id", "knowledge_document_events", ["document_id"], unique=False)
        if not _has_index(inspector, "knowledge_document_events", "ix_knowledge_document_events_project_id"):
            op.create_index("ix_knowledge_document_events_project_id", "knowledge_document_events", ["project_id"], unique=False)
        if not _has_index(inspector, "knowledge_document_events", "ix_knowledge_document_events_actor_user_id"):
            op.create_index("ix_knowledge_document_events_actor_user_id", "knowledge_document_events", ["actor_user_id"], unique=False)
        if not _has_index(inspector, "knowledge_document_events", "ix_knowledge_document_events_event_type"):
            op.create_index("ix_knowledge_document_events_event_type", "knowledge_document_events", ["event_type"], unique=False)
        if not _has_index(inspector, "knowledge_document_events", "ix_knowledge_document_events_created_at"):
            op.create_index("ix_knowledge_document_events_created_at", "knowledge_document_events", ["created_at"], unique=False)
        if not _has_index(inspector, "knowledge_document_events", "ix_kde_project_created_at"):
            op.create_index("ix_kde_project_created_at", "knowledge_document_events", ["project_id", "created_at"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("knowledge_document_events"):
        for idx in (
            "ix_kde_project_created_at",
            "ix_knowledge_document_events_created_at",
            "ix_knowledge_document_events_event_type",
            "ix_knowledge_document_events_actor_user_id",
            "ix_knowledge_document_events_project_id",
            "ix_knowledge_document_events_document_id",
        ):
            if _has_index(inspector, "knowledge_document_events", idx):
                op.drop_index(idx, table_name="knowledge_document_events")
        op.drop_table("knowledge_document_events")

    if inspector.has_table("knowledge_documents"):
        for idx in (
            "ix_kd_project_status",
            "ix_kd_project_created_at",
            "ix_knowledge_documents_deleted_at",
            "ix_knowledge_documents_storage_key",
        ):
            if _has_index(inspector, "knowledge_documents", idx):
                op.drop_index(idx, table_name="knowledge_documents")

        columns = {col["name"] for col in inspector.get_columns("knowledge_documents")}
        if "deleted_at" in columns:
            op.drop_column("knowledge_documents", "deleted_at")
        if "original_filename" in columns:
            op.drop_column("knowledge_documents", "original_filename")
        if "storage_key" in columns:
            op.drop_column("knowledge_documents", "storage_key")
        if "file_path" in columns:
            op.drop_column("knowledge_documents", "file_path")
