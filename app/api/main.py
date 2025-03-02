from fastapi import (
    FastAPI,
)

from app.api.routes import products

app = FastAPI()

app.include_router(products.router)
