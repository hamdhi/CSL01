"""Teacher model for the Student Management System.

Teacher entity from the ER diagram:
    tid(uuid) | Name | Subject | School |
    fk - zonal_id | fk-role_id
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .educational_zone import EducationalZone
    from .monthly_record import MonthlyRecord
    from .role import Role
    from .student import Student


class Teacher(Base):
    """Represents a teacher at a school."""

    __tablename__ = "teachers"

    tid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    Name: Mapped[str] = mapped_column(String(100), nullable=False)
    Subject: Mapped[str] = mapped_column(String(100), nullable=False)
    School: Mapped[str] = mapped_column(String(100), nullable=False)

    # Foreign keys (nullable as they may not be assigned yet)
    zonal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )

    # Relationships
    zone: Mapped["EducationalZone | None"] = relationship(
        "EducationalZone",
        back_populates="teachers",
        primaryjoin="foreign(Teacher.zonal_id) == EducationalZone.zone_id",
    )
    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="teachers",
        primaryjoin="foreign(Teacher.role_id) == Role.role_id",
    )
    monthly_records: Mapped[list["MonthlyRecord"]] = relationship(
        "MonthlyRecord",
        back_populates="teacher",
        primaryjoin="Teacher.tid == foreign(MonthlyRecord.fk_tid)",
    )
    students: Mapped[list["Student"]] = relationship(
        secondary="student_teacher",
        primaryjoin="Teacher.tid == student_teacher.tid",
        secondaryjoin="Student.stid == student_teacher.stid",
        back_populates="teachers",
    )

    def __repr__(self) -> str:
        return (
            f"<Teacher(tid={self.tid!r}, Name={self.Name!r}, "
            f"Subject={self.Subject!r}, School={self.School!r})>"
        )
