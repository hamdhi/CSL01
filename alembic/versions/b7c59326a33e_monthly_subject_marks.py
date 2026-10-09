"""Add grade subjects and monthly report marks.

Revision ID: b7c59326a33e
Revises: a6c2d19f48b3
Create Date: 2026-10-09
"""

import sqlalchemy as sa

from alembic import op

revision = "b7c59326a33e"
down_revision = "a6c2d19f48b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monthly_records",
        sa.Column("reporting_month", sa.Date(), nullable=True),
    )
    op.execute(
        "UPDATE monthly_records "
        "SET reporting_month = date_trunc('month', upload_date)::date"
    )
    op.alter_column(
        "monthly_records", "reporting_month", nullable=False
    )

    op.create_table(
        "subjects",
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_key", sa.String(length=100), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("stream", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("subject_id"),
        sa.UniqueConstraint(
            "grade", "stream", "name_key", name="uq_subject_grade_stream_name"
        ),
    )
    op.create_table(
        "monthly_record_marks",
        sa.Column("mark_id", sa.UUID(), nullable=False),
        sa.Column("monthly_record_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column(
            "max_score", sa.Numeric(precision=7, scale=2), nullable=False
        ),
        sa.CheckConstraint(
            "score >= 0", name="ck_monthly_record_mark_score_nonnegative"
        ),
        sa.CheckConstraint(
            "max_score > 0", name="ck_monthly_record_mark_max_positive"
        ),
        sa.CheckConstraint(
            "score <= max_score", name="ck_monthly_record_mark_score_lte_max"
        ),
        sa.ForeignKeyConstraint(
            ["monthly_record_id"],
            ["monthly_records.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.subject_id"]),
        sa.PrimaryKeyConstraint("mark_id"),
        sa.UniqueConstraint(
            "monthly_record_id",
            "subject_id",
            name="uq_monthly_record_subject",
        ),
    )
    op.create_index(
        op.f("ix_monthly_record_marks_monthly_record_id"),
        "monthly_record_marks",
        ["monthly_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_monthly_record_marks_subject_id"),
        "monthly_record_marks",
        ["subject_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_monthly_record_marks_subject_id"),
        table_name="monthly_record_marks",
    )
    op.drop_index(
        op.f("ix_monthly_record_marks_monthly_record_id"),
        table_name="monthly_record_marks",
    )
    op.drop_table("monthly_record_marks")
    op.drop_table("subjects")
    op.drop_column("monthly_records", "reporting_month")
