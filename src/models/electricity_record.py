from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .student import Student


class ElectricityRecord(Base):
    """Represents an electricity account record for a school."""

    __tablename__ = "electricity_records"

    acc_number: Mapped[str] = mapped_column(
        String(50), primary_key=True, nullable=False
    )
    acc_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship: An electricity record can be linked to one student
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="electricity_record",
        uselist=False,
        primaryjoin="ElectricityRecord.acc_number == foreign(Student.acc_number)",
    )

    def __repr__(self) -> str:
        return f"<ElectricityRecord(acc_number={self.acc_number!r}, acc_name={self.acc_name!r})>"
