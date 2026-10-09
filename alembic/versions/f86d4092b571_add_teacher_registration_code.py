"""Add public registration codes to teachers.

Revision ID: f86d4092b571
Revises: e82d1a9b4f31
Create Date: 2026-10-13
"""

import sqlalchemy as sa

from alembic import op

revision = "f86d4092b571"
down_revision = "e82d1a9b4f31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SEQUENCE teacher_code_seq"))
    op.add_column(
        "teachers",
        sa.Column("teacher_code", sa.String(length=20), nullable=True),
    )
    op.execute(
        sa.text(
            """
            WITH numbered_teachers AS (
                SELECT tid, ROW_NUMBER() OVER (ORDER BY tid) AS code_number
                FROM teachers
            )
            UPDATE teachers
            SET teacher_code = 'T' || LPAD(
                numbered_teachers.code_number::text, 3, '0'
            )
            FROM numbered_teachers
            WHERE teachers.tid = numbered_teachers.tid
            """
        )
    )
    op.execute(
        sa.text(
            """
            SELECT setval(
                'teacher_code_seq',
                GREATEST(COUNT(*), 1),
                COUNT(*) > 0
            )
            FROM teachers
            """
        )
    )
    op.alter_column("teachers", "teacher_code", nullable=False)
    op.create_index(
        "ix_teachers_teacher_code",
        "teachers",
        ["teacher_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_teachers_teacher_code", table_name="teachers")
    op.drop_column("teachers", "teacher_code")
    op.execute(sa.text("DROP SEQUENCE teacher_code_seq"))
