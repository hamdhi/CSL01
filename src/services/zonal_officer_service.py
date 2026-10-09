from datetime import date
from typing import Annotated, Any

from fastapi import Depends

from src.repositories.zonal_officer_repo import ZonalOfficerRepository


class ZonalOfficerService:
    def __init__(
        self,
        zonal_officer_repository: Annotated[ZonalOfficerRepository, Depends()],
    ) -> None:
        self.zonal_officer_repository = zonal_officer_repository

    def add_teacher(self, request_data: dict[str, Any]):
        return self.zonal_officer_repository.create_teacher(request_data)

    def get_monthly_report(self, start_date: date, end_date: date):
        return self.zonal_officer_repository.get_monthly_report(
            start_date, end_date
        )

    def get_three_month_report(self, start_date: date, end_date: date):
        return self.zonal_officer_repository.get_three_month_report(
            start_date, end_date
        )
