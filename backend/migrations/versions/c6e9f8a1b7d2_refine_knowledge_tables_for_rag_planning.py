"""refine knowledge tables for rag planning

Revision ID: c6e9f8a1b7d2
Revises: b9d1e2f3a4c5
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c6e9f8a1b7d2"
down_revision = "b9d1e2f3a4c5"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_unique_constraint(inspector, table_name, constraint_name):
    if not inspector.has_table(table_name):
        return False
    for constraint in inspector.get_unique_constraints(table_name):
        if constraint.get("name") == constraint_name:
            return True
    return False


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("knowledge_documents"):
        if not _has_column(inspector, "knowledge_documents", "mime_type"):
            op.add_column("knowledge_documents", sa.Column("mime_type", sa.String(length=120), nullable=True))
        if not _has_column(inspector, "knowledge_documents", "size_bytes"):
            op.add_column("knowledge_documents", sa.Column("size_bytes", sa.Integer(), nullable=True))
        if not _has_column(inspector, "knowledge_documents", "error_message"):
            op.add_column("knowledge_documents", sa.Column("error_message", sa.Text(), nullable=True))
        if not _has_column(inspector, "knowledge_documents", "updated_at"):
            op.add_column(
                "knowledge_documents",
                sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            )

    inspector = sa.inspect(bind)
    if _has_unique_constraint(inspector, "knowledge_documents", "uq_knowledge_documents_sha256"):
        op.drop_constraint("uq_knowledge_documents_sha256", "knowledge_documents", type_="unique")

    inspector = sa.inspect(bind)
    if not _has_unique_constraint(inspector, "knowledge_documents", "uq_knowledge_documents_user_sha256"):
        op.create_unique_constraint(
            "uq_knowledge_documents_user_sha256",
            "knowledge_documents",
            ["user_id", "sha256"],
        )

    if inspector.has_table("knowledge_chunks"):
        if not _has_column(inspector, "knowledge_chunks", "chunk_index"):
            op.add_column(
                "knowledge_chunks",
                sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
            )
        if not _has_column(inspector, "knowledge_chunks", "token_count"):
            op.add_column(
                "knowledge_chunks",
                sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_unique_constraint(inspector, "knowledge_documents", "uq_knowledge_documents_user_sha256"):
        op.drop_constraint("uq_knowledge_documents_user_sha256", "knowledge_documents", type_="unique")
    inspector = sa.inspect(bind)
    if not _has_unique_constraint(inspector, "knowledge_documents", "uq_knowledge_documents_sha256"):
        op.create_unique_constraint("uq_knowledge_documents_sha256", "knowledge_documents", ["sha256"])

    inspector = sa.inspect(bind)
    if _has_column(inspector, "knowledge_chunks", "token_count"):
        op.drop_column("knowledge_chunks", "token_count")
    if _has_column(inspector, "knowledge_chunks", "chunk_index"):
        op.drop_column("knowledge_chunks", "chunk_index")

    inspector = sa.inspect(bind)
    if _has_column(inspector, "knowledge_documents", "updated_at"):
        op.drop_column("knowledge_documents", "updated_at")
    if _has_column(inspector, "knowledge_documents", "error_message"):
        op.drop_column("knowledge_documents", "error_message")
    if _has_column(inspector, "knowledge_documents", "size_bytes"):
        op.drop_column("knowledge_documents", "size_bytes")
    if _has_column(inspector, "knowledge_documents", "mime_type"):
        op.drop_column("knowledge_documents", "mime_type")
