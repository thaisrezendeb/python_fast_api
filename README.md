# Welcome to my first FastAPI project

Hello! My name is Thaís Rezende and I'm a Telecommunication Engineer and System Analyst. I love programming and I have some knowing in Java, Python, Typescript, among others.

This project is part of a self-teach of backend technologies using Python as a basement. It's based on the official documentation available on https://fastapi.tiangolo.com/tutorial/

If you want to replicate my development, follow the steps below to prepare your environment.

## Clone this repository

    git@github.com:thaisrezendeb/python_fast_api.git

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

Using **Swagger UI** interface available on 

    http://127.0.0.1:8000/docs

Using **ReDoc** interface available on

    http://127.0.0.1:8000/redoc