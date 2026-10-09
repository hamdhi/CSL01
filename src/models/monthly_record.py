import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import UUID, Boolean, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .monthly_record_mark import MonthlyRecordMark
    from .student import Student
    from .teacher import Teacher


class MonthlyRecord(Base):
    """Stores a student's submission and its teacher-review status."""

    __tablename__ = "monthly_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    fk_stid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    fk_tid: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    reporting_month: Mapped[date] = mapped_column(Date, nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    approved: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, default=None
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="monthly_records",
        primaryjoin="foreign(MonthlyRecord.fk_stid) == Student.stid",
    )
    teacher: Mapped["Teacher | None"] = relationship(
        "Teacher",
        back_populates="monthly_records",
        primaryjoin="foreign(MonthlyRecord.fk_tid) == Teacher.tid",
    )
    marks: Mapped[list["MonthlyRecordMark"]] = relationship(
        "MonthlyRecordMark",
        back_populates="monthly_record",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MonthlyRecord(id={self.id!r}, fk_stid={self.fk_stid!r}, "
            f"upload_date={self.upload_date!r})>"
        )
