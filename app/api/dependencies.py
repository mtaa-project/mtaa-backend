from typing import AsyncGenerator

from fastapi import Request
from fastapi.security import HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from ..db.database import async_session

security = HTTPBearer()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_user(request: Request):
    return request.state.user
