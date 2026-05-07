"""add project_id to knowledge tables

Revision ID: g_add_project_id_to_knowledge_tables
Revises: d7a2c9b1e4f6
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "g_add_project_id_to_knowledge_tables"
down_revision = "d7a2c9b1e4f6"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("knowledge_documents"):
        # add column if not exists
        cols = {c['name'] for c in inspector.get_columns('knowledge_documents')}
        if 'project_id' not in cols:
            op.add_column('knowledge_documents', sa.Column('project_id', sa.Integer(), nullable=True))
            # index
            op.create_index('ix_knowledge_documents_project_id', 'knowledge_documents', ['project_id'], unique=False)

    if inspector.has_table('knowledge_chunks'):
        cols = {c['name'] for c in inspector.get_columns('knowledge_chunks')}
        if 'project_id' not in cols:
            op.add_column('knowledge_chunks', sa.Column('project_id', sa.Integer(), nullable=True))
            op.create_index('ix_knowledge_chunks_project_id', 'knowledge_chunks', ['project_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('knowledge_chunks'):
        cols = {c['name'] for c in inspector.get_columns('knowledge_chunks')}
        if 'project_id' in cols:
            # drop index if exists
            try:
                op.drop_index('ix_knowledge_chunks_project_id', table_name='knowledge_chunks')
            except Exception:
                pass
            op.drop_column('knowledge_chunks', 'project_id')

    if inspector.has_table('knowledge_documents'):
        cols = {c['name'] for c in inspector.get_columns('knowledge_documents')}
        if 'project_id' in cols:
            try:
                op.drop_index('ix_knowledge_documents_project_id', table_name='knowledge_documents')
            except Exception:
                pass
            op.drop_column('knowledge_documents', 'project_id')
