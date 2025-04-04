from fastapi import Request, status
from fastapi.responses import JSONResponse
from firebase_admin import _apps, auth, credentials, initialize_app

if not _apps:
    cred = credentials.Certificate("mtaa-project-service-account.json")
    firebase_app = initialize_app(cred)


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
