import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TeacherCreateRequestSchema(BaseModel):
    Name: str
    subject_id: uuid.UUID
    School: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    zonal_id: uuid.UUID | None = None


class TeacherLookupResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    teacher_code: str
    Name: str
    Subject: str
    School: str


class TeacherAssignmentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    teacher_code: str
    Name: str
    Subject: str
    School: str
    assignment_status: str


class TeacherResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tid: uuid.UUID
    teacher_code: str
    Name: str
    Subject: str
    subject_id: uuid.UUID | None = None
    School: str
    zonal_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    approval_status: str


class MonthlyRecordDecisionSchema(BaseModel):
    approved: bool


class TeacherAssignmentDecisionSchema(BaseModel):
    approved: bool
