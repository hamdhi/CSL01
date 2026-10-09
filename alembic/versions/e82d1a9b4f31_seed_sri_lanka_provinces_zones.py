"""Seed Sri Lanka provinces and example zones.

Revision ID: e82d1a9b4f31
Revises: d29c44e8a102
Create Date: 2026-10-09
"""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op

revision = "e82d1a9b4f31"
down_revision = "d29c44e8a102"
branch_labels = None
depends_on = None

PROVINCES = (
    "Western Province",
    "Central Province",
    "Southern Province",
    "Northern Province",
    "Eastern Province",
    "North Western Province",
    "North Central Province",
    "Uva Province",
    "Sabaragamuwa Province",
)


def _seed_id(kind: str, name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"csl01:{kind}:{name}")


def upgrade() -> None:
    connection = op.get_bind()
    provinces = sa.table(
        "provinces",
        sa.column("prov_id", sa.Uuid()),
        sa.column("Province_name", sa.String(length=100)),
    )
    connection.execute(
        insert(provinces)
        .values(
            [
                {
                    "prov_id": _seed_id("province", name),
                    "Province_name": name,
                }
                for name in PROVINCES
            ]
        )
        .on_conflict_do_nothing(index_elements=[provinces.c.Province_name])
    )

    connection.execute(
        sa.text(
            """
            INSERT INTO educational_zones (zone_id, name, prov_id)
            SELECT seeded.zone_id, seeded.name, province.prov_id
            FROM (
                VALUES
                    (:zone_1_id, 'Test Zone 1'),
                    (:zone_2_id, 'Test Zone 2')
            ) AS seeded(zone_id, name)
            CROSS JOIN provinces AS province
            WHERE province."Province_name" = 'Western Province'
            ON CONFLICT (name) DO NOTHING
            """
        ).bindparams(
            zone_1_id=_seed_id("zone", "Test Zone 1"),
            zone_2_id=_seed_id("zone", "Test Zone 2"),
        )
    )


def downgrade() -> None:
    pass
