import uuid
from typing import Annotated, Any

from fastapi import Depends

from src.repositories.student_repo import StudentRepository
from src.repositories.teacher_repo import TeacherRepository


class TeacherService:
    def __init__(
        self,
        teacher_repository: Annotated[TeacherRepository, Depends()],
        student_repository: Annotated[StudentRepository, Depends()],
    ) -> None:
        self.teacher_repository = teacher_repository
        self.student_repository = student_repository

    def add_student(self, teacher_id: uuid.UUID, request_data: dict[str, Any]):
        return self.student_repository.create_student(
            request_data, teacher_id=teacher_id
        )

    def list_subjects(self):
        return self.teacher_repository.list_subjects()

    def get_assigned_subject(self, teacher_id: uuid.UUID):
        return self.teacher_repository.get_assigned_subject(teacher_id)

    def list_assigned_students(
        self, teacher_id: uuid.UUID, offset: int, limit: int
    ):
        return self.teacher_repository.list_assigned_students(
            teacher_id, offset, limit
        )

    def list_student_assignment_requests(
        self, teacher_id: uuid.UUID, offset: int, limit: int
    ):
        return self.teacher_repository.list_student_assignment_requests(
            teacher_id, offset, limit
        )

    def decide_student_assignment(
        self, student_id: uuid.UUID, teacher_id: uuid.UUID, approved: bool
    ):
        return self.teacher_repository.decide_student_assignment(
            student_id, teacher_id, approved
        )

    def list_colleagues(
        self, zone_id: uuid.UUID, offset: int, limit: int
    ):
        return self.teacher_repository.list_colleagues(zone_id, offset, limit)

    def list_monthly_records(
        self,
        teacher_id: uuid.UUID,
        zone_id: uuid.UUID,
        offset: int,
        limit: int,
    ):
        return self.teacher_repository.list_teacher_monthly_records(
            teacher_id, zone_id, offset, limit
        )

    def decide_monthly_record(
        self,
        record_id: str,
        approved: bool,
        teacher_id: uuid.UUID,
        zone_id: uuid.UUID,
    ):
        return self.teacher_repository.decide_monthly_record(
            record_id, approved, teacher_id, zone_id
        )

    def decide_student_registration(
        self, student_id: str, approved: bool, zone_id: uuid.UUID
    ):
        return self.teacher_repository.decide_student_registration(
            student_id, approved, zone_id
        )

    def reset_student_login(self, student_id: str, zone_id: uuid.UUID):
        return self.teacher_repository.reset_student_login(student_id, zone_id)

    def reset_monthly_record(self, student_id: str, zone_id: uuid.UUID):
        return self.teacher_repository.reset_monthly_record(student_id, zone_id)
