from pydantic import BaseModel, ConfigDict, EmailStr
import uuid

class AdminRequestSchema(BaseModel):
    name: str
    role_id: uuid.UUID
    admin_email: EmailStr


class AdminResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    admin_id: uuid.UUID
    admin_name: str
    admin_email: EmailStr
    role_id: uuid.UUID
