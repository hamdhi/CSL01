import uuid
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.zonal_officer import ZonalOfficer
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories.report_repo import ReportRepository


class ZonalOfficerRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_zonal_officer(self, request_data: dict[str, Any]):
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

    def list_zonal_officers(self, ministry_officer_id: str | None = None):
        statement = select(ZonalOfficer)
        if ministry_officer_id is not None:
            statement = statement.where(
                ZonalOfficer.mini_id == as_uuid(ministry_officer_id)
            )
        return list(self.db.scalars(statement.order_by(ZonalOfficer.name)).all())

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

    def get_monthly_report():
        pass

    def get_three_month_report():
        pass
