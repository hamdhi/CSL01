import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ZonalOfficerCreateRequestSchema(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    zone_id: uuid.UUID


class ZonalOfficerUpdateRequestSchema(BaseModel):
    name: str | None = None
    mini_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None


class ZonalOfficerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zonal_id: uuid.UUID
    name: str
    approval_status: str
    email: EmailStr | None = None
    mini_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
