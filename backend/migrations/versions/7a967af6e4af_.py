"""empty message

Revision ID: 7a967af6e4af
Revises: a5efd8d22631, add_deleted_field
Create Date: 2026-01-22 02:29:08.248698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a967af6e4af'
down_revision = ('a5efd8d22631', 'add_deleted_field')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
