from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
)

from app.api.routes import products
from app.db.database import init_db


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
