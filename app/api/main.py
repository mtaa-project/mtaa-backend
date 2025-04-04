import os
import shutil
from typing import Annotated, List

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from firebase_admin import _apps, auth, credentials, initialize_app
from pydantic import BaseModel, conlist

from app.api.routes import auth_route, listings, users_route

app = None
if not _apps:
    cred = credentials.Certificate("mtaa-project-service-account.json")
    firebase_app = initialize_app(cred)

security = HTTPBearer()

app = FastAPI(dependencies=[Depends(security)])
# app = FastAPI()

app.include_router(auth_route.router)
app.include_router(users_route.router)
app.include_router(listings.router)


@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    if request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header is missing"},
        )

    token = auth_header.split(" ")[1] if " " in auth_header else None
    if not token:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content="Invalid or missing authentication token",
        )
    try:
        user = auth.verify_id_token(token, firebase_app)
        request.state.user = user
        return await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Invalid or expired token",
        )


app = FastAPI()
UPLOAD_DIRECTORY = "./uploads"

FilesType = Annotated[conlist(UploadFile, min_length=3, max_length=3), File(...)]


class ProductForm(BaseModel):
    product_name: str
    product_category: str
    files: FilesType


@app.post("/uploadfile")
async def create_upload_file(form: ProductForm = File(...)):
    saved_files = []
    for file in form.files:
        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append({"filename": file.filename, "location": file_location})
    print(form.product_name, form.product_category)
    return {
        "product_name": form.product_name,
        "product_category": form.product_category,
        "files": saved_files,
    }
