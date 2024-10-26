from typing import Union
from fastapi import FastAPI
from core.config import settings

app = FastAPI(title=settings.PROJECT_NAME,
              version=settings.PROJECT_VERSION)

@app.get("/")
def hello_api():
    return { "projectName": settings.PROJECT_NAME, 
             "projectVersion": settings.PROJECT_VERSION }

@app.get("/items/{itemId}")
def find_item_by_item_id(itemId: int, q: Union[str, None] = None):
    return { "itemId": itemId, 
             "q": q }
