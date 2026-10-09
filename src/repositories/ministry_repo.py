import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.educational_zone import EducationalZone
from src.models.ministry_officer import MinistryOfficer
from src.models.zonal_officer import ZonalOfficer
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories.report_repo import ReportRepository


class MinistryRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def addZonalOfficer(self, request_data: dict[str, Any]):
        ministry_id = request_data.get("mini_id")
        if ministry_id is not None and self.db.get(
            MinistryOfficer, ministry_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ministry officer not found.",
            )
        zone_id = request_data.get("zone_id")
        if zone_id is not None and self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        request_data["zonal_id"] = uuid.uuid4()
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
        ministry_id = changes.get("mini_id")
        if ministry_id is not None and self.db.get(
            MinistryOfficer, ministry_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ministry officer not found.",
            )
        zone_id = changes.get("zone_id")
        if zone_id is not None and self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
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

    def get_monthly_province_report(self, start_date: date, end_date: date):
        return ReportRepository(self.db).get_monthly_records(
            start_date, end_date, report_type="province"
        )

    def get_three_month_province_report(self, start_date: date, end_date: date):
        return ReportRepository(self.db).get_monthly_records(
            start_date, end_date, report_type="three_month_province"
        )
