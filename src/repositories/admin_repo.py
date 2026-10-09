import calendar
import uuid
from collections import defaultdict
from datetime import date
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.ministry_officer import MinistryOfficer
from src.models.monthly_record import MonthlyRecord
from src.repositories._helpers import as_uuid, get_role_id


class AdminRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    async def addMinistry(self, request_data: dict[str, Any]):
        request_data["mini_id"] = uuid.uuid4()
        request_data["role_id"] = get_role_id(self.db, "MINISTRY")
        officer = MinistryOfficer(**request_data)
        try:
            self.db.add(officer)
            self.db.commit()
            self.db.refresh(officer)
            return officer
        except Exception:
            self.db.rollback()
            raise

    def get_ministry_officer(self, officer_id: str):
        return self.db.scalar(
            select(MinistryOfficer).where(
                MinistryOfficer.mini_id == as_uuid(officer_id)
            )
        )

    def list_ministry_officers(self):
        return list(
            self.db.scalars(
                select(MinistryOfficer).order_by(MinistryOfficer.name)
            ).all()
        )

    def update_ministry_officer(self, officer_id: str, changes: dict[str, Any]):
        officer = self.get_ministry_officer(officer_id)
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

    def delete_ministry_officer(self, officer_id: str):
        officer = self.get_ministry_officer(officer_id)
        if officer is None:
            return False
        try:
            self.db.delete(officer)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

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
