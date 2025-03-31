from typing import AsyncGenerator

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db.database import async_session

security = HTTPBearer()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_user(request: Request):
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="User not authenticated.")
    return request.state.user
