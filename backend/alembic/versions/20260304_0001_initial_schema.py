"""initial schema

Revision ID: 20260304_0001
Revises:
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260304_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("available_hours_per_day", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("preferred_time_block", sa.String(length=32), nullable=False, server_default="19:00-21:00"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("importance_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="general"),
    )
    op.create_index("ix_subjects_id", "subjects", ["id"])
    op.create_index("ix_subjects_user_id", "subjects", ["user_id"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("estimated_time", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("mastery_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
    )
    op.create_index("ix_tasks_id", "tasks", ["id"])
    op.create_index("ix_tasks_subject_id", "tasks", ["subject_id"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"),
    )
    op.create_index("ix_reviews_id", "reviews", ["id"])
    op.create_index("ix_reviews_task_id", "reviews", ["task_id"])

    op.create_table(
        "performances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("completed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("focus_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("productivity_index", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index("ix_performances_id", "performances", ["id"])
    op.create_index("ix_performances_user_id", "performances", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_performances_user_id", table_name="performances")
    op.drop_index("ix_performances_id", table_name="performances")
    op.drop_table("performances")

    op.drop_index("ix_reviews_task_id", table_name="reviews")
    op.drop_index("ix_reviews_id", table_name="reviews")
    op.drop_table("reviews")

    op.drop_index("ix_tasks_subject_id", table_name="tasks")
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")

    op.drop_index("ix_subjects_user_id", table_name="subjects")
    op.drop_index("ix_subjects_id", table_name="subjects")
    op.drop_table("subjects")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

