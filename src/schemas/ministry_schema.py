import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MinistryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mini_id: uuid.UUID
    name: str
    email: str
    approval_status: str
    admin_id: uuid.UUID | None
    role_id: uuid.UUID | None


class MinistryCreateRequestSchema(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class MinistryRequestSchema(BaseModel):
    name: str
    email: str


class MinistryUpdateRequestSchema(BaseModel):
    name: str | None = None
    email: str | None = None