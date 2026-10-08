import calendar
import uuid
from collections import defaultdict
from datetime import date
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.monthly_record import MonthlyRecord
from src.models.zonal_officer import ZonalOfficer
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories.report_repo import ReportRepository


class MinistryRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def addZonalOfficer(self, request_data: dict[str, Any]):
        request_data["zonal_id"] = uuid.uuid4()
        if request_data.get("role_id") is None:
            request_data["role_id"] = get_role_id(self.db, "ZONAL")
        officer = ZonalOfficer(**request_data)
        try:
            self.db.add(officer)
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def get_zonal_officer(self, officer_id: str):
        return self.db.scalar(
            select(ZonalOfficer).where(
                ZonalOfficer.zonal_id == as_uuid(officer_id)
            )
        )

    def list_zonal_officers(self):
        return list(
            self.db.scalars(select(ZonalOfficer).order_by(ZonalOfficer.name)).all()
        )

    def update_zonal_officer(self, officer_id: str, changes: dict[str, Any]):
        officer = self.get_zonal_officer(officer_id)
        if officer is None:
            return None
        try:
            for field, value in changes.items():
                setattr(officer, field, value)
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def delete_zonal_officer(self, officer_id: str):
        officer = self.get_zonal_officer(officer_id)
        if officer is None:
            return False
        try:
            self.db.delete(officer)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    # TODO: Implement report generation methods for MinistryRepository

    # def get_monthly_province_report(self, start_date: str, end_date: str):
    #     return ReportRepository(self.db).get_monthly_records(
    #         start_date, end_date, report_type="province"
    #     )

    # def get_three_month_province_report(self, start_date: str, end_date: str):
    #     return ReportRepository(self.db).get_monthly_records(
    #         start_date, end_date, report_type="three_month_province"
    #     )

    def view_any_report(self):
        records = self.db.scalars(
            select(MonthlyRecord).order_by(MonthlyRecord.upload_date)
        ).all()
        reports: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            uploaded = record.upload_date.date()
            reports[(uploaded.year, uploaded.month)].append(
                {
                    "id": record.id,
                    "fk_stid": record.fk_stid,
                    "fk_tid": record.fk_tid,
                    "upload_date": record.upload_date,
                    "approved": record.approved,
                }
            )

        return [
            {
                "report_type": "monthly",
                "start_date": date(year, month, 1),
                "end_date": date(
                    year, month, calendar.monthrange(year, month)[1]
                ),
                "data": data,
            }
            for (year, month), data in sorted(reports.items())
        ]
