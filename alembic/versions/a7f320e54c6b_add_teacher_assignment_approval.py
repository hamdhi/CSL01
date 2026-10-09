"""Track student-to-teacher assignment approval.

Revision ID: a7f320e54c6b
Revises: f86d4092b571
Create Date: 2026-10-09
"""

import sqlalchemy as sa

from alembic import op

revision = "a7f320e54c6b"
down_revision = "f86d4092b571"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_teacher",
        sa.Column(
            "assignment_status",
            sa.String(length=20),
            server_default="approved",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_student_teacher_assignment_status",
        "student_teacher",
        "assignment_status IN ('pending', 'approved', 'rejected')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_student_teacher_assignment_status",
        "student_teacher",
        type_="check",
    )
    op.drop_column("student_teacher", "assignment_status")
