import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class StudentRegisterRequestSchema(BaseModel):
    Name: str
    Grade: str
    School: str
    Gmail: EmailStr
    prov_id: uuid.UUID | None = None
    acc_number: str | None = None


class StudentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stid: uuid.UUID
    Name: str
    Grade: str
    School: str
    Gmail: EmailStr
    registration_status: str
    prov_id: uuid.UUID | None = None
    acc_number: str | None = None
    role_id: uuid.UUID | None = None


class GoogleLoginRequestSchema(BaseModel):
    id_token: str


class MonthlyRecordResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fk_stid: uuid.UUID
    fk_tid: uuid.UUID | None = None
    upload_date: datetime
    approved: bool | None = None


class StudentRegistrationDecisionSchema(BaseModel):
    approved: bool
