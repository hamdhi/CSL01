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

    def login_with_google(self, id_token: str):
        return self.student_repository.login_with_google(id_token)

    def submit_monthly_record(self, request_data: dict[str, Any]):
        return self.student_repository.create_monthly_record(request_data)

    def decide_student_registration(self, student_id: str, approved: bool):
        return self.student_repository.decide_student_registration(
            student_id, approved
        )

    def reset_student_login(self, student_id: str):
        return self.student_repository.reset_student_login(student_id)
