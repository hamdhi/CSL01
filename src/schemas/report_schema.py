import uuid
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict, model_validator

from src.repositories._helpers import resolve_period


class ReportRequestSchema(BaseModel):
    """Report period filter.

    Prefer the flexible ``year`` / ``month`` / ``start_month`` / ``end_month``
    fields. When nothing is provided the current month and year are assumed.
    The explicit ``start_date`` / ``end_date`` fields remain supported for
    backward compatibility and take precedence when both are provided.
    """

    year: int | None = None
    month: int | None = None
    start_month: int | None = None
    end_month: int | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _validate_explicit_dates(self) -> "ReportRequestSchema":
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError(
                "start_date and end_date must be provided together."
            )
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date must be on or before end_date.")
        return self

    def resolve_period(self) -> tuple[date, date]:
        """Return the inclusive (start_date, end_date) for this request."""
        from src.repositories._helpers import resolve_period as _resolve

        if self.start_date is not None and self.end_date is not None:
            return self.start_date, self.end_date
        return _resolve(
            year=self.year,
            month=self.month,
            start_month=self.start_month,
            end_month=self.end_month,
        )


def report_period_dependency(
    year: Annotated[int | None, Query(ge=1970, le=9999)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    start_month: Annotated[int | None, Query(ge=1, le=12)] = None,
    end_month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> tuple[date, date]:
    """Resolve the reporting period from optional query parameters.

    When nothing is provided the current month (day 1 to last day) and current
    year are assumed. Supports a single month, a month range within one year,
    or a full year.
    """
    return resolve_period(
        year=year,
        month=month,
        start_month=start_month,
        end_month=end_month,
    )


ReportPeriodParam = Annotated[tuple[date, date], Depends(report_period_dependency)]


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
