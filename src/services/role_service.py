import uuid
from typing import Annotated

from fastapi import Depends

from src.repositories.role_repo import RoleRepository


class RoleService:
    def __init__(
        self, role_repository: Annotated[RoleRepository, Depends()]
    ) -> None:
        self.role_repository = role_repository

    def list_roles(self) -> list[dict[str, object]]:
        return self.role_repository.list_roles()

    def get_role(self, role_id: uuid.UUID) -> dict[str, object] | None:
        return self.role_repository.get_role(role_id)

    def create_role(self, name: str) -> dict[str, object]:
        return self.role_repository.create_role(name)

    def update_role(self, role_id: uuid.UUID, name: str) -> dict[str, object] | None:
        return self.role_repository.update_role(role_id, name)

    def delete_role(self, role_id: uuid.UUID) -> bool:
        return self.role_repository.delete_role(role_id)
