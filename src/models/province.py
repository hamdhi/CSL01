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
    from .student import Student


class Province(Base):
    """Represents a province in the country (for organization purposes)."""

    __tablename__ = "provinces"

    prov_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    Province_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Relationship: A province can have many students and zones
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="province",
        primaryjoin="Province.prov_id == foreign(Student.prov_id)",
    )
    zones: Mapped[list["EducationalZone"]] = relationship(
        "EducationalZone",
        back_populates="province",
        primaryjoin="Province.prov_id == foreign(EducationalZone.prov_id)",
    )

    def __repr__(self) -> str:
        return f"<Province(prov_id={self.prov_id!r}, name={self.Province_name!r})>"
