import uuid

from pydantic import BaseModel, ConfigDict


class ZonalOfficerCreateRequestSchema(BaseModel):
    name: str
    mini_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None


class ZonalOfficerUpdateRequestSchema(BaseModel):
    name: str | None = None
    mini_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None


class ZonalOfficerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zonal_id: uuid.UUID
    name: str
    mini_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
