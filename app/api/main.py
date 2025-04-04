from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from firebase_admin import _apps, auth, credentials, initialize_app

from app.api.middleware import authenticate_request
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


app.middleware("http")(authenticate_request)
