from fastapi import (
    FastAPI,
)

from app.api.routes import auth

app = FastAPI()

app.include_router(auth.router)
# app.include_router(products.router)
