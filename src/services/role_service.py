import uuid
from typing import Annotated

from fastapi import Depends

from src.models.role import Role
from src.repositories.role_repo import RoleRepository


class RoleService:
    def __init__(
        self, role_repository: Annotated[RoleRepository, Depends()]
    ) -> None:
        self.role_repository = role_repository

    def list_roles(self) -> list[Role]:
        return self.role_repository.list_roles()

    def get_role(self, role_id: uuid.UUID) -> Role | None:
        return self.role_repository.get_role(role_id)
