import logging
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import _apps, auth, credentials, initialize_app
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db.database import async_session

if not _apps:
    cred = credentials.Certificate("mtaa-project-service-account.json")
    initialize_app(cred)

security = HTTPBearer()


def get_firebase_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný alebo expirovaný token",
        )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_user(request: Request):
    return request.state.user
