from datetime import datetime, timedelta, time
from typing import Annotated, Any, Union
from uuid import UUID
from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Header, Path, Query, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from routers.files import Image
from core.utils import CommonQueryParams, CommonHeaders, MyCustomException, Tags, InternalError
from core.security import Cookies, oauth2_scheme, query_or_cookie_extractor, verify_key, verify_token
from routers.users import BaseUser, get_user


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


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

items_l = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]

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

items_t = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


router = APIRouter(tags=[Tags.items])


@router.get("/items/", response_model_exclude_unset=True)
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
    )] = None,
    x_token: Annotated[list[str] | None, Header()] = None
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    if ads_id:
        results.update({"ads_id": ads_id})
    if user_agent:
        results.update({"user_agent": user_agent})
    if strange_header:
        results.update({"strange_header": strange_header})
    if x_token:
        results.update({"X-Token values:": x_token})
    return results


@router.get("/items/params")
async def read_items_by_params(commons: Annotated[CommonQueryParams, Depends()]):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip: commons.skip + commons.limit]
    response.update({"items": items})
    return response


@router.get("/items/query")
async def read_query(
    query_or_default: Annotated[str, Depends(query_or_cookie_extractor, use_cache=False)],
):
    return {"q_or_cookie": query_or_default}


@router.get("/items/token",
            dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items_simple():
    return [{"item": "Foo"}, {"item": "Bar"}]


@router.post(
        "/items/",
        status_code=status.HTTP_201_CREATED,
        summary="Create an item",
        response_description="The created item"
)
async def create_item(
    item: Annotated[Item, Body(embed=True)],  # Embed a body parameter, only if you have a single body parameter
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


@router.get("/items/list", response_model=list[ItemList])
async def read_items_list():
    return items_l


@router.get("/items/{item_id}")
def find_item_by_item_id(
        *,  # kwargs -  all the following parameters should be called as keyword arguments
            # (key-value pairs) - to avoid error "Non-default argument follows default argument"
        item_id: Annotated[int, Path(title="The ID of the item to get", gt=0, le=1000)],  # path parameter will be
                                                                                          # always required even when
                                                                                          # default value is None
        q: str,
        size: Annotated[float, Query(gt=0, lt=10.5)],
        cookies: Annotated[Cookies, Cookie()],
        headers: Annotated[CommonHeaders, Header()]
):
    results = {"itemId": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    if cookies:
        results.update({"cookies": cookies})
    if headers:
        results.update({"headers": headers})
    return results


@router.put("/items/{item_id}")
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
        result.update({"item": item.model_dump()})

    return result


@router.patch("/items/{item_id}", response_model=Item)
async def patch_items(item_id: str, item: Item):
    stored_item_data = items[item_id]
    stored_item_model = Item(**stored_item_data)
    update_data = item.model_dump(exclude_unset=True)
    updated_item = stored_item_model.model_copy(update=update_data)
    items[item_id] = jsonable_encoder(updated_item)
    return updated_item


@router.get(
    "/items/{item_id}/name",
    response_model=Item,
    response_model_include={"name", "description"}
)
async def read_item_name(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
            headers={"X-Error": "There goes my error"}
        )
    return items[item_id]


@router.get("/items/{item_id}/public", response_model=Item, response_model_exclude={"tax"})
async def read_item_public_data(item_id: str):
    if item_id not in items:
        raise MyCustomException(name=item_id)
    return items[item_id]


@router.get("/items/{item_id}/transport", response_model=Union[PlaneItem, CarItem])
async def read_item_transport(item_id: str):
    return items_t[item_id]


@router.get("/items/{item_id}/username")
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


@router.get("/users/{user_id}/items/{item_id}", tags=[Tags.users, Tags.items])
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
