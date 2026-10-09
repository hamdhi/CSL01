import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_session
from src.models.monthly_record import MonthlyRecord
from src.models.student import Student
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.models.user_account import UserAccount
from src.repositories._helpers import as_uuid, get_role_id


class TeacherRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def list_subjects(self):
        return list(
            self.db.scalars(
                select(Subject)
                .where(Subject.active.is_(True))
                .order_by(Subject.name)
            ).all()
        )

    def get_teacher(self, teacher_id: str):
        return self.db.scalar(
            select(Teacher).where(Teacher.tid == as_uuid(teacher_id))
        )

    def list_teachers(self, zonal_id: str | None = None):
        statement = select(Teacher)
        if zonal_id is not None:
            statement = statement.where(Teacher.zonal_id == as_uuid(zonal_id))
        return list(self.db.scalars(statement.order_by(Teacher.Name)).all())

    def update_teacher(self, teacher_id: str, changes: dict[str, Any]):
        teacher = self.get_teacher(teacher_id)
        if teacher is None:
            return None
        try:
            for field, value in changes.items():
                setattr(teacher, field, value)
            self.db.commit()
            self.db.refresh(teacher)
            return teacher
        except Exception:
            self.db.rollback()
            raise

    def delete_teacher(self, teacher_id: str):
        teacher = self.get_teacher(teacher_id)
        if teacher is None:
            return False
        try:
            for record in teacher.monthly_records:
                record.fk_tid = None
                record.teacher = None
            teacher.students.clear()
            self.db.delete(teacher)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def decide_monthly_record(
        self, record_id: str, approved: bool, zone_id: uuid.UUID
    ):
        record = self.db.scalar(
            select(MonthlyRecord)
            .join(Student, Student.stid == MonthlyRecord.fk_stid)
            .where(
                MonthlyRecord.id == as_uuid(record_id),
                Student.zone_id == zone_id,
            )
        )
        if record is None:
            return None
        try:
            record.approved = approved
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def decide_student_registration(
        self, student_id: str, approved: bool, zone_id: uuid.UUID
    ):
        student = self.db.scalar(
            select(Student).where(
                Student.stid == as_uuid(student_id),
                Student.zone_id == zone_id,
            )
        )
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

    def reset_student_login(self, student_id: str, zone_id: uuid.UUID):
        student = self.db.scalar(
            select(Student).where(
                Student.stid == as_uuid(student_id),
                Student.zone_id == zone_id,
            )
        )
        if student is None:
            return False
        account = self.db.scalar(
            select(UserAccount).where(
                UserAccount.actor_type == "student",
                UserAccount.actor_id == student.stid,
            )
        )
        if account is None:
            return False
        try:
            now = datetime.now(UTC)
            for session in account.sessions:
                if session.revoked_at is None:
                    session.revoked_at = now
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def reset_monthly_record(self, student_id: str, zone_id: uuid.UUID):
        records = list(
            self.db.scalars(
                select(MonthlyRecord)
                .join(Student, Student.stid == MonthlyRecord.fk_stid)
                .where(
                    MonthlyRecord.fk_stid == as_uuid(student_id),
                    Student.zone_id == zone_id,
                )
            ).all()
        )
        if not records:
            return False
        try:
            for record in records:
                record.approved = None
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def assign_monthly_record(self, record_id: str, teacher_id: str):
        teacher = self.get_teacher(teacher_id)
        if teacher is None:
            return None
        record = self.db.scalar(
            select(MonthlyRecord).where(
                MonthlyRecord.id == as_uuid(record_id)
            )
        )
        if record is None:
            return None
        try:
            record.teacher = teacher
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def list_monthly_records(self, teacher_id: str):
        return list(
            self.db.scalars(
                select(MonthlyRecord)
                .where(MonthlyRecord.fk_tid == as_uuid(teacher_id))
                .order_by(MonthlyRecord.upload_date.desc())
            ).all()
        )
