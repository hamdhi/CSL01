import uuid
from typing import Annotated

from fastapi import Depends

from src.repositories.teacher_repo import TeacherRepository


class TeacherService:
    def __init__(
        self, teacher_repository: Annotated[TeacherRepository, Depends()]
    ) -> None:
        self.teacher_repository = teacher_repository

    def list_subjects(self):
        return self.teacher_repository.list_subjects()

    def decide_monthly_record(
        self, record_id: str, approved: bool, zone_id: uuid.UUID
    ):
        return self.teacher_repository.decide_monthly_record(
            record_id, approved, zone_id
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
