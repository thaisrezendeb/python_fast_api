from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field as FieldSQL
from core import config
import time as t
from core.db import create_db_and_tables
from core.utils import CommonsDep, MyCustomException
from routers import files, items, models, offers, users, credentials

"""
    ----------------------------------------------------------------
    This code is a mess, I know, I will fix it in the next versions
    ----------------------------------------------------------------
"""


app = FastAPI(
    title=config.settings.PROJECT_NAME,
    version=config.settings.PROJECT_VERSION,
    # dependencies=[Depends(verify_token), Depends(verify_key)] # Dependency to all endpoints
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Hero(SQLModel, table=True):
    id: int | None = FieldSQL(default=None, primary_key=True)
    name: str = FieldSQL(index=True)
    age: int | None = FieldSQL(default=None, index=True)
    secret_name: str


@app.exception_handler(MyCustomException)
async def my_custom_exception_handler(request: Request, exc: MyCustomException):
    return JSONResponse(
        status_code=status.HTTP_418_IM_A_TEAPOT,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # return PlainTextResponse(str(exc), status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = t.perf_counter()
    response = await call_next(request)
    process_time = t.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(credentials.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(files.router)
app.include_router(offers.router)
app.include_router(models.router)


@app.get("/")
def hello_api():
    return {"projectName": app.title,
            "projectVersion": app.version}


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
