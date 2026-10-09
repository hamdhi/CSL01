import uuid

from pydantic import BaseModel, EmailStr, Field


class PasswordLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class GoogleLoginRequestSchema(BaseModel):
    id_token: str = Field(min_length=1)


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str = Field(min_length=1)


class PasswordUpdateRequestSchema(BaseModel):
    password: str = Field(min_length=12, max_length=128)


class AuthTokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    account_id: uuid.UUID
    actor_id: uuid.UUID
    role: str
