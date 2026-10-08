from typing import Annotated, Any

from fastapi import Depends

from src.repositories.zonal_officer_repo import ZonalOfficerRepository


class ZonalOfficerService:
    def __init__(
        self,
        zonal_officer_repository: Annotated[ZonalOfficerRepository, Depends()],
    ) -> None:
        self.zonal_officer_repository = zonal_officer_repository

    def add_zonal_officer(self, request_data: dict[str, Any]):
        return self.zonal_officer_repository.create_zonal_officer(request_data)

    def update_zonal_officer(self, officer_id: str, changes: dict[str, Any]):
        return self.zonal_officer_repository.update_zonal_officer(
            officer_id, changes
        )

    def remove_zonal_officer(self, officer_id: str):
        return self.zonal_officer_repository.delete_zonal_officer(officer_id)

    def get_monthly_report(self, start_date: str, end_date: str):
        return self.zonal_officer_repository.get_monthly_report(
            start_date, end_date
        )

    def get_three_month_report(self, start_date: str, end_date: str):
        return self.zonal_officer_repository.get_three_month_report(
            start_date, end_date
        )
