import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .monthly_record_mark import MonthlyRecordMark


class Subject(Base):
    """A Ministry-managed subject for a grade and optional A/L stream."""

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint(
            "grade",
            "stream",
            "name_key",
            name="uq_subject_grade_stream_name",
        ),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_key: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    stream: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    monthly_marks: Mapped[list["MonthlyRecordMark"]] = relationship(
        "MonthlyRecordMark", back_populates="subject"
    )
