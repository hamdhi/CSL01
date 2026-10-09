from datetime import date
from typing import Annotated, Any

from fastapi import Depends

from src.repositories.ministry_repo import MinistryRepository


class MinistryService:
    def __init__(
        self, ministry_repository: Annotated[MinistryRepository, Depends()]
    ) -> None:
        self.ministry_repository = ministry_repository

    def addZonalOfficer(self, request_data: dict[str, Any]):
        return self.ministry_repository.addZonalOfficer(request_data)

    def update_zonal_officer(self, officer_id: str, changes: dict[str, Any]):
        return self.ministry_repository.update_zonal_officer(officer_id, changes)

    def remove_zonal_officer(self, officer_id: str):
        return self.ministry_repository.delete_zonal_officer(officer_id)

    def get_monthly_province_report(self, start_date: date, end_date: date):
        return self.ministry_repository.get_monthly_province_report(
            start_date, end_date
        )

    def get_three_month_province_report(self, start_date: date, end_date: date):
        return self.ministry_repository.get_three_month_province_report(
            start_date, end_date
        )
