"""add missing timeline.remark column (idempotent)

Revision ID: e6a9b3c4d5f6
Revises: c1d2e3f4a5bb
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e6a9b3c4d5f6"
down_revision = "c1d2e3f4a5bb"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("timelines"):
        return

    columns = {column["name"] for column in inspector.get_columns("timelines")}
    if "remark" not in columns:
        with op.batch_alter_table("timelines", schema=None) as batch_op:
            batch_op.add_column(sa.Column("remark", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("timelines"):
        return

    columns = {column["name"] for column in inspector.get_columns("timelines")}
    if "remark" in columns:
        with op.batch_alter_table("timelines", schema=None) as batch_op:
            batch_op.drop_column("remark")
