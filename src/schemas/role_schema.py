import uuid

from pydantic import BaseModel, ConfigDict


class RoleResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: uuid.UUID
    name: str
