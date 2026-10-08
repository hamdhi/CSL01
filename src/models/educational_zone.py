import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .province import Province
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
    Province_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )

    # Foreign keys (nullable)
    prov_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )

    # Relationships
    province: Mapped["Province | None"] = relationship(
        "Province",
        back_populates="zones",
        primaryjoin="foreign(EducationalZone.prov_id) == Province.prov_id",
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        back_populates="zone",
        primaryjoin="EducationalZone.zone_id == foreign(Teacher.zonal_id)",
    )
    zonal_officers: Mapped[list["ZonalOfficer"]] = relationship(
        "ZonalOfficer",
        back_populates="zone",
        primaryjoin="EducationalZone.zone_id == foreign(ZonalOfficer.zone_id)",
    )

    def __repr__(self) -> str:
        return (
            f"<EducationalZone(zone_id={self.zone_id!r}, "
            f"province_name={self.Province_name!r})>"
        )
