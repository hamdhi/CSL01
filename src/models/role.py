"""Role model for the Student Management System.

Role entities from the ER diagram:
    role_id | name
    --------|------------------------
    0       | ADMIN
    1       | MINISTRY
    2       | ZONAL
    3       | TEACHER
    4       | STUDENT
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .admin import Admin
    from .ministry_officer import MinistryOfficer
    from .student import Student
    from .teacher import Teacher
    from .zonal_officer import ZonalOfficer


class Role(Base):
    """Represents the role/classification of a user in the system."""

    __tablename__ = "roles"

    # role_id is a small integer used as the primary key
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    admins: Mapped[list["Admin"]] = relationship(
        "Admin",
        back_populates="role",
        primaryjoin="Role.role_id == foreign(Admin.role_id)",
    )
    ministry_officers: Mapped[list["MinistryOfficer"]] = relationship(
        "MinistryOfficer",
        back_populates="role",
        primaryjoin="Role.role_id == foreign(MinistryOfficer.role_id)",
    )
    zonal_officers: Mapped[list["ZonalOfficer"]] = relationship(
        "ZonalOfficer",
        back_populates="role",
        primaryjoin="Role.role_id == foreign(ZonalOfficer.role_id)",
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        back_populates="role",
        primaryjoin="Role.role_id == foreign(Teacher.role_id)",
    )
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="role",
        primaryjoin="Role.role_id == foreign(Student.role_id)",
    )

    def __repr__(self) -> str:
        return f"<Role(role_id={self.role_id!r}, name={self.name!r})>"
