"""performance enhancements

Revision ID: 20260304_0002
Revises: 20260304_0001
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260304_0002"
down_revision = "20260304_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "performances",
        sa.Column("study_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "performances",
        sa.Column("time_block", sa.String(length=32), nullable=False, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("performances", "time_block")
    op.drop_column("performances", "study_minutes")

