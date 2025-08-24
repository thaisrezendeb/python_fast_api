from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
import jwt
from jwt.exceptions import InvalidTokenError

from core.utils import CommonsDep, InternalError, Tags
from core.security import ALGORITHM, SECRET_KEY, TokenData, fake_password_hasher, oauth2_scheme


class BaseUser(BaseModel):
    username: str
    full_name: str | None = None
    email: EmailStr
    disabled: bool | None = None


class UserIn(BaseUser):
    password: str


class UserDb(BaseUser):
    hashed_password: str


def get_user(db, username: str):
    try:
        if username in db:
            user_dict = db[username]
            return UserDb(**user_dict)
    except InternalError:
        print("We don't swallow the internal error here, we raise again 😎")
        raise


def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserDb(**user_in.model_dump(),                 # **user_in.model_dump() is an unwrap - it will pass
                                                                # all attributes as key: value, avoiding refactoring
                                                                # when some change occurs in the base class
                        hashed_password=hashed_password)        # Changing a key explicitly
    print("User saved! ..not really")
    return user_in_db


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


router = APIRouter(tags=[Tags.users])


@router.post("/user/", response_model=BaseUser)
async def create_user(user: UserIn):
    user_saved = fake_save_user(user)
    return user_saved


@router.get("/users/")
async def read_users(commons: CommonsDep):
    return commons


@router.get("/users/me")
async def read_users_me(current_user: Annotated[BaseUser, Depends(get_current_active_user)]):
    return current_user
