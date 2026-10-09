"""Connect provinces and zones; derive student province through zone.

Revision ID: d29c44e8a102
Revises: c41df8a071be
Create Date: 2026-10-09
"""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op

revision = "d29c44e8a102"
down_revision = "c41df8a071be"
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
WESTERN_PROVINCE_ID = uuid.uuid5(
    uuid.NAMESPACE_URL, "csl01:province:Western Province"
)
TEST_ZONES = (
    (
        uuid.uuid5(uuid.NAMESPACE_URL, "csl01:zone:Test Zone 1"),
        "Test Zone 1",
    ),
    (
        uuid.uuid5(uuid.NAMESPACE_URL, "csl01:zone:Test Zone 2"),
        "Test Zone 2",
    ),
)


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
                    "prov_id": uuid.uuid5(
                        uuid.NAMESPACE_URL, f"csl01:province:{name}"
                    ),
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
            UPDATE educational_zones
            SET prov_id = (
                SELECT prov_id
                FROM provinces
                WHERE "Province_name" = 'Western Province'
            )
            WHERE prov_id IS NULL
              AND "Province_name" IN ('Test Zone 1', 'Test Zone 2')
            """
        )
    )

    connection.execute(
        sa.text(
            """
            UPDATE educational_zones AS zone
            SET prov_id = inferred.prov_id
            FROM (
                SELECT zone_id, MIN(prov_id::text)::uuid AS prov_id
                FROM students
                WHERE zone_id IS NOT NULL AND prov_id IS NOT NULL
                GROUP BY zone_id
                HAVING COUNT(DISTINCT prov_id) = 1
            ) AS inferred
            WHERE zone.zone_id = inferred.zone_id
              AND zone.prov_id IS NULL
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE educational_zones
            SET prov_id = (
                SELECT prov_id
                FROM provinces
                LIMIT 1
            )
            WHERE prov_id IS NULL
              AND (SELECT COUNT(*) FROM provinces) = 1
            """
        )
    )

    connection.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM educational_zones AS zone
                    LEFT JOIN provinces AS province
                      ON province.prov_id = zone.prov_id
                    WHERE zone.prov_id IS NULL OR province.prov_id IS NULL
                ) THEN
                    RAISE EXCEPTION
                      'Cannot require a province for every zone: assign each existing zone a valid prov_id first.';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM students AS student
                    LEFT JOIN educational_zones AS zone
                      ON zone.zone_id = student.zone_id
                    WHERE student.prov_id IS NOT NULL
                      AND (
                        student.zone_id IS NULL
                        OR zone.zone_id IS NULL
                        OR zone.prov_id IS DISTINCT FROM student.prov_id
                      )
                ) THEN
                    RAISE EXCEPTION
                      'Cannot remove students.prov_id safely: assign each province-linked student to a matching zone first.';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM students AS student
                    LEFT JOIN educational_zones AS zone
                      ON zone.zone_id = student.zone_id
                    WHERE student.zone_id IS NOT NULL
                      AND zone.zone_id IS NULL
                ) THEN
                    RAISE EXCEPTION
                      'Cannot add student-zone foreign key: fix students with an unknown zone_id first.';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM teachers AS teacher
                    LEFT JOIN educational_zones AS zone
                      ON zone.zone_id = teacher.zonal_id
                    WHERE teacher.zonal_id IS NOT NULL
                      AND zone.zone_id IS NULL
                ) THEN
                    RAISE EXCEPTION
                      'Cannot add teacher-zone foreign key: fix teachers with an unknown zonal_id first.';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM zonal_officers AS officer
                    LEFT JOIN educational_zones AS zone
                      ON zone.zone_id = officer.zone_id
                    WHERE officer.zone_id IS NOT NULL
                      AND zone.zone_id IS NULL
                ) THEN
                    RAISE EXCEPTION
                      'Cannot add zonal-officer foreign key: fix officers with an unknown zone_id first.';
                END IF;
            END
            $$;
            """
        )
    )

    op.drop_constraint(
        "educational_zones_Province_name_key",
        "educational_zones",
        type_="unique",
    )
    op.alter_column(
        "educational_zones",
        "Province_name",
        new_column_name="name",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "educational_zones",
        "prov_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.create_unique_constraint(
        "educational_zones_name_key",
        "educational_zones",
        ["name"],
    )
    op.create_foreign_key(
        "fk_educational_zones_prov_id_provinces",
        "educational_zones",
        "provinces",
        ["prov_id"],
        ["prov_id"],
    )
    op.create_foreign_key(
        "fk_students_zone_id_educational_zones",
        "students",
        "educational_zones",
        ["zone_id"],
        ["zone_id"],
    )
    op.create_foreign_key(
        "fk_teachers_zonal_id_educational_zones",
        "teachers",
        "educational_zones",
        ["zonal_id"],
        ["zone_id"],
    )
    op.create_foreign_key(
        "fk_zonal_officers_zone_id_educational_zones",
        "zonal_officers",
        "educational_zones",
        ["zone_id"],
        ["zone_id"],
    )
    op.execute(
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
            zone_1_id=TEST_ZONES[0][0],
            zone_2_id=TEST_ZONES[1][0],
        )
    )
    op.drop_index(op.f("ix_students_prov_id"), table_name="students")
    op.drop_column("students", "prov_id")


def downgrade() -> None:
    op.add_column(
        "students",
        sa.Column("prov_id", sa.UUID(), nullable=True),
    )
    op.create_index(
        op.f("ix_students_prov_id"),
        "students",
        ["prov_id"],
        unique=False,
    )
    op.execute(
        """
        UPDATE students AS student
        SET prov_id = zone.prov_id
        FROM educational_zones AS zone
        WHERE student.zone_id = zone.zone_id
        """
    )
    op.drop_constraint(
        "fk_zonal_officers_zone_id_educational_zones",
        "zonal_officers",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_teachers_zonal_id_educational_zones",
        "teachers",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_students_zone_id_educational_zones",
        "students",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_educational_zones_prov_id_provinces",
        "educational_zones",
        type_="foreignkey",
    )
    op.drop_constraint(
        "educational_zones_name_key",
        "educational_zones",
        type_="unique",
    )
    op.alter_column(
        "educational_zones",
        "prov_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.alter_column(
        "educational_zones",
        "name",
        new_column_name="Province_name",
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.create_unique_constraint(
        "educational_zones_Province_name_key",
        "educational_zones",
        ["Province_name"],
    )
