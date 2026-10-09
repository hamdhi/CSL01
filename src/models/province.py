"""Province model for the Student Management System.

Province entity from the ER diagram:
    prov_id | Province_name
    --------|--------------
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .educational_zone import EducationalZone


class Province(Base):
    """Represents a province in the country (for organization purposes)."""

    __tablename__ = "provinces"

    prov_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    Province_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    zones: Mapped[list["EducationalZone"]] = relationship(
        "EducationalZone",
        back_populates="province",
    )

    def __repr__(self) -> str:
        return f"<Province(prov_id={self.prov_id!r}, name={self.Province_name!r})>"
