import uuid
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from src.core.database import get_session
from src.models.educational_zone import EducationalZone
from src.models.monthly_record import MonthlyRecord
from src.models.monthly_record_mark import MonthlyRecordMark
from src.models.student import Student
from src.models.student_teacher import student_teacher
from src.models.subject import Subject
from src.models.teacher import Teacher
from src.repositories._helpers import as_uuid, get_role_id
from src.repositories._pagination import paginate
from src.repositories.account_repo import add_user_account


class StudentRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def create_student(
        self,
        request_data: dict[str, Any],
        teacher_id: uuid.UUID | None = None,
    ):
        password = request_data.pop("password")
        teacher_code = request_data.pop("teacher_code", None)
        if teacher_id is not None:
            teacher = self.db.get(Teacher, teacher_id)
        elif teacher_code is not None:
            teacher = self.db.scalar(
                select(Teacher).where(Teacher.teacher_code == teacher_code.upper())
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A teacher must be selected for student registration.",
            )
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found.",
            )
        if teacher.approval_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The selected teacher is not approved.",
            )
        if teacher.zonal_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The selected teacher is not assigned to an educational zone.",
            )
        if teacher.subject_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The selected teacher does not have an assigned subject.",
            )
        teacher_subject = self.db.get(Subject, teacher.subject_id)
        if (
            teacher_subject is None
            or not teacher_subject.active
            or teacher_subject.grade != request_data["Grade"]
            or teacher_subject.stream != request_data["stream"]
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The selected teacher is not assigned to the student's grade and stream.",
            )
        zone = self.db.get(EducationalZone, teacher.zonal_id)
        if zone is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The selected teacher's educational zone was not found.",
            )
        if zone.prov_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The selected zone is not assigned to a province.",
            )
        request_data["zone_id"] = zone.zone_id

        # Just Add Electricity Record No Validation
        # if (
        #     request_data.get("acc_number") is not None
        #     and self.db.get(ElectricityRecord, request_data["acc_number"]) is None
        # ):
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Electricity account not found.",
        #     )
        request_data["stid"] = uuid.uuid4()
        request_data["registration_status"] = "pending"
        request_data["role_id"] = get_role_id(self.db, "STUDENT")
        student = Student(**request_data)
        try:
            student.teachers.append(teacher)
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

    def list_zone_students(self, zone_id: uuid.UUID, offset: int, limit: int):
        return paginate(
            self.db,
            select(Student)
            .where(Student.zone_id == zone_id)
            .order_by(Student.Name, Student.stid),
            offset,
            limit,
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

    def list_student_subjects(self, student_id: uuid.UUID):
        student = self.get_student(str(student_id))
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found.",
            )
        return list(
            self.db.scalars(
                select(Subject)
                .join(Teacher, Teacher.subject_id == Subject.subject_id)
                .join(student_teacher, student_teacher.tid == Teacher.tid)
                .where(
                    student_teacher.stid == student_id,
                    student_teacher.assignment_status == "approved",
                    Teacher.approval_status == "approved",
                    Subject.grade == student.Grade,
                    Subject.stream == student.stream,
                    Subject.active.is_(True),
                )
                .order_by(Subject.name)
            ).all()
        )

    def request_teacher_assignment(
        self, student_id: uuid.UUID, teacher_code: str
    ):
        student = self.get_student(str(student_id))
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found.",
            )
        if student.registration_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student registration must be approved before requesting another teacher.",
            )
        teacher = self.get_teacher_by_code(teacher_code)
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approved teacher not found.",
            )
        if student.zone_id is None or teacher.zonal_id != student.zone_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The teacher must be assigned to the student's educational zone.",
            )
        teacher_subject = (
            self.db.get(Subject, teacher.subject_id)
            if teacher.subject_id is not None
            else None
        )
        if (
            teacher_subject is None
            or not teacher_subject.active
            or teacher_subject.grade != student.Grade
            or teacher_subject.stream != student.stream
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The teacher is not assigned to the student's grade and stream.",
            )

        assignment = self.db.get(student_teacher, (student_id, teacher.tid))
        if assignment is not None and assignment.assignment_status in {
            "pending",
            "approved",
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request or assignment for this teacher already exists.",
            )
        try:
            if assignment is None:
                assignment = student_teacher(
                    stid=student_id,
                    tid=teacher.tid,
                    assignment_status="pending",
                )
                self.db.add(assignment)
            else:
                assignment.assignment_status = "pending"
            self.db.commit()
            return {
                "teacher_code": teacher.teacher_code,
                "Name": teacher.Name,
                "Subject": teacher.Subject,
                "School": teacher.School,
                "assignment_status": assignment.assignment_status,
            }
        except Exception:
            self.db.rollback()
            raise

    def list_student_teacher_assignments(self, student_id: uuid.UUID):
        rows = self.db.execute(
            select(
                Teacher.teacher_code,
                Teacher.Name,
                Teacher.Subject,
                Teacher.School,
                student_teacher.assignment_status,
            )
            .join(student_teacher, student_teacher.tid == Teacher.tid)
            .where(student_teacher.stid == student_id)
            .order_by(Teacher.Name, Teacher.teacher_code)
        ).mappings()
        return [dict(row) for row in rows]

    def list_available_teachers(self, query: str | None, offset: int, limit: int):
        statement = select(Teacher).where(Teacher.approval_status == "approved")
        if query is not None:
            search = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Teacher.teacher_code.ilike(search),
                    Teacher.Name.ilike(search),
                    Teacher.School.ilike(search),
                )
            )
        return paginate(
            self.db,
            statement.order_by(Teacher.Name, Teacher.teacher_code),
            offset,
            limit,
        )

    def get_teacher_by_code(self, teacher_code: str):
        return self.db.scalar(
            select(Teacher).where(
                Teacher.teacher_code == teacher_code.upper(),
                Teacher.approval_status == "approved",
            )
        )

    def list_student_monthly_records(
        self, student_id: uuid.UUID, offset: int, limit: int
    ):
        return paginate(
            self.db,
            select(MonthlyRecord)
            .where(MonthlyRecord.fk_stid == student_id)
            .options(
                selectinload(MonthlyRecord.marks).joinedload(MonthlyRecordMark.subject)
            )
            .order_by(
                MonthlyRecord.reporting_month.desc(),
                MonthlyRecord.upload_date.desc(),
                MonthlyRecord.id,
            ),
            offset,
            limit,
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
            select(MonthlyRecord).where(MonthlyRecord.id == as_uuid(record_id))
        )
