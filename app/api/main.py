from fastapi import (
    FastAPI,
)
from app.api.routes import products
from app.db.database import create_db_and_tables


app = FastAPI()

app.include_router(products.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
