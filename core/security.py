from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class FormData(BaseModel):
    username: str
    password: str
    model_config = {"extra": "forbid"}


class Cookies(BaseModel):
    model_config = {"extra": "forbid"}

    session_id: str
    social_media_1_tracker: str | None = None
    social_media_2_tracker: str | None = None


def query_extractor(q: str | None = None):
    return q


def query_or_cookie_extractor(
        q: Annotated[str, Depends(query_extractor)],
        last_query: Annotated[str, None, Cookie()] = None
):
    if not q:
        return last_query
    return q


def fake_password_hasher(raw_password: str):
    return "supersecret" + raw_password


async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
