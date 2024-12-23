from enum import Enum
from turtle import st
from fastapi import FastAPI, Response, status, Form, File, UploadFile
from fastapi import Query, Path, Body, Cookie, Header
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from core import config
from typing import Annotated, Literal, Any, Union
from datetime import datetime, time, timedelta
from uuid import UUID


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
    tags: list[str] = []

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


class BaseItem(BaseModel):
    name: str | None = None
    description: str | None = None


class ItemList(BaseItem):
    pass


class CarItem(BaseItem):
    type: str = "car"


class PlaneItem(BaseItem):
    type: str = "plane"
    size: int


class Offer(BaseModel):
    name: str
    description: str | None = None
    total_price: float
    items: list[Item]


class BaseUser(BaseModel):
    username: str
    full_name: str | None = None
    email: EmailStr


class UserIn(BaseUser):
    password: str


class UserDb(BaseUser):
    hashed_password: str
    

class Cookies(BaseModel):
    model_config = {"extra": "forbid"}

    session_id: str
    social_media_1_tracker: str | None = None
    social_media_2_tracker: str | None = None


class CommonHeaders(BaseModel):
    model_config = {"extra": "forbid"}
    
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []


class EnumModelName(str, Enum):
    MODEL_A = "MODEL_A"
    MODEL_B = "MODEL_B"
    MODEL_C = "MODEL_C"


class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


@app.get("/")
def hello_api():
    return {"projectName": app.title,
            "projectVersion": app.version}


@app.get("/items/", response_model_exclude_unset=True)
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
    ] = None,
    ads_id: Annotated[str | None, Cookie()] = None,
    user_agent: Annotated[str | None, Header()] = None,     # Automatically onverts "_" into "-", so the real header param is user-agent
    strange_header: Annotated[str | None, Header(
        convert_underscores=False                           # Use this if you don't want to autoconvert underscores to hyphens
    )] = None ,
    x_token: Annotated[list[str] | None, Header()] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    if ads_id:
        results.update({ "ads_id": ads_id })
    if user_agent:
        results.update({ "user_agent": user_agent })
    if strange_header:
        results.update({ "strange_header": strange_header })
    if x_token: 
        results.update({ "X-Token values:": x_token })
    return results


@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Annotated[Item, Body(embed=True)]):    # Embed a body parameter, only if you have a single body parameter
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({
            "price_with_tax": price_with_tax
        })
    return item_dict


items_l = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]


@app.get("/items/list", response_model=list[ItemList])
async def read_items_list():
    return items_l


@app.get("/items/{item_id}")
def find_item_by_item_id(
        *, # kwargs -  all the following parameters should be called as keyword arguments (key-value pairs) - to avoid error "Non-default argument follows default argument"
        item_id: Annotated[int, Path(title="The ID of the item to get", gt=0, le=1000)], # path parameter will be always required even when default value is None
        q: str,
        size: Annotated[float, Query(gt=0, lt=10.5)],
        cookies: Annotated[Cookies, Cookie()],
        headers: Annotated[CommonHeaders, Header()]
    ):
    results =  { "itemId": item_id }
    if q:
        results.update({ "q": q })
    if size:
        results.update({ "size": size })
    if cookies:
        results.update({ "cookies": cookies })
    if headers:
        results.update({ "headers": headers })
    return results


@app.put("/items/{item_id}")
def update_item(
        item_id: UUID, 
        user: BaseUser, 
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
        start_datetime: Annotated[datetime, Body()],
        end_datetime: Annotated[datetime, Body()],
        process_after: Annotated[timedelta, Body()],
        repeat_at: Annotated[time | None, Body()] = None,
        q: str | None = None                        # Query parameter
    ) -> Any:
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    result = {
             "itemId": item_id,
             #  **item.model_dump()
             "user": user,
             "importance": importance,
             "start_datetime": start_datetime,
             "end_datetime": end_datetime,
             "process_after": process_after,
             "repeat_at": repeat_at,
             "start_process": start_process,
             "duration": duration,
           }
    if q:
        result.update({"q": q})

    if item:
        result.update({ "item": item.model_dump() })

    return result


items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The Bar fighters", "price": 62, "tax": 20.2},
    "baz": {
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
        "tax": 10.5,
    },
}


@app.get(
    "/items/{item_id}/name",
    response_model=Item,
    response_model_include={"name", "description"},
)
async def read_item_name(item_id: str):
    return items[item_id]


@app.get("/items/{item_id}/public", response_model=Item, response_model_exclude={"tax"})
async def read_item_public_data(item_id: str):
    return items[item_id]


items_t = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


@app.get("/items/{item_id}/transport", response_model=Union[PlaneItem, CarItem])
async def read_item_transport(item_id: str):
    return items_t[item_id]


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
async def create_offer(offer: Offer) -> Offer:
    return offer


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]) -> list[Image]:
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
    return 


@app.get("/keyword-weights/", response_model=dict[str, float])
async def read_keyword_weights():
    return {"foo": 2.3, "bar": 3.4}


def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserDb(**user_in.model_dump(),                 # **user_in.model_dump() is an unwrap - it will pass all attributes as key: value, avoiding refactoring when some change occurs in the base class
                        hashed_password=hashed_password)        # Changing a key explicitly
    print("User saved! ..not really")
    return user_in_db


@app.post("/user/", response_model=BaseUser)
async def create_user(user: UserIn):
    user_saved = fake_save_user(user)
    return user_saved


@app.get("/portal", response_model=None)
async def get_portal(teleport: bool = False) -> Response | dict:
    if teleport:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    # return JSONResponse(content={"message": "Here's your interdimensional portal."})
    return {"message": "Here's your interdimensional portal."}


@app.get("/teleport")
async def get_teleport() -> RedirectResponse:
    return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return username


@app.post("/login2/")
async def login_form(data: Annotated[FormData, Form()]):
    return data


@app.post("/file/")
async def create_file(file: Annotated[bytes | None, File(description="A file read as bytes")] = None):
    if not file:
        return { "message": "No upload file sent" }
    else:
        return { "file_size": len(file) }


@app.post("/files/")
async def create_files(files: Annotated[list[bytes] | None, File()] = None):
    return {"file_sizes": [len(file) for file in files]}


@app.post("/uploadfile/")
async def create_upload_file(file: Annotated[UploadFile, File(description="A file read as UploadFile")]):
    return { "filename": file.filename }


@app.post("/uploadfiles/")
async def create_upload_files(files: Annotated[list[UploadFile], File(description="A file read as UploadFile")]):
    return { "filename": [file.filename for file in files] }


@app.post("/files_and_forms/")
async def create_files_and_forms(
    file_a: Annotated[bytes, File()],
    file_b: Annotated[UploadFile, File()],
    token: Annotated[str, Form()]
):
    return {
        "file_a_size": len(file_a),
        "token": token,
        "file_b_content_type": file_b.content_type
    }