from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    File,
    UploadFile,
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, conlist

from app.api.middleware import authenticate_request
from app.api.routes import auth_route, listings, users_route

security = HTTPBearer()
app = FastAPI(dependencies=[Depends(security)])

app.middleware("http")(authenticate_request)


app.include_router(auth_route.router)
app.include_router(users_route.router)
app.include_router(listings.router)


UPLOAD_DIRECTORY = "./uploads"

FilesType = Annotated[conlist(UploadFile, min_length=3, max_length=3), File(...)]


class ProductForm(BaseModel):
    product_name: str
    product_category: str
    files: FilesType


# @app.post("/uploadfile")
# async def create_upload_file(form: ProductForm = File(...)):
#     saved_files = []
#     for file in form.files:
#         file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
#         with open(file_location, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         saved_files.append({"filename": file.filename, "location": file_location})
#     print(form.product_name, form.product_category)
#     return {
#         "product_name": form.product_name,
#         "product_category": form.product_category,
#         "files": saved_files,
#     }
