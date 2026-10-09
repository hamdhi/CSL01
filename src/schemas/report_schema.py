import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ReportRequestSchema(BaseModel):
    start_date: date
    end_date: date


class ReportResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: uuid.UUID | None = None
    report_type: str
    scope_type: str | None = None
    scope_id: uuid.UUID | None = None
    start_date: date
    end_date: date
    generated_at: datetime | None = None
    generated_by_id: uuid.UUID | None = None
    data: list[dict[str, Any]]
