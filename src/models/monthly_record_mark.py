import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .monthly_record import MonthlyRecord
    from .subject import Subject


class MonthlyRecordMark(Base):
    """A student's marks for one subject in one monthly report."""

    __tablename__ = "monthly_record_marks"
    __table_args__ = (
        UniqueConstraint(
            "monthly_record_id",
            "subject_id",
            name="uq_monthly_record_subject",
        ),
        CheckConstraint("score >= 0", name="ck_monthly_record_mark_score_nonnegative"),
        CheckConstraint("max_score > 0", name="ck_monthly_record_mark_max_positive"),
        CheckConstraint(
            "score <= max_score", name="ck_monthly_record_mark_score_lte_max"
        ),
    )

    mark_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monthly_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monthly_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.subject_id"),
        nullable=False,
        index=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    max_score: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)

    monthly_record: Mapped["MonthlyRecord"] = relationship(
        "MonthlyRecord", back_populates="marks"
    )
    subject: Mapped["Subject"] = relationship(
        "Subject", back_populates="monthly_marks"
    )
