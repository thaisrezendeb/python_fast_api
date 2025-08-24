from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, HttpUrl

from core.utils import Tags


class Image(BaseModel):
    url: HttpUrl
    name: str


router = APIRouter()


@router.get("/files/{file_path:path}", tags=[Tags.files])
async def read_file(file_path: str):
    return {"filePath": file_path}


@router.post("/files/images/multiple/", tags=[Tags.files])
async def create_multiple_images(images: list[Image]) -> list[Image]:
    for image in images:
        image.name += "_received"
    return images


@router.post("/file/", tags=[Tags.files])
async def create_file(file: Annotated[bytes | None, File(description="A file read as bytes")] = None):
    if not file:
        return {"message": "No upload file sent"}
    else:
        return {"file_size": len(file)}


@router.post("/files/", tags=[Tags.files])
async def create_files(files: Annotated[list[bytes] | None, File()] = None):
    return {"file_sizes": [len(file) for file in files]}


@router.post(
        "/uploadfile/",
        tags=[Tags.files],
        summary="Upload a file",
        description="Upload a single file"
    )
async def create_upload_file(file: Annotated[UploadFile, File(description="A file read as UploadFile")]):
    return {"filename": file.filename}


@router.post(
        "/uploadfiles/",
        tags=[Tags.files],
        summary="Upload files",
        description="Upload a list of files"
    )
async def create_upload_files(files: Annotated[list[UploadFile], File(description="A file read as UploadFile")]):
    return {"filename": [file.filename for file in files]}


@router.post(
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
