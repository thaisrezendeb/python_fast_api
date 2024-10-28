from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel
from core.config import settings


app = FastAPI(title=settings.PROJECT_NAME,
              version=settings.PROJECT_VERSION)


class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None      # Optional


class EnumModelName(str, Enum):
    MODEL_A = "model_a"
    MODEL_B = "model_b"
    MODEL_C = "model_c"


@app.get("/")
def hello_api():
    return { "projectName": app.title,
             "projectVersion": app.version }


@app.get("/items/{item_id}")
def find_item_by_item_id(item_id: int, q: str | None = None):
    return { "itemId": item_id,
             "q": q }


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {
             "itemId": item_id,
             "itemName": item.name,
             "itemPrice": item.price
           }


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
    return { "filePath": file_path }


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
