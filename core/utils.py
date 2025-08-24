from enum import Enum
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import BaseModel, Field


class InternalError(Exception):
    pass


class Tags(Enum):
    items = "items"
    files = "files"
    users = "users"
    offers = "offers"
    models = "models"


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}  # Forbid any extra param
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal['created_at', 'updated_at'] = 'created_at'
    tags: set[str] = set()


class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


class CommonHeaders(BaseModel):
    model_config = {"extra": "forbid"}

    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []


class MyCustomException(Exception):
    def __init__(self, name: str):
        self.name = name


async def common_parameters(
        q: str | None = None,
        skip: int = 0,
        limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


CommonsDep = Annotated[dict, Depends(common_parameters)]
