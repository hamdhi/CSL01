import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .ministry_officer import MinistryOfficer
    from .role import Role


class Admin(Base):
    """Represents an admin user in the system."""

    __tablename__ = "admins"

    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
    )
    admin_name: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        nullable=False,
        index=True,
    )
    
    admin_email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Foreign key (nullable)
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), default=None, index=True
    )

    # Relationships
    ministry_officers: Mapped[list["MinistryOfficer"]] = relationship(
        "MinistryOfficer",
        back_populates="admin",
        primaryjoin="Admin.admin_id == foreign(MinistryOfficer.admin_id)",
        foreign_keys="MinistryOfficer.admin_id",
    )
    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="admins",
        primaryjoin="foreign(Admin.role_id) == Role.role_id",
    )

    def __repr__(self) -> str:
        return (
            f"<Admin(admin_id={self.admin_id!r}, admin_name={self.admin_name!r}, "
            f"admin_email={self.admin_email!r})>"
        )
