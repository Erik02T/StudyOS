"""add idempotency keys and study events

Revision ID: 20260305_0008
Revises: 20260305_0007
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0008"
down_revision = "20260305_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "user_id",
            "organization_id",
            "endpoint",
            "idempotency_key",
            name="uq_idempotency_scope_key",
        ),
    )
    op.create_index("ix_idempotency_keys_id", "idempotency_keys", ["id"])
    op.create_index("ix_idempotency_keys_user_id", "idempotency_keys", ["user_id"])
    op.create_index("ix_idempotency_keys_organization_id", "idempotency_keys", ["organization_id"])
    op.create_index("ix_idempotency_keys_endpoint", "idempotency_keys", ["endpoint"])

    op.create_table(
        "study_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_study_events_id", "study_events", ["id"])
    op.create_index("ix_study_events_organization_id", "study_events", ["organization_id"])
    op.create_index("ix_study_events_user_id", "study_events", ["user_id"])
    op.create_index("ix_study_events_event_type", "study_events", ["event_type"])
    op.create_index("ix_study_events_entity_type", "study_events", ["entity_type"])
    op.create_index("ix_study_events_entity_id", "study_events", ["entity_id"])
    op.create_index("ix_study_events_created_at", "study_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_study_events_created_at", table_name="study_events")
    op.drop_index("ix_study_events_entity_id", table_name="study_events")
    op.drop_index("ix_study_events_entity_type", table_name="study_events")
    op.drop_index("ix_study_events_event_type", table_name="study_events")
    op.drop_index("ix_study_events_user_id", table_name="study_events")
    op.drop_index("ix_study_events_organization_id", table_name="study_events")
    op.drop_index("ix_study_events_id", table_name="study_events")
    op.drop_table("study_events")

    op.drop_index("ix_idempotency_keys_endpoint", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_organization_id", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_user_id", table_name="idempotency_keys")
    op.drop_index("ix_idempotency_keys_id", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
