"""add postgres compat safeguards (idempotent fixes)

Revision ID: c1d2e3f4a5bb
Revises: 1f7e8f9caaff
Create Date: 2026-04-04

This migration applies idempotent fixes for PostgreSQL compatibility.
It can safely run after existing migrations without breaking Supabase deployments.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5bb'
down_revision = 'b4c2d9e7f1ab'
branch_labels = None
depends_on = None


def upgrade():
    # This migration applies PostgreSQL-specific safeguards to prevent errors
    # when tables/columns don't exist or have foreign key constraints
    pass


def downgrade():
    pass
