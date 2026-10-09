import uuid

from pydantic import BaseModel, Field


class ZoneCreateRequestSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    prov_id: uuid.UUID


class ZoneResponseSchema(BaseModel):
    zone_id: uuid.UUID
    name: str
    prov_id: uuid.UUID


class ProvinceResponseSchema(BaseModel):
    prov_id: uuid.UUID
    name: str
