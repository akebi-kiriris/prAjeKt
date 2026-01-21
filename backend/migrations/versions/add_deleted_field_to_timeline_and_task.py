"""add deleted field to timeline and task

Revision ID: add_deleted_field
Revises: 
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_deleted_field'
down_revision = None  # 改成你最新的 migration ID
branch_labels = None
depends_on = None


def upgrade():
    # 新增 deleted 欄位到 timelines 表
    op.add_column('timelines', sa.Column('deleted', sa.Boolean(), nullable=False, server_default='0'))
    
    # 新增 deleted 欄位到 tasks 表
    op.add_column('tasks', sa.Column('deleted', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    # 移除 timelines 的 deleted 欄位
    op.drop_column('timelines', 'deleted')
    
    # 移除 tasks 的 deleted 欄位
    op.drop_column('tasks', 'deleted')
