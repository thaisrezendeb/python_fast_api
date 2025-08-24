from enum import Enum
from typing import Annotated
from fastapi import APIRouter, Query
from sqlmodel import SQLModel, Field as FieldSQL

from core.utils import FilterParams, Tags


class EnumModelName(str, Enum):
    MODEL_A = "MODEL_A"
    MODEL_B = "MODEL_B"
    MODEL_C = "MODEL_C"


class Hero(SQLModel, table=True):
    id: int | None = FieldSQL(default=None, primary_key=True)
    name: str = FieldSQL(index=True)
    age: int | None = FieldSQL(default=None, index=True)
    secret_name: str


router = APIRouter(tags=[Tags.models])


@router.get("/models/{model_name}")
async def get_by_model_name(
        model_name: EnumModelName,
        filter_query: Annotated[FilterParams, Query()]  # Query parameters in a Pydantic model
):
    message = "Selected model C"
    if model_name is EnumModelName.MODEL_A:
        message = "Selected model A"
    elif model_name.value == EnumModelName.MODEL_B:     # another way to compare
        message = "Selected model B"

    return {
        "modelName": model_name,
        "message": message,
        "filter_query": filter_query
    }
