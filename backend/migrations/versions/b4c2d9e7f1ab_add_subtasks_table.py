"""add subtasks table

Revision ID: b4c2d9e7f1ab
Revises: 1f7e8f9caaff
Create Date: 2026-04-04 03:05:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4c2d9e7f1ab'
down_revision = 'add_deleted_field'
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent: only create table if it doesn't exist (safe for both new and existing DB)
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('subtasks'):
        op.create_table(
            'subtasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('completed', sa.Boolean(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table('subtasks'):
        op.drop_table('subtasks')
