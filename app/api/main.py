from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from firebase_admin import _apps, auth, credentials, initialize_app

from app.api.routes import auth_route, users_route

if not _apps:
    cred = credentials.Certificate("mtaa-project-service-account.json")
    initialize_app(cred)

app = FastAPI()

app.include_router(auth_route.router)
app.include_router(users_route.router)


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
        raise JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing authentication token",
        )
    try:
        auth.verify_id_token(token)
        return await call_next(request)
    except Exception as e:
        raise JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
