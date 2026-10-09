import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.core.security import AuthenticatedPrincipal
from src.models.educational_zone import EducationalZone
from src.models.monthly_record import MonthlyRecord
from src.models.role import Role
from src.models.student import Student
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.models.zonal_officer import ZonalOfficer
from src.repositories._pagination import paginate
from src.repositories.account_repo import add_user_account
from src.repositories.report_repo import ReportRepository


class ZonalOfficerRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def list_subjects(
        self, grade: str | None = None, stream: str | None = None
    ):
        statement = select(Subject).where(Subject.active.is_(True))
        if grade is not None:
            statement = statement.where(Subject.grade == grade)
        if stream is not None:
            statement = statement.where(Subject.stream == stream)
        return list(
            self.db.scalars(
                statement.order_by(Subject.grade, Subject.stream, Subject.name)
            ).all()
        )

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
        next_code = self.db.execute(
            text("SELECT nextval('teacher_code_seq')")
        ).scalar_one()
        request_data["teacher_code"] = f"T{next_code:03d}"
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

    def list_teachers(self, zone_id: uuid.UUID, offset: int, limit: int):
        return paginate(
            self.db,
            select(Teacher)
            .where(Teacher.zonal_id == zone_id)
            .order_by(Teacher.Name, Teacher.tid),
            offset,
            limit,
        )

    def list_zonal_officers(
        self, zonal_id: uuid.UUID, offset: int, limit: int
    ):
        officer = self.db.get(ZonalOfficer, zonal_id)
        if officer is None:
            return paginate(
                self.db,
                select(ZonalOfficer).where(
                    ZonalOfficer.zonal_id == zonal_id
                ),
                offset,
                limit,
            )
        statement = select(ZonalOfficer)
        if officer.mini_id is None:
            statement = statement.where(
                ZonalOfficer.zonal_id == officer.zonal_id
            )
        else:
            statement = statement.where(
                ZonalOfficer.mini_id == officer.mini_id
            )
        return paginate(
            self.db,
            statement.order_by(ZonalOfficer.name, ZonalOfficer.zonal_id),
            offset,
            limit,
        )

    def list_students(self, zone_id: uuid.UUID, offset: int, limit: int):
        return paginate(
            self.db,
            select(Student)
            .where(Student.zone_id == zone_id)
            .order_by(Student.Name, Student.stid),
            offset,
            limit,
        )

    def list_monthly_records(
        self, zone_id: uuid.UUID, offset: int, limit: int
    ):
        return paginate(
            self.db,
            select(MonthlyRecord)
            .join(Student, Student.stid == MonthlyRecord.fk_stid)
            .where(Student.zone_id == zone_id)
            .order_by(MonthlyRecord.upload_date.desc(), MonthlyRecord.id),
            offset,
            limit,
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
