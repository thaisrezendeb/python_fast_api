from enum import Enum
from fastapi import FastAPI
from fastapi import Query, Path
from pydantic import BaseModel
from core import config
from typing import Annotated


app = FastAPI(title=config.settings.PROJECT_NAME,
              version=config.settings.PROJECT_VERSION)


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    is_offer: bool | None = None      # Optional


class EnumModelName(str, Enum):
    MODEL_A = "MODEL_A"
    MODEL_B = "MODEL_B"
    MODEL_C = "MODEL_C"


@app.get("/")
def hello_api():
    return {"projectName": app.title,
            "projectVersion": app.version}


@app.get("/items/")
async def read_items(
    q: Annotated[
        str | None,
        Query(
            alias="item-query",
            title="Query string",
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            max_length=50,
            pattern="^fixedquery$",
            deprecated=True,
            include_in_schema=True
        )
    ] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({
            "price_with_tax": price_with_tax
        })
    return item_dict


@app.get("/items/{item_id}")
def find_item_by_item_id(
        *, # kwargs -  all the following parameters should be called as keyword arguments (key-value pairs) - to avoid error "Non-default argument follows default argument"
        item_id: Annotated[int, Path(title="The ID of the item to get", gt=1, le=1000)], # path parameter will be always required even when default value is None
        q: str,
        size: Annotated[float, Query(gt=0, lt=10.5)]
    ):
    results =  { "itemId": item_id }
    if q:
        results.update({ "q": q })
    if size:
        results.update({ "size": size })

    return results


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, q: str | None = None):
    result = {
             "itemId": item_id,
             **item.model_dump()
           }
    if q:
        result.update({"q": q})
    return result


@app.get("/models/{model_name}")
async def get_by_model_name(model_name: EnumModelName):
    message = "Selected model C"
    if model_name is EnumModelName.MODEL_A:
        message = "Selected model A"
    elif model_name.value == EnumModelName.MODEL_B:     # another way to compare
        message = "Selected model B"

    return {
        "modelName": model_name,
        "message": message
    }


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"filePath": file_path}


@app.get("/users/{user_id}/items/{item_id}")
async def get_items_by_user_id_and_item_id(
        user_id: int,
        item_id: str,
        q: str | None,
        short: bool = False
):
    item = {
        "item_id": item_id,
        "owner_id": user_id
    }

    if q:
        item.update(
            {
                "q": q
            }
        )

    if not short:
        item.update(
            {
                "description": "This is an amazing item that has a long description"
            }
        )

    return item
