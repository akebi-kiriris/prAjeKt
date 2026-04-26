"""add source_text to knowledge documents

Revision ID: d7a2c9b1e4f6
Revises: c6e9f8a1b7d2
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d7a2c9b1e4f6"
down_revision = "c6e9f8a1b7d2"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "knowledge_documents", "source_text"):
        return

    op.add_column("knowledge_documents", sa.Column("source_text", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "knowledge_documents", "source_text"):
        op.drop_column("knowledge_documents", "source_text")
