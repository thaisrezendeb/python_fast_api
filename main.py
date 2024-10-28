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
    model_a = "model_a"
    model_b = "model_b"
    model_c = "model_c"


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
    if model_name is EnumModelName.model_a:
        message = "Selected model A"
    elif model_name.value == EnumModelName.model_b:     # another way to compare
        message = "Selected model B"

    return {
        "modelName": model_name,
        "message": message
    }


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return { "filePath": file_path }
