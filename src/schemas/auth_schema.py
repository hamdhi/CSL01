import uuid

from pydantic import BaseModel, EmailStr, Field


class PasswordLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str = Field(min_length=1)


class PasswordUpdateRequestSchema(BaseModel):
    password: str = Field(min_length=12, max_length=128)


class AuthSessionResponseSchema(BaseModel):
    expires_in: int
    account_id: uuid.UUID
    actor_id: uuid.UUID
    role: str


class AuthenticatedUserSchema(BaseModel):
    account_id: uuid.UUID
    actor_id: uuid.UUID
    actor_type: str
    role: str
