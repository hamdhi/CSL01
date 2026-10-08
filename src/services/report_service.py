from datetime import date
from typing import Annotated

from fastapi import Depends

from src.repositories.report_repo import ReportRepository


class ReportService:
    def __init__(
        self, report_repository: Annotated[ReportRepository, Depends()]
    ) -> None:
        self.report_repository = report_repository

    def get_monthly_report(self, start_date: date, end_date: date):
        return self.report_repository.get_monthly_records(
            start_date, end_date, report_type="monthly"
        )

    def get_three_month_report(self, start_date: date, end_date: date):
        return self.report_repository.get_monthly_records(
            start_date, end_date, report_type="three_month"
        )

    def get_province_report(self, start_date: date, end_date: date):
        return self.report_repository.get_monthly_records(
            start_date, end_date, report_type="province"
        )
