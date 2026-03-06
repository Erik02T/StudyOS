"""email queue

Revision ID: 20260305_0006
Revises: 20260305_0005
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0006"
down_revision = "20260305_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="console"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_email_jobs_id", "email_jobs", ["id"])
    op.create_index("ix_email_jobs_to_email", "email_jobs", ["to_email"])
    op.create_index("ix_email_jobs_status", "email_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_email_jobs_status", table_name="email_jobs")
    op.drop_index("ix_email_jobs_to_email", table_name="email_jobs")
    op.drop_index("ix_email_jobs_id", table_name="email_jobs")
    op.drop_table("email_jobs")

