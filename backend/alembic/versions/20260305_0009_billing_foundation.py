"""billing foundation tables

Revision ID: 20260305_0009
Revises: 20260305_0008
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0009"
down_revision = "20260305_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("stripe_customer_id", sa.String(length=120), nullable=True, unique=True),
        sa.Column("stripe_subscription_id", sa.String(length=120), nullable=True, unique=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_organization_subscriptions_id", "organization_subscriptions", ["id"])
    op.create_index(
        "ix_organization_subscriptions_organization_id",
        "organization_subscriptions",
        ["organization_id"],
        unique=True,
    )

    op.create_table(
        "organization_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("metric", sa.String(length=60), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("organization_id", "period_start", "metric", name="uq_org_usage_period_metric"),
    )
    op.create_index("ix_organization_usage_id", "organization_usage", ["id"])
    op.create_index("ix_organization_usage_organization_id", "organization_usage", ["organization_id"])
    op.create_index("ix_organization_usage_period_start", "organization_usage", ["period_start"])
    op.create_index("ix_organization_usage_metric", "organization_usage", ["metric"])

    op.execute(
        """
        INSERT INTO organization_subscriptions (organization_id, plan, status, created_at, updated_at)
        SELECT id, 'free', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM organizations
        """
    )


def downgrade() -> None:
    op.drop_index("ix_organization_usage_metric", table_name="organization_usage")
    op.drop_index("ix_organization_usage_period_start", table_name="organization_usage")
    op.drop_index("ix_organization_usage_organization_id", table_name="organization_usage")
    op.drop_index("ix_organization_usage_id", table_name="organization_usage")
    op.drop_table("organization_usage")

    op.drop_index("ix_organization_subscriptions_organization_id", table_name="organization_subscriptions")
    op.drop_index("ix_organization_subscriptions_id", table_name="organization_subscriptions")
    op.drop_table("organization_subscriptions")
