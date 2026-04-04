"""add group_ai_snapshots table

Revision ID: f9c3d8a1b2e4
Revises: e6a9b3c4d5f6
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9c3d8a1b2e4'
down_revision = 'e6a9b3c4d5f6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('group_ai_snapshots'):
        return

    op.create_table(
        'group_ai_snapshots',
        sa.Column('snapshot_id', sa.Integer(), primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.group_id'), nullable=False),
        sa.Column('summary_json', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('source_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('model', sa.String(length=128), nullable=True),
        sa.Column('provider', sa.String(length=64), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
    )
    op.create_index('ix_group_ai_snapshots_group_id', 'group_ai_snapshots', ['group_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('group_ai_snapshots'):
        return

    op.drop_index('ix_group_ai_snapshots_group_id', table_name='group_ai_snapshots')
    op.drop_table('group_ai_snapshots')
