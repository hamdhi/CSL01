import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .educational_zone import EducationalZone
    from .ministry_officer import MinistryOfficer
    from .role import Role


class ZonalOfficer(Base):
    """Represents a zonal officer responsible for a zone."""

    __tablename__ = "zonal_officers"

    zonal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # Foreign keys (nullable)
    mini_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        default=None,
        index=True,
    )

    # Relationships
    ministry_officer: Mapped["MinistryOfficer | None"] = relationship(
        "MinistryOfficer",
        back_populates="zonal_officers",
        primaryjoin="foreign(ZonalOfficer.mini_id) == MinistryOfficer.mini_id",
    )
    zone: Mapped["EducationalZone | None"] = relationship(
        "EducationalZone",
        back_populates="zonal_officers",
        primaryjoin="foreign(ZonalOfficer.zone_id) == EducationalZone.zone_id",
    )
    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="zonal_officers",
        primaryjoin="foreign(ZonalOfficer.role_id) == Role.role_id",
    )

    def __repr__(self) -> str:
        return (
            f"<ZonalOfficer(zonal_id={self.zonal_id!r}, name={self.name!r})>"
        )
