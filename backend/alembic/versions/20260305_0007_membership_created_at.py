"""add created_at to memberships

Revision ID: 20260305_0007
Revises: 20260305_0006
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0007"
down_revision = "20260305_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "memberships",
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.execute("UPDATE memberships SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    op.alter_column("memberships", "created_at", nullable=False)


def downgrade() -> None:
    op.drop_column("memberships", "created_at")
