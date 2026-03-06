"""auth security and rate limit

Revision ID: 20260305_0004
Revises: 20260305_0003
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0004"
down_revision = "20260305_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_auth_sessions_id", "auth_sessions", ["id"])
    op.create_index("ix_auth_sessions_session_id", "auth_sessions", ["session_id"], unique=True)
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("token_type", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_revoked_tokens_id", "revoked_tokens", ["id"])
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"], unique=True)

    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier", sa.String(length=255), nullable=False),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rate_limit_events_id", "rate_limit_events", ["id"])
    op.create_index("ix_rate_limit_events_identifier", "rate_limit_events", ["identifier"])
    op.create_index("ix_rate_limit_events_endpoint", "rate_limit_events", ["endpoint"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_events_endpoint", table_name="rate_limit_events")
    op.drop_index("ix_rate_limit_events_identifier", table_name="rate_limit_events")
    op.drop_index("ix_rate_limit_events_id", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")

    op.drop_index("ix_revoked_tokens_jti", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_id", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")

    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_session_id", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")

