"""Add student login and monthly record workflow state.

Revision ID: a6c2d19f48b3
Revises: 0b433dd20065
Create Date: 2026-10-08
"""

import sqlalchemy as sa

from alembic import op

revision = "a6c2d19f48b3"
down_revision = "0b433dd20065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column(
            "registration_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "monthly_records",
        sa.Column("approved", sa.Boolean(), nullable=True),
    )
    op.alter_column("students", "registration_status", server_default=None)


def downgrade() -> None:
    op.drop_column("monthly_records", "approved")
    op.drop_column("students", "registration_status")
