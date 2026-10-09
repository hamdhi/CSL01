from typing import Annotated

from fastapi import Depends

from src.repositories.teacher_repo import TeacherRepository


class TeacherService:
    def __init__(
        self, teacher_repository: Annotated[TeacherRepository, Depends()]
    ) -> None:
        self.teacher_repository = teacher_repository

    def decide_monthly_record(self, record_id: str, approved: bool):
        return self.teacher_repository.decide_monthly_record(record_id, approved)

    def decide_student_registration(self, student_id: str, approved: bool):
        return self.teacher_repository.decide_student_registration(
            student_id, approved
        )

    def reset_student_login(self, student_id: str):
        return self.teacher_repository.reset_student_login(student_id)

    def reset_monthly_record(self, student_id: str):
        return self.teacher_repository.reset_monthly_record(student_id)
