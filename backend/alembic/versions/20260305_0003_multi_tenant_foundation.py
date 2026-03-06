"""multi-tenant foundation

Revision ID: 20260305_0003
Revises: 20260304_0002
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260305_0003"
down_revision = "20260304_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_organizations_id", "organizations", ["id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_memberships_user_org"),
    )
    op.create_index("ix_memberships_id", "memberships", ["id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    op.create_index("ix_memberships_organization_id", "memberships", ["organization_id"])

    op.add_column("subjects", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_subjects_organization_id_organizations", "subjects", "organizations", ["organization_id"], ["id"]
    )
    op.create_index("ix_subjects_organization_id", "subjects", ["organization_id"])

    op.add_column("performances", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_performances_organization_id_organizations",
        "performances",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_index("ix_performances_organization_id", "performances", ["organization_id"])

    op.execute(
        """
        INSERT INTO organizations (name, slug)
        SELECT email || ' Workspace', 'user-' || id
        FROM users
        """
    )
    op.execute(
        """
        INSERT INTO memberships (user_id, organization_id, role)
        SELECT u.id, o.id, 'owner'
        FROM users u
        JOIN organizations o ON o.slug = 'user-' || u.id
        """
    )
    op.execute(
        """
        UPDATE subjects
        SET organization_id = (
            SELECT m.organization_id
            FROM memberships m
            WHERE m.user_id = subjects.user_id
            ORDER BY m.id
            LIMIT 1
        )
        """
    )
    op.execute(
        """
        UPDATE performances
        SET organization_id = (
            SELECT m.organization_id
            FROM memberships m
            WHERE m.user_id = performances.user_id
            ORDER BY m.id
            LIMIT 1
        )
        """
    )

    op.alter_column("subjects", "organization_id", nullable=False)
    op.alter_column("performances", "organization_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_performances_organization_id", table_name="performances")
    op.drop_constraint("fk_performances_organization_id_organizations", "performances", type_="foreignkey")
    op.drop_column("performances", "organization_id")

    op.drop_index("ix_subjects_organization_id", table_name="subjects")
    op.drop_constraint("fk_subjects_organization_id_organizations", "subjects", type_="foreignkey")
    op.drop_column("subjects", "organization_id")

    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_id", table_name="memberships")
    op.drop_table("memberships")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_id", table_name="organizations")
    op.drop_table("organizations")

