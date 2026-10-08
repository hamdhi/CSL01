import uuid
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.monthly_record import MonthlyRecord
from src.models.student import Student
from src.repositories._helpers import as_uuid, get_role_id


class StudentRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_student(self, request_data: dict[str, Any]):
        request_data["stid"] = uuid.uuid4()
        request_data["registration_status"] = "pending"
        request_data.setdefault("role_id", None)
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

    def list_students(self):
        return list(self.db.scalars(select(Student).order_by(Student.Name)).all())

    def update_student(self, student_id: str, changes: dict[str, Any]):
        student = self.get_student(student_id)
        if student is None:
            return None
        try:
            for field, value in changes.items():
                setattr(student, field, value)
            self.db.commit()
            self.db.refresh(student)
            return student
        except Exception:
            self.db.rollback()
            raise

    def decide_student_registration(self, student_id: str, approved: bool):
        student = self.get_student(student_id)
        if student is None:
            return None
        try:
            student.registration_status = "approved" if approved else "rejected"
            if approved:
                student.role_id = get_role_id(self.db, "STUDENT")
            self.db.commit()
            self.db.refresh(student)
            return student
        except Exception:
            self.db.rollback()
            raise

    def reset_student_login(self, student_id: str):
        pass

    def delete_student(self, student_id: str):
        student = self.get_student(student_id)
        if student is None:
            return False
        try:
            self.db.delete(student)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def create_monthly_record(self, request_data: dict[str, Any]):
        request_data["id"] = uuid.uuid4()
        request_data.setdefault("approved", None)
        record = MonthlyRecord(**request_data)
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

    def list_monthly_records(self, student_id: str | None = None):
        statement = select(MonthlyRecord)
        if student_id is not None:
            statement = statement.where(
                MonthlyRecord.fk_stid == as_uuid(student_id)
            )
        return list(
            self.db.scalars(
                statement.order_by(MonthlyRecord.upload_date.desc())
            ).all()
        )

    def delete_monthly_record(self, record_id: str):
        record = self.get_monthly_record(record_id)
        if record is None:
            return False
        try:
            self.db.delete(record)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
