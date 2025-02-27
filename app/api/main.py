from fastapi import (
    FastAPI,
)
from app.api.routes import products
from app.core import config
from app.db.database import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(products.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
