import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoleCreateRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class RoleUpdateRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class RoleResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: uuid.UUID
    name: str
