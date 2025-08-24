from enum import Enum
from typing import Annotated
from fastapi import APIRouter, Query

from core.utils import FilterParams, Tags


class EnumModelName(str, Enum):
    MODEL_A = "MODEL_A"
    MODEL_B = "MODEL_B"
    MODEL_C = "MODEL_C"


router = APIRouter()


@router.get("/models/{model_name}", tags=[Tags.models])
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
