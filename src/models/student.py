import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .educational_zone import EducationalZone
    from .electricity_record import ElectricityRecord
    from .monthly_record import MonthlyRecord
    from .province import Province
    from .role import Role
    from .teacher import Teacher


class Student(Base):
    """Represents a student in the system."""

    __tablename__ = "students"

    stid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    Name: Mapped[str] = mapped_column(String(100), nullable=False)
    Grade: Mapped[str] = mapped_column(String(50), nullable=False)
    stream: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    School: Mapped[str] = mapped_column(String(100), nullable=False)
    Gmail: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    registration_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # Foreign keys (nullable as they may not be assigned yet)
    prov_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )
    acc_number: Mapped[str | None] = mapped_column(
        String(50),
        default=None,
        index=True,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )

    # Relationships
    province: Mapped["Province | None"] = relationship(
        "Province",
        back_populates="students",
        primaryjoin="foreign(Student.prov_id) == Province.prov_id",
    )
    zone: Mapped["EducationalZone | None"] = relationship(
        "EducationalZone",
        primaryjoin="foreign(Student.zone_id) == EducationalZone.zone_id",
    )
    electricity_record: Mapped["ElectricityRecord | None"] = relationship(
        "ElectricityRecord",
        back_populates="student",
        uselist=False,
        primaryjoin="foreign(Student.acc_number) == ElectricityRecord.acc_number",
    )
    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="students",
        primaryjoin="foreign(Student.role_id) == Role.role_id",
    )
    monthly_records: Mapped[list["MonthlyRecord"]] = relationship(
        "MonthlyRecord",
        back_populates="student",
        cascade="all, delete-orphan",
        primaryjoin="Student.stid == foreign(MonthlyRecord.fk_stid)",
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary="student_teacher",
        primaryjoin="Student.stid == student_teacher.stid",
        secondaryjoin="Teacher.tid == student_teacher.tid",
        back_populates="students",
    )

    def __repr__(self) -> str:
        return (
            f"<Student(stid={self.stid!r}, Name={self.Name!r}, "
            f"Grade={self.Grade!r}, School={self.School!r})>"
        )
