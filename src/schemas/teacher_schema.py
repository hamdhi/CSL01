import uuid

from pydantic import BaseModel, ConfigDict


class TeacherCreateRequestSchema(BaseModel):
    Name: str
    Subject: str
    School: str
    zonal_id: uuid.UUID | None = None


class TeacherResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tid: uuid.UUID
    Name: str
    Subject: str
    School: str
    zonal_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None


class MonthlyRecordDecisionSchema(BaseModel):
    approved: bool
