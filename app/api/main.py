import asyncio
from typing import Annotated

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.security import HTTPBearer
from pydantic import BaseModel, conlist

from app.api.middleware import authenticate_request
from app.api.routes import auth_route, listings, users_route

security = HTTPBearer()
app = FastAPI(dependencies=[Depends(security)])

app.include_router(auth_route.router)
app.include_router(users_route.router)
app.include_router(listings.router)
app.middleware("http")(authenticate_request)
