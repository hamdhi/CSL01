import uuid

from sqlalchemy import UUID, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class student_teacher(Base):
    """Association table for the many-to-many relationship between students and teachers."""

    __tablename__ = "student_teacher"

    stid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.stid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    tid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.tid", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # Ensure a student can only have one record per teacher
    __table_args__ = (
        UniqueConstraint("stid", "tid", name="uq_student_teacher_pair"),
    )

    def __repr__(self) -> str:
        return f"<student_teacher(stid={self.stid!r}, tid={self.tid!r})>"
