from datetime import date
from typing import Any

from pydantic import BaseModel


class ReportRequestSchema(BaseModel):
    start_date: date
    end_date: date


class ReportResponseSchema(BaseModel):
    report_type: str
    start_date: date
    end_date: date
    data: list[dict[str, Any]]
