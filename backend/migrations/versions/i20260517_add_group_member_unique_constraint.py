"""add unique constraint for group_members (group_id, user_id)

Revision ID: i20260517
Revises: h20260507
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa


revision = "i20260517"
down_revision = "h20260507"
branch_labels = None
depends_on = None


def _has_unique_constraint(inspector, table_name: str, constraint_name: str) -> bool:
    try:
        return any(
            item.get("name") == constraint_name
            for item in inspector.get_unique_constraints(table_name)
        )
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("group_members"):
        return

    # 先去重，保留最小 id，避免加 unique constraint 失敗
    op.execute(
        sa.text(
            """
            DELETE FROM group_members
            WHERE id NOT IN (
              SELECT MIN(id)
              FROM group_members
              GROUP BY group_id, user_id
            )
            """
        )
    )

    if not _has_unique_constraint(inspector, "group_members", "uq_group_members_group_user"):
        with op.batch_alter_table("group_members") as batch_op:
            batch_op.create_unique_constraint(
                "uq_group_members_group_user",
                ["group_id", "user_id"],
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("group_members"):
        return

    if _has_unique_constraint(inspector, "group_members", "uq_group_members_group_user"):
        with op.batch_alter_table("group_members") as batch_op:
            batch_op.drop_constraint("uq_group_members_group_user", type_="unique")
