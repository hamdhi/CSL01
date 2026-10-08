from pydantic import BaseModel


class StandardResponseSchema[DataT](BaseModel):
    status_code: int
    message: str
    data: DataT | None = None
