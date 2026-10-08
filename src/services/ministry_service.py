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

    def get_monthly_province_report(self, start_date: str, end_date: str):
        return self.ministry_repository.get_monthly_province_report(
            start_date, end_date
        )

    def get_three_month_province_report(self, start_date: str, end_date: str):
        return self.ministry_repository.get_three_month_province_report(
            start_date, end_date
        )

    def view_any_report(self):
        return self.ministry_repository.view_any_report()
