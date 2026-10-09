import uuid
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.electricity_record import ElectricityRecord
from src.models.monthly_record import MonthlyRecord
from src.models.province import Province
from src.models.student import Student
from src.repositories._helpers import as_uuid


class StudentRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_student(self, request_data: dict[str, Any]):
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

    def login_with_google(self, id_token: str):
        pass

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
        record = MonthlyRecord(fk_stid=student.stid)
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
