import uuid

from pydantic import BaseModel, ConfigDict

class MinistryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mini_id: uuid.UUID
    name: str
    email: str
    admin_id: uuid.UUID | None
    role_id: uuid.UUID | None

class MinistryRequestSchema(BaseModel):
    name: str
    email: str
    role_id: uuid.UUID | None = None