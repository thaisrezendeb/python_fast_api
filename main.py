from enum import Enum
from fastapi import FastAPI
from fastapi import Query, Path, Body
from pydantic import BaseModel, Field, HttpUrl
from core import config
from typing import Annotated, Literal


app = FastAPI(title=config.settings.PROJECT_NAME,
              version=config.settings.PROJECT_VERSION)


class FilterParams(BaseModel):
    model_config = { "extra": "forbid" } # Forbid any extra param
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal['created_at', 'updated_at'] = 'created_at'
    tags: set[str] = set()


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None, 
        title="The description of the item",
        max_length=300,
        examples=["Some description to Item"]
    )
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = Field(default=None, examples=[13.2])    # Examples could be here
    is_offer: bool | None = None      # Optional
    images: list[Image] | None = None

    # Examples could be also here
    # model_config = {
    #     "json_schema_extra": {
    #         "examples": [
    #             {
    #                 "name": "Foo",
    #                 "description": "A very nice Item",
    #                 "price": 35.4,
    #                 "tax": 3.2,
    #                 "is_offer": True
    #             }
    #         ]
    #     }
    # }


class Offer(BaseModel):
    name: str
    description: str | None = None
    total_price: float
    items: list[Item]


class User(BaseModel):
    username: str
    full_name: str | None = None


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
async def create_item(item: Annotated[Item, Body(embed=True)]):    # Embed a body parameter, only if you have a single body parameter
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
        item_id: Annotated[int, Path(title="The ID of the item to get", gt=0, le=1000)], # path parameter will be always required even when default value is None
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
def update_item(
        item_id: int, 
        user: User, 
        importance: Annotated[int, Body(gt=0)],     # Body parameter as a singular value (not Pydantic model)
        item: Annotated[
            Item, 
            Body(
                # examples=[  # And examples could be here too
                #     {
                #         "name": "Foo",
                #         "description": "A very nice Item",
                #         "price": 35.4,
                #         "tax": 3.2,
                #     },
                #     # Multiple examples
                #     {
                #         "name": "Bar",
                #         "price": "35.4",
                #     },
                #     {
                #         "name": "Baz",
                #         "price": "thirty five point four",
                #     },
                # ],
                openapi_examples={  # Hmmm.. didn't work to me. I don't know why...
                    "normal": {
                        "summary": "A normal example",
                        "description": "A **normal** item works correctly.",
                        "value": {
                            "name": "Foo",
                            "description": "A very nice Item",
                            "price": 35.4,
                            "tax": 3.2,
                        },
                    },
                    "converted": {
                        "summary": "An example with converted data",
                        "description": "FastAPI can convert price `strings` to actual `numbers` automatically",
                        "value": {
                            "name": "Bar",
                            "price": "35.4",
                        },
                    },
                    "invalid": {
                        "summary": "Invalid data is rejected with an error",
                        "value": {
                            "name": "Baz",
                            "price": "thirty five point four",
                        },
                    },
                },
            )
        ],
        q: str | None = None                        # Query parameter
    ):
    result = {
             "itemId": item_id,
             #  **item.model_dump()
             "user": user,
             "importance": importance
           }
    if q:
        result.update({"q": q})

    if item:
        result.update({ "item": item.model_dump() })

    return result


@app.get("/models/{model_name}")
async def get_by_model_name(
        model_name: EnumModelName, 
        filter_query: Annotated[FilterParams, Query()] # Query parameters in a Pydantic model
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


@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    for image in images:
        image.name += "_received"
    return images


@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    # Something like this
    # {
    #     "0": 0,
    #     "1": 0.2,
    #     "2": 1
    # }
    return weights