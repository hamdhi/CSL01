from pydantic import BaseModel


class PaginatedDataSchema[ItemT](BaseModel):
    items: list[ItemT]
    total: int
    limit: int
    offset: int
