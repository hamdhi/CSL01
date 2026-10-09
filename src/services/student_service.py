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

    def list_subjects(self, grade: str, stream: str = ""):
        return self.student_repository.list_subjects(grade, stream)

    def submit_monthly_record(self, request_data: dict[str, Any]):
        return self.student_repository.create_monthly_record(request_data)
