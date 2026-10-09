"""Add accounts, approval states, report archive, and student zone data.

Revision ID: c41df8a071be
Revises: b7c59326a33e
Create Date: 2026-10-09
"""

import sqlalchemy as sa

from alembic import op

revision = "c41df8a071be"
down_revision = "b7c59326a33e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("stream", sa.String(length=50), nullable=False, server_default=""),
    )
    op.add_column("students", sa.Column("zone_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_students_zone_id"), "students", ["zone_id"])
    op.add_column(
        "teachers",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column(
        "teachers", sa.Column("subject_id", sa.UUID(), nullable=True)
    )
    op.create_index(op.f("ix_teachers_subject_id"), "teachers", ["subject_id"])
    op.create_foreign_key(
        "fk_teachers_subject_id_subjects",
        "teachers",
        "subjects",
        ["subject_id"],
        ["subject_id"],
    )
    op.add_column(
        "zonal_officers",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column(
        "ministry_officers",
        sa.Column("email", sa.String(length=100), nullable=True),
    )
    op.create_unique_constraint(
        "uq_ministry_officers_email", "ministry_officers", ["email"]
    )
    op.add_column(
        "ministry_officers",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )
    op.create_table(
        "user_accounts",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("actor_type", sa.String(length=30), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("account_id"),
        sa.UniqueConstraint("actor_type", "actor_id", name="uq_user_account_actor"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_user_accounts_email"), "user_accounts", ["email"]
    )
    op.execute(
        """
        INSERT INTO user_accounts
            (account_id, email, actor_type, actor_id, password_hash, created_at)
        SELECT gen_random_uuid(),
               lower(trim(profiles.profile_email)),
               profiles.actor_type,
               profiles.actor_id,
               NULL,
               now()
        FROM (
            SELECT admins.admin_email AS profile_email,
                   'admin' AS actor_type,
                   admins.admin_id AS actor_id
            FROM admins
            UNION ALL
            SELECT ministry_officers.email AS profile_email,
                   'ministry' AS actor_type,
                   ministry_officers.mini_id AS actor_id
            FROM ministry_officers
            WHERE ministry_officers.email IS NOT NULL
              AND trim(ministry_officers.email) <> ''
            UNION ALL
            SELECT students."Gmail" AS profile_email,
                   'student' AS actor_type,
                   students.stid AS actor_id
            FROM students
        ) AS profiles
        """
    )
    op.create_table(
        "auth_sessions",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("access_jti", sa.String(length=36), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "refresh_expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"], ["user_accounts.account_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("access_jti"),
    )
    op.create_index(
        op.f("ix_auth_sessions_account_id"),
        "auth_sessions",
        ["account_id"],
    )
    op.create_table(
        "report_snapshots",
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("report_type", sa.String(length=40), nullable=False),
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("scope_id", sa.UUID(), nullable=True),
        sa.Column("generated_by_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["generated_by_id"], ["user_accounts.account_id"]
        ),
        sa.PrimaryKeyConstraint("report_id"),
    )
    op.create_index(
        op.f("ix_report_snapshots_scope_id"),
        "report_snapshots",
        ["scope_id"],
    )
    op.create_index(
        op.f("ix_report_snapshots_generated_by_id"),
        "report_snapshots",
        ["generated_by_id"],
    )
    op.alter_column("students", "stream", server_default=None)
    op.alter_column("teachers", "approval_status", server_default=None)
    op.alter_column("zonal_officers", "approval_status", server_default=None)
    op.alter_column(
        "ministry_officers", "approval_status", server_default=None
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_report_snapshots_generated_by_id"),
        table_name="report_snapshots",
    )
    op.drop_index(
        op.f("ix_report_snapshots_scope_id"),
        table_name="report_snapshots",
    )
    op.drop_table("report_snapshots")
    op.drop_index(
        op.f("ix_auth_sessions_account_id"), table_name="auth_sessions"
    )
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_user_accounts_email"), table_name="user_accounts")
    op.drop_table("user_accounts")
    op.drop_column("ministry_officers", "approval_status")
    op.drop_constraint(
        "uq_ministry_officers_email", "ministry_officers", type_="unique"
    )
    op.drop_column("ministry_officers", "email")
    op.drop_column("zonal_officers", "approval_status")
    op.drop_constraint(
        "fk_teachers_subject_id_subjects", "teachers", type_="foreignkey"
    )
    op.drop_index(op.f("ix_teachers_subject_id"), table_name="teachers")
    op.drop_column("teachers", "subject_id")
    op.drop_column("teachers", "approval_status")
    op.drop_index(op.f("ix_students_zone_id"), table_name="students")
    op.drop_column("students", "zone_id")
    op.drop_column("students", "stream")
