"""Ensure each profile has its canonical role.

Revision ID: b184ce7e6a23
Revises: a7f320e54c6b
Create Date: 2026-10-09
"""

import sqlalchemy as sa

from alembic import op

revision = "b184ce7e6a23"
down_revision = "a7f320e54c6b"
branch_labels = None
depends_on = None


PROFILE_ROLES = (
    ("admins", "ADMIN"),
    ("ministry_officers", "MINISTRY"),
    ("zonal_officers", "ZONAL"),
    ("teachers", "TEACHER"),
    ("students", "STUDENT"),
)


def upgrade() -> None:
    expected_roles = ", ".join(f"'{role_name}'" for _, role_name in PROFILE_ROLES)
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF (
                    SELECT COUNT(DISTINCT name)
                    FROM roles
                    WHERE name IN ({expected_roles})
                ) <> {len(PROFILE_ROLES)} THEN
                    RAISE EXCEPTION
                        'Cannot backfill profile roles: a required role is missing.';
                END IF;
            END
            $$
            """
        )
    )
    for table_name, role_name in PROFILE_ROLES:
        op.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET role_id = (
                    SELECT role_id FROM roles WHERE name = '{role_name}'
                )
                """
            )
        )


def downgrade() -> None:
    pass
