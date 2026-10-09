from datetime import date
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database import get_session


class ReportRepository:
    def __init__(self, db: Annotated[Session, Depends(get_session)]) -> None:
        self.db = db

    def get_monthly_records(
        self,
        start_date: date,
        end_date: date,
        **filters: Any,
    ):
        pass