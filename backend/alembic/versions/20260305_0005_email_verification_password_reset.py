"""email verification and password reset

Revision ID: 20260305_0005
Revises: 20260305_0004
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0005"
down_revision = "20260305_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))

    op.create_table(
        "action_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_action_tokens_id", "action_tokens", ["id"])
    op.create_index("ix_action_tokens_user_id", "action_tokens", ["user_id"])
    op.create_index("ix_action_tokens_purpose", "action_tokens", ["purpose"])
    op.create_index("ix_action_tokens_token_hash", "action_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_action_tokens_token_hash", table_name="action_tokens")
    op.drop_index("ix_action_tokens_purpose", table_name="action_tokens")
    op.drop_index("ix_action_tokens_user_id", table_name="action_tokens")
    op.drop_index("ix_action_tokens_id", table_name="action_tokens")
    op.drop_table("action_tokens")

    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "is_email_verified")

