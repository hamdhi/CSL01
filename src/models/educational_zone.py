import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .province import Province
    from .student import Student
    from .teacher import Teacher
    from .zonal_officer import ZonalOfficer


class EducationalZone(Base):
    """Represents an educational zone within a province."""

    __tablename__ = "educational_zones"

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )

    prov_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provinces.prov_id"),
        nullable=False,
        index=True,
    )

    province: Mapped["Province"] = relationship("Province", back_populates="zones")
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="zone",
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        back_populates="zone",
    )
    zonal_officers: Mapped[list["ZonalOfficer"]] = relationship(
        "ZonalOfficer",
        back_populates="zone",
    )

    def __repr__(self) -> str:
        return (
            f"<EducationalZone(zone_id={self.zone_id!r}, "
            f"name={self.name!r})>"
        )
