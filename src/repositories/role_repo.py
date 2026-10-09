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
