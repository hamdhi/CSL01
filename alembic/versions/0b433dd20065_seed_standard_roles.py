"""Seed the standard user roles.

Revision ID: 0b433dd20065
Revises: f3a27733e72b
Create Date: 2026-10-08 15:37:39.258584

"""
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op

# revision identifiers, used by Alembic.
revision = '0b433dd20065'
down_revision = 'f3a27733e72b'
branch_labels = None
depends_on = None

roles = sa.table(
    "roles",
    sa.column("role_id", sa.Uuid()),
    sa.column("name", sa.String(length=50)),
)
seed_roles = [
    (uuid.UUID("d730ab1c-b43c-5806-a94b-597c341e64c1"), "ADMIN"),
    (uuid.UUID("1175c099-c2d5-5d94-9e6f-3f622fc76ade"), "MINISTRY"),
    (uuid.UUID("afa9ee33-001b-5b4b-8bb2-cda57db1d518"), "ZONAL"),
    (uuid.UUID("14162ba8-f87c-58c8-b599-3588558a7895"), "TEACHER"),
    (uuid.UUID("c7b8b337-5043-52f9-a723-8b93424bd117"), "STUDENT"),
]


def upgrade() -> None:
    op.get_bind().execute(
        insert(roles)
        .values([{"role_id": role_id, "name": name} for role_id, name in seed_roles])
        .on_conflict_do_nothing(index_elements=[roles.c.name])
    )


def downgrade() -> None:
    bind = op.get_bind()
    for role_id, name in seed_roles:
        bind.execute(
            roles.delete().where(
                roles.c.role_id == role_id,
                roles.c.name == name,
            )
        )
