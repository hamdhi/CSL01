import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.core.security import AuthenticatedPrincipal
from src.models.educational_zone import EducationalZone
from src.models.role import Role
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.repositories.account_repo import add_user_account
from src.repositories.report_repo import ReportRepository


class ZonalOfficerRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_teacher(self, request_data: dict[str, Any]):
        email = str(request_data.pop("email"))
        password = request_data.pop("password")
        zone_id = request_data.get("zonal_id")
        if zone_id is not None and self.db.get(EducationalZone, zone_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        subject_id = request_data.get("subject_id")
        subject = self.db.get(Subject, subject_id)
        if subject is None or not subject.active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active subject not found.",
            )
        role = self.db.scalar(select(Role).where(Role.name == "TEACHER"))
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The TEACHER role has not been configured.",
            )
        request_data["tid"] = uuid.uuid4()
        request_data["role_id"] = role.role_id
        request_data["Subject"] = subject.name
        request_data["approval_status"] = "pending"
        teacher = Teacher(**request_data)
        try:
            self.db.add(teacher)
            add_user_account(
                self.db,
                actor_type="teacher",
                actor_id=teacher.tid,
                email=email,
                password=password,
            )
            self.db.commit()
            self.db.refresh(teacher)
            return teacher
        except Exception:
            self.db.rollback()
            raise

    def get_monthly_report(
        self,
        start_date: date,
        end_date: date,
        principal: AuthenticatedPrincipal,
    ):
        return ReportRepository(self.db).generate_report(
            start_date, end_date, report_type="monthly", principal=principal
        )

    def get_three_month_report(
        self,
        start_date: date,
        end_date: date,
        principal: AuthenticatedPrincipal,
    ):
        return ReportRepository(self.db).generate_report(
            start_date,
            end_date,
            report_type="three_month",
            principal=principal,
        )

    def decide_teacher_registration(
        self, teacher_id: str, approved: bool, zone_id: uuid.UUID
    ):
        teacher = self.db.scalar(
            select(Teacher).where(
                Teacher.tid == uuid.UUID(teacher_id),
                Teacher.zonal_id == zone_id,
            )
        )
        if teacher is None:
            return None
        try:
            teacher.approval_status = "approved" if approved else "rejected"
            self.db.commit()
            self.db.refresh(teacher)
            return teacher
        except Exception:
            self.db.rollback()
            raise
