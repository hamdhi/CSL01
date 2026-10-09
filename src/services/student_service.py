import uuid
from typing import Annotated, Any

from fastapi import Depends

from src.repositories.student_repo import StudentRepository


class StudentService:
    def __init__(
        self, student_repository: Annotated[StudentRepository, Depends()]
    ) -> None:
        self.student_repository = student_repository

    def register_student(self, request_data: dict[str, Any]):
        return self.student_repository.create_student(request_data)

    def list_available_teachers(self, query: str | None, offset: int, limit: int):
        return self.student_repository.list_available_teachers(query, offset, limit)

    def get_teacher_by_code(self, teacher_code: str):
        return self.student_repository.get_teacher_by_code(teacher_code)

    def request_teacher_assignment(
        self, student_id: uuid.UUID, teacher_code: str
    ):
        return self.student_repository.request_teacher_assignment(
            student_id, teacher_code
        )

    def list_teacher_assignments(self, student_id: uuid.UUID):
        return self.student_repository.list_student_teacher_assignments(
            student_id
        )

    def list_subjects(self, grade: str, stream: str = ""):
        return self.student_repository.list_subjects(grade, stream)

    def list_student_subjects(self, student_id: uuid.UUID):
        return self.student_repository.list_student_subjects(student_id)

    def list_monthly_records(
        self, student_id: uuid.UUID, offset: int, limit: int
    ):
        return self.student_repository.list_student_monthly_records(
            student_id, offset, limit
        )

    def list_zone_students(
        self, zone_id: uuid.UUID, offset: int, limit: int
    ):
        return self.student_repository.list_zone_students(
            zone_id, offset, limit
        )

    def submit_monthly_record(self, request_data: dict[str, Any]):
        return self.student_repository.create_monthly_record(request_data)
