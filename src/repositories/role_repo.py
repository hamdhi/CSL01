import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.role import Role


class RoleRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def list_roles(self) -> list[Role]:
        return list(self.db.scalars(select(Role).order_by(Role.name)).all())

    def get_role(self, role_id: uuid.UUID) -> Role | None:
        return self.db.get(Role, role_id)

    def create_role(self, name: str) -> Role:
        role = Role(name=name)
        try:
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            return role
        except Exception:
            self.db.rollback()
            raise

    def update_role(self, role_id: uuid.UUID, name: str) -> Role | None:
        role = self.get_role(role_id)
        if role is None:
            return None
        try:
            role.name = name
            self.db.commit()
            self.db.refresh(role)
            return role
        except Exception:
            self.db.rollback()
            raise

    def delete_role(self, role_id: uuid.UUID) -> bool:
        role = self.get_role(role_id)
        if role is None:
            return False
        try:
            self.db.delete(role)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
