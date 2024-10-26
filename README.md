#

## Running on Windows

Create a virtual environment

    python.exe -m venv .venv

Activate the virtual environment 

- Using Power Shell

        .\.venv\Scripts\Activate.ps1 

- Using CMD

        .\.venv\Scripts\Activate.bat

Install libraries from _requirements.txt_

    pip install -r requirements.txt

## Executing the API

    fastapi dev main.py

## API Documentation

Documentation available on 

    http://127.0.0.1:8000/docs

Or 

    http://127.0.0.1:8000/redoc