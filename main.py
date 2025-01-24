from fastapi import Depends, FastAPI, Request, Response, status, Form, File, UploadFile, HTTPException
from fastapi import Query, Path, Body, Cookie, Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from enum import Enum
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from core import config
from typing import Annotated, Literal, Any, Union
from datetime import datetime, time, timedelta, timezone
from uuid import UUID
import jwt
from jwt.exceptions import InvalidTokenError


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


app = FastAPI(
    title=config.settings.PROJECT_NAME,
    version=config.settings.PROJECT_VERSION,
    #dependencies=[Depends(verify_token), Depends(verify_key)] # Dependency to all endpoints
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


class Tags(Enum):
    items = "items"
    files = "files"
    users = "users"
    offers = "offers"


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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class BaseUser(BaseModel):
    username: str
    full_name: str | None = None
    email: EmailStr
    disabled: bool | None = None


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


class MyCustomException(Exception):
    def __init__(self, name: str):
        self.name = name


class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit
        

class InternalError(Exception):
    pass


def get_user(db, username: str):
    try:
        if username in db:
            user_dict = db[username]
            return UserDb(**user_dict)
    except InternalError:
        print("We don't swallow the internal error here, we raise again 😎")
        raise


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[BaseUser, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def common_parameters(
        q: str | None = None, 
        skip: int = 0, 
        limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}


CommonsDep = Annotated[dict, Depends(common_parameters)]


def query_extractor(q: str | None = None):
    return q


def query_or_cookie_extractor(
        q: Annotated[str, Depends(query_extractor)],
        last_query: Annotated[str, None, Cookie()] = None
):
    if not q:
        return last_query
    return q


@app.exception_handler(MyCustomException)
async def my_custom_exception_handler(request: Request, exc: MyCustomException):
    return JSONResponse(
        status_code=status.HTTP_418_IM_A_TEAPOT,
        content={ "message": f"Oops! {exc.name} did something. There goes a rainbow..." }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    #return PlainTextResponse(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.get("/")
def hello_api():
    return {"projectName": app.title,
            "projectVersion": app.version}


@app.get("/items/", response_model_exclude_unset=True, tags=[Tags.items])
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


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/params", tags=[Tags.items])
async def read_items_by_params(commons: Annotated[CommonQueryParams, Depends()]):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip : commons.skip + commons.limit]
    response.update({"items": items})
    return response


@app.get("/items/query", tags=[Tags.items])
async def read_query(
    query_or_default: Annotated[str, Depends(query_or_cookie_extractor, use_cache=False)],
):
    return {"q_or_cookie": query_or_default}


@app.get("/items/token", tags=[Tags.items], dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]


@app.post(
        "/items/", 
        status_code=status.HTTP_201_CREATED, 
        tags=[Tags.items], 
        summary="Create an item",
        response_description="The created item"
    )
async def create_item(
    item: Annotated[Item, Body(embed=True)], # Embed a body parameter, only if you have a single body parameter
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
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


@app.get("/items/list", response_model=list[ItemList], tags=[Tags.items])
async def read_items_list():
    return items_l


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


@app.get("/items/{item_id}", tags=[Tags.items])
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


@app.put("/items/{item_id}", tags=[Tags.items])
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


@app.patch("/items/{item_id}", response_model=Item, tags=[Tags.items])
async def patch_items(item_id: str, item: Item):
    stored_item_data = items[item_id]
    stored_item_model = Item(**stored_item_data)
    update_data = item.model_dump(exclude_unset=True)
    updated_item = stored_item_model.model_copy(update=update_data)
    items[item_id] = jsonable_encoder(updated_item)
    return updated_item


@app.get(
    "/items/{item_id}/name",
    response_model=Item,
    response_model_include={"name", "description"},
    tags=[Tags.items]
)
async def read_item_name(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found",
            headers={"X-Error": "There goes my error"}
        )
    return items[item_id]


@app.get("/items/{item_id}/public", response_model=Item, response_model_exclude={"tax"}, tags=[Tags.items])
async def read_item_public_data(item_id: str):
    if item_id not in items:
        raise MyCustomException(name=item_id)
    return items[item_id]


items_t = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


@app.get("/items/{item_id}/transport", response_model=Union[PlaneItem, CarItem], tags=[Tags.items])
async def read_item_transport(item_id: str):
    return items_t[item_id]


@app.get("/items/{item_id}/username", tags=[Tags.items])
def get_item(item_id: str, username: Annotated[str, Depends(get_user)]):
    if item_id == "portal-gun":
        raise InternalError(
            f"The portal gun is too dangerous to be owned by {username}"
        )
    if item_id != "plumbus":
        raise HTTPException(
            status_code=404, detail="Item not found, there's only a plumbus here"
        )
    return item_id


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


@app.get("/files/{file_path:path}", tags=[Tags.files])
async def read_file(file_path: str):
    return {"filePath": file_path}


@app.get("/users/{user_id}/items/{item_id}", tags=[Tags.users, Tags.items])
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


@app.post("/offers/", tags=[Tags.offers])
async def create_offer(offer: Offer) -> Offer:
    return offer


@app.post("/files/images/multiple/", tags=[Tags.files])
async def create_multiple_images(images: list[Image]) -> list[Image]:
    for image in images:
        image.name += "_received"
    return images


@app.post("/index-weights/", deprecated=True)
async def create_index_weights(weights: dict[int, float]):
    # Something like this
    # {
    #     "0": 0,
    #     "1": 0.2,
    #     "2": 1
    # }
    return 


@app.get("/keyword-weights/", response_model=dict[str, float], deprecated=True)
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


@app.post("/user/", response_model=BaseUser, tags=[Tags.users])
async def create_user(user: UserIn):
    user_saved = fake_save_user(user)
    return user_saved


@app.get("/users/", tags=[Tags.users])
async def read_users(commons: CommonsDep):
    return commons


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me", tags=[Tags.users])
async def read_users_me(current_user: Annotated[BaseUser, Depends(get_current_active_user)]):
    return current_user


@app.get("/portal", response_model=None)
async def get_portal(commons: CommonsDep, teleport: bool = False) -> Response | dict:
    if teleport:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    # return JSONResponse(content={"message": "Here's your interdimensional portal."})
    return {
                "message": "Here's your interdimensional portal.",
                "commons": commons
           }


@app.get("/teleport")
async def get_teleport() -> RedirectResponse:
    return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")


@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return username


@app.post("/login2/")
async def login_form(data: Annotated[FormData, Form()]):
    return data


@app.post("/file/", tags=[Tags.files])
async def create_file(file: Annotated[bytes | None, File(description="A file read as bytes")] = None):
    if not file:
        return { "message": "No upload file sent" }
    else:
        return { "file_size": len(file) }


@app.post("/files/", tags=[Tags.files])
async def create_files(files: Annotated[list[bytes] | None, File()] = None):
    return {"file_sizes": [len(file) for file in files]}


@app.post(
        "/uploadfile/", 
        tags=[Tags.files],
        summary="Upload a file",
        description="Upload a single file"
    )
async def create_upload_file(file: Annotated[UploadFile, File(description="A file read as UploadFile")]):
    return { "filename": file.filename }


@app.post(
        "/uploadfiles/", 
        tags=[Tags.files],
        summary="Upload files",
        description="Upload a list of files"
    )
async def create_upload_files(files: Annotated[list[UploadFile], File(description="A file read as UploadFile")]):
    return { "filename": [file.filename for file in files] }


@app.post(
        "/files_and_forms/", 
        tags=[Tags.files],
        summary="Upload files and forms",
        description="Allows to upload files and add some form"
    )
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