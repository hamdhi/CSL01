from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from src.schemas.subject_schema import SubjectResponseSchema


class StudentRegisterRequestSchema(BaseModel):
    Name: str
    Grade: str
    stream: str = ""
    School: str
    Gmail: EmailStr
    password: str = Field(min_length=12, max_length=128)
    zone_id: uuid.UUID
    prov_id: uuid.UUID | None = None
    acc_number: str | None = None

    @field_validator("Grade")
    @classmethod
    def validate_grade(cls, grade: str) -> str:
        grade = grade.strip()
        if grade not in {str(number) for number in range(1, 14)}:
            raise ValueError("Grade must be from 1 through 13.")
        return grade

    @field_validator("stream")
    @classmethod
    def validate_stream(cls, stream: str) -> str:
        return " ".join(stream.split()).casefold()

    @model_validator(mode="after")
    def validate_grade_stream(self):
        if self.Grade in {"12", "13"} and not self.stream:
            raise ValueError("A stream is required for Grades 12 and 13.")
        if self.Grade not in {"12", "13"} and self.stream:
            raise ValueError("A stream can only be provided for Grades 12 or 13.")
        return self


class StudentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stid: uuid.UUID
    Name: str
    Grade: str
    stream: str
    School: str
    Gmail: EmailStr
    registration_status: str
    prov_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    acc_number: str | None = None
    role_id: uuid.UUID | None = None


class MonthlyRecordResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fk_stid: uuid.UUID
    fk_tid: uuid.UUID | None = None
    reporting_month: date
    upload_date: datetime
    approved: bool | None = None
    marks: list[MonthlyRecordMarkResponseSchema]


class MonthlyRecordMarkRequestSchema(BaseModel):
    subject_id: uuid.UUID
    score: Decimal = Field(ge=0, le=99999.99)
    max_score: Decimal = Field(gt=0, le=99999.99)

    @model_validator(mode="after")
    def score_must_not_exceed_maximum(self):
        if self.score > self.max_score:
            raise ValueError("score must not exceed max_score.")
        return self


class MonthlyRecordRequestSchema(BaseModel):
    reporting_month: date
    marks: list[MonthlyRecordMarkRequestSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_month_and_unique_subjects(self):
        if self.reporting_month.day != 1:
            raise ValueError("reporting_month must be the first day of a month.")
        subject_ids = [mark.subject_id for mark in self.marks]
        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError("A subject can only appear once per monthly report.")
        return self


class MonthlyRecordMarkResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mark_id: uuid.UUID
    subject_id: uuid.UUID
    score: Decimal
    max_score: Decimal
    subject: SubjectResponseSchema


class StudentRegistrationDecisionSchema(BaseModel):
    approved: bool
