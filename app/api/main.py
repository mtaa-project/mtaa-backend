from typing import Union

from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from app.api.routes import items


app = FastAPI()

app.include_router(items.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
