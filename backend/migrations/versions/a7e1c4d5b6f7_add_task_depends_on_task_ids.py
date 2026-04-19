"""add depends_on_task_ids to tasks (idempotent)

Revision ID: a7e1c4d5b6f7
Revises: d2f4a8c1e9b0
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7e1c4d5b6f7"
down_revision = "d2f4a8c1e9b0"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tasks"):
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "depends_on_task_ids" not in columns:
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.add_column(sa.Column("depends_on_task_ids", sa.JSON(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tasks"):
        return

    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "depends_on_task_ids" in columns:
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.drop_column("depends_on_task_ids")
