import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends

from src.core.security import AuthenticatedPrincipal
from src.repositories.ministry_repo import MinistryRepository
from src.repositories.report_repo import ReportRepository


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

    def list_zonal_officers(
        self, ministry_id: uuid.UUID, offset: int, limit: int
    ):
        return self.ministry_repository.list_zonal_officers(
            ministry_id, offset, limit
        )

    def list_ministry_officers(self, offset: int, limit: int):
        return self.ministry_repository.list_ministry_officers(offset, limit)

    def create_zone(
        self, name: str, prov_id: uuid.UUID
    ):
        return self.ministry_repository.create_zone(name, prov_id)

    def list_zones(self, offset: int, limit: int):
        return self.ministry_repository.list_zones(offset, limit)

    def list_provinces(self, offset: int, limit: int):
        return self.ministry_repository.list_provinces(offset, limit)

    def decide_zonal_officer(self, officer_id: str, approved: bool):
        return self.ministry_repository.decide_zonal_officer(
            officer_id, approved
        )

    def create_subject(self, request_data: dict[str, Any]):
        return self.ministry_repository.create_subject(request_data)

    def list_subjects(
        self,
        grade: str | None = None,
        stream: str | None = None,
        include_inactive: bool = False,
    ):
        return self.ministry_repository.list_subjects(
            grade, stream, include_inactive
        )

    def update_subject(self, subject_id: str, changes: dict[str, Any]):
        return self.ministry_repository.update_subject(subject_id, changes)

    def list_saved_reports(self, principal: AuthenticatedPrincipal):
        return ReportRepository(
            self.ministry_repository.db
        ).list_saved_reports(principal)

    def get_saved_report(
        self, report_id: uuid.UUID, principal: AuthenticatedPrincipal
    ):
        return ReportRepository(
            self.ministry_repository.db
        ).get_saved_report(report_id, principal)

    def get_monthly_province_report(
        self,
        start_date: date,
        end_date: date,
        principal: AuthenticatedPrincipal,
    ):
        return self.ministry_repository.get_monthly_province_report(
            start_date, end_date, principal
        )

    def generate_ministry_pdf(
        self,
        principal: AuthenticatedPrincipal,
        period: tuple[date, date],
    ) -> bytes:
        return ReportRepository(
            self.ministry_repository.db
        ).generate_ministry_pdf(principal, period)
