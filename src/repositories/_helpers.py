import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.role import Role


def as_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


def as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else date.fromisoformat(value)


def get_role_id(db: Session, name: str) -> uuid.UUID:
    role = db.scalar(select(Role).where(Role.name == name))
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The {name} role has not been configured.",
        )
    return role.role_id


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def resolve_period(
    *,
    year: int | None = None,
    month: int | None = None,
    start_month: int | None = None,
    end_month: int | None = None,
) -> tuple[date, date]:
    """Resolve an inclusive reporting period from optional filters.

    Defaults to the current month and year when nothing is provided. Supports a
    single month, a month range within one year, or a full year.
    """
    today = datetime.now(UTC).date()
    if year is None and month is None and start_month is None and end_month is None:
        # Nothing provided -> assume the current month and year.
        year, month = today.year, today.month
    year = year if year is not None else today.year
    if year < 1 or year > 9999:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="year must be a valid calendar year.",
        )

    months: list[int] = []
    if month is not None and not 1 <= month <= 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must be between 1 and 12.",
        )
    if month is not None:
        months.append(month)
    if start_month is not None or end_month is not None:
        if start_month is None or end_month is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "start_month and end_month must be provided together."
                ),
            )
        if not 1 <= start_month <= 12 or not 1 <= end_month <= 12:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Months must be between 1 and 12.",
            )
        if start_month > end_month:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_month must be on or before end_month.",
            )
        months = list(range(start_month, end_month + 1))

    if not months:
        # Only a year provided (without a month) -> whole year.
        start_month, end_month = 1, 12
    else:
        start_month, end_month = min(months), max(months)

    start_date = date(year, start_month, 1)
    end_date = date(year, end_month, _last_day_of_month(year, end_month))
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be on or before end_date.",
        )
    return start_date, end_date
