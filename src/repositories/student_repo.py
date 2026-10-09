import uuid
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.educational_zone import EducationalZone
from src.models.electricity_record import ElectricityRecord
from src.models.monthly_record import MonthlyRecord
from src.models.monthly_record_mark import MonthlyRecordMark
from src.models.province import Province
from src.models.student import Student
from src.models.subject import Subject
from src.repositories._helpers import as_uuid
from src.repositories.account_repo import add_user_account


class StudentRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_student(self, request_data: dict[str, Any]):
        password = request_data.pop("password")
        zone = self.db.get(EducationalZone, request_data["zone_id"])
        if zone is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational zone not found.",
            )
        if (
            request_data.get("prov_id") is not None
            and request_data["prov_id"] != zone.prov_id
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The selected zone does not belong to the selected province.",
            )
        request_data["prov_id"] = zone.prov_id
        if request_data.get("prov_id") is not None and self.db.get(
            Province, request_data["prov_id"]
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Province not found.",
            )
        if request_data.get("acc_number") is not None and self.db.get(
            ElectricityRecord, request_data["acc_number"]
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Electricity account not found.",
            )
        request_data["stid"] = uuid.uuid4()
        request_data["registration_status"] = "pending"
        request_data["role_id"] = None
        student = Student(**request_data)
        try:
            self.db.add(student)
            add_user_account(
                self.db,
                actor_type="student",
                actor_id=student.stid,
                email=student.Gmail,
                password=password,
            )
            self.db.commit()
            self.db.refresh(student)
            return student
        except Exception:
            self.db.rollback()
            raise

    def get_student(self, student_id: str):
        return self.db.scalar(
            select(Student).where(Student.stid == as_uuid(student_id))
        )

    def get_student_by_email(self, email: str):
        return self.db.scalar(select(Student).where(Student.Gmail == email))

    def list_subjects(self, grade: str, stream: str = ""):
        return list(
            self.db.scalars(
                select(Subject)
                .where(
                    Subject.grade == grade,
                    Subject.stream == stream,
                    Subject.active.is_(True),
                )
                .order_by(Subject.name)
            ).all()
        )

    def create_monthly_record(self, request_data: dict[str, Any]):
        student = self.get_student(str(request_data["fk_stid"]))
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found.",
            )
        if student.registration_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student registration has not been approved.",
            )
        reporting_month = request_data["reporting_month"]
        existing_record = self.db.scalar(
            select(MonthlyRecord).where(
                MonthlyRecord.fk_stid == student.stid,
                MonthlyRecord.reporting_month == reporting_month,
            )
        )
        if existing_record is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A monthly report has already been submitted for this month.",
            )

        submitted_marks = request_data["marks"]
        subject_ids = {mark["subject_id"] for mark in submitted_marks}
        subjects = set(
            self.db.scalars(
                select(Subject.subject_id).where(
                    Subject.subject_id.in_(subject_ids),
                    Subject.active.is_(True),
                    Subject.grade == student.Grade,
                    Subject.stream == student.stream,
                )
            ).all()
        )
        if subjects != subject_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "One or more submitted subjects are not available for "
                    "the student's grade and stream."
                ),
            )

        record = MonthlyRecord(
            fk_stid=student.stid,
            reporting_month=reporting_month,
            marks=[
                MonthlyRecordMark(
                    subject_id=mark["subject_id"],
                    score=mark["score"],
                    max_score=mark["max_score"],
                )
                for mark in submitted_marks
            ],
        )
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def get_monthly_record(self, record_id: str):
        return self.db.scalar(
            select(MonthlyRecord).where(
                MonthlyRecord.id == as_uuid(record_id)
            )
        )
