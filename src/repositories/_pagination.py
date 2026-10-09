from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginate(
    db: Session,
    statement: Any,
    offset: int,
    limit: int,
) -> dict[str, Any]:
    count_statement = select(func.count()).select_from(
        statement.order_by(None).subquery()
    )
    total = db.scalar(count_statement)
    items = list(
        db.scalars(statement.offset(offset).limit(limit)).all()
    )
    return {
        "items": items,
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }
