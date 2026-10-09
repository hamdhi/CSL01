import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends

from src.core.security import AuthenticatedPrincipal
from src.repositories.report_repo import ReportRepository
from src.repositories.zonal_officer_repo import ZonalOfficerRepository


class ZonalOfficerService:
    def __init__(
        self,
        zonal_officer_repository: Annotated[ZonalOfficerRepository, Depends()],
    ) -> None:
        self.zonal_officer_repository = zonal_officer_repository

    def add_teacher(self, request_data: dict[str, Any]):
        return self.zonal_officer_repository.create_teacher(request_data)

    def get_monthly_report(
        self,
        start_date: date,
        end_date: date,
        principal: AuthenticatedPrincipal,
    ):
        return self.zonal_officer_repository.get_monthly_report(
            start_date, end_date, principal
        )

    def get_three_month_report(
        self,
        start_date: date,
        end_date: date,
        principal: AuthenticatedPrincipal,
    ):
        return self.zonal_officer_repository.get_three_month_report(
            start_date, end_date, principal
        )

    def decide_teacher_registration(
        self, teacher_id: str, approved: bool, zone_id: uuid.UUID
    ):
        return self.zonal_officer_repository.decide_teacher_registration(
            teacher_id, approved, zone_id
        )

    def list_saved_reports(self, principal: AuthenticatedPrincipal):
        return ReportRepository(
            self.zonal_officer_repository.db
        ).list_saved_reports(principal)

    def get_saved_report(
        self, report_id: uuid.UUID, principal: AuthenticatedPrincipal
    ):
        return ReportRepository(
            self.zonal_officer_repository.db
        ).get_saved_report(report_id, principal)
