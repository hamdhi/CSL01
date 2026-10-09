import uuid
from typing import Annotated, Any

from fastapi import Depends

from src.core.security import AuthenticatedPrincipal
from src.repositories.admin_repo import AdminRepository


class AdminService:
    def __init__(
        self, admin_repository: Annotated[AdminRepository, Depends()]
    ) -> None:
        self.admin_repository = admin_repository
    
    async def addMinistry(self, request_data: dict[str, Any]):
        return await self.admin_repository.addMinistry(request_data)

    def update_ministry_officer(self, officer_id: str, changes: dict[str, Any]):
        return self.admin_repository.update_ministry_officer(officer_id, changes)

    def remove_ministry_officer(self, officer_id: str):
        return self.admin_repository.delete_ministry_officer(officer_id)

    def decide_ministry_officer(self, officer_id: str, approved: bool):
        return self.admin_repository.decide_ministry_officer(
            officer_id, approved
        )

    def view_any_report(self, principal: AuthenticatedPrincipal):
        return self.admin_repository.view_any_report(principal)

    def get_report(
        self, report_id: uuid.UUID, principal: AuthenticatedPrincipal
    ):
        return self.admin_repository.get_report(report_id, principal)
