import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .admin import Admin
    from .role import Role
    from .zonal_officer import ZonalOfficer


class MinistryOfficer(Base):
    """Represents a ministry officer."""

    __tablename__ = "ministry_officers"

    mini_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True
    )
    approval_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    # Foreign keys (nullable)
    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )



    # Relationships
    admin: Mapped["Admin | None"] = relationship(
        "Admin",
        back_populates="ministry_officers",
        primaryjoin="foreign(MinistryOfficer.admin_id) == Admin.admin_id",
        foreign_keys="MinistryOfficer.admin_id",
    )
    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="ministry_officers",
        primaryjoin="foreign(MinistryOfficer.role_id) == Role.role_id",
    )
    zonal_officers: Mapped[list["ZonalOfficer"]] = relationship(
        "ZonalOfficer",
        back_populates="ministry_officer",
        primaryjoin="MinistryOfficer.mini_id == foreign(ZonalOfficer.mini_id)",
    )

    def __repr__(self) -> str:
        return f"<MinistryOfficer(mini_id={self.mini_id!r}, name={self.name!r})>"
