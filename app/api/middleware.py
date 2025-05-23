import os

from fastapi import Request, status
from fastapi.responses import JSONResponse
from firebase_admin import _apps, auth, credentials, initialize_app

firebase_app = None


def init_firebase():
    global firebase_app
    if not _apps:
        cred = credentials.Certificate("./mtaa-project-service-account.json")
        firebase_app = initialize_app(
            cred,
            # https://firebase.google.com/docs/storage/admin/start
            {"storageBucket": "mtaa-project-5235a.firebasestorage.app"},
            # {"storageBucket": "mtaa-project-5235a.appspot.com"}   # ⬅ správne
        )


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
        if os.environ.get("TESTING") == "1":
            request.state.user = {"email": "test@example.com"}
            return await call_next(request)

        user = auth.verify_id_token(token, firebase_app)
        request.state.user = user
        return await call_next(request)
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": f"{e}"},
        )
