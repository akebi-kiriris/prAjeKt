"""add completed_at to tasks (idempotent)

Revision ID: d2f4a8c1e9b0
Revises: f9c3d8a1b2e4
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2f4a8c1e9b0"
down_revision = "f9c3d8a1b2e4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tasks"):
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "completed_at" not in columns:
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tasks"):
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "completed_at" in columns:
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.drop_column("completed_at")
