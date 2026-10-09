import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.educational_zone import EducationalZone
from src.models.role import Role
from src.models.teacher import Teacher


class ZonalOfficerRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_teacher(self, request_data: dict[str, Any]):
        zone_id = request_data.get("zonal_id")
        if zone_id is not None and self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        role = self.db.scalar(select(Role).where(Role.name == "TEACHER"))
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The TEACHER role has not been configured.",
            )
        request_data["tid"] = uuid.uuid4()
        request_data["role_id"] = role.role_id
        teacher = Teacher(**request_data)
        try:
            self.db.add(teacher)
            self.db.commit()
            self.db.refresh(teacher)
            return teacher
        except Exception:
            self.db.rollback()
            raise

    def get_monthly_report(self, start_date: date, end_date: date):
        pass

    def get_three_month_report(self, start_date: date, end_date: date):
        pass
