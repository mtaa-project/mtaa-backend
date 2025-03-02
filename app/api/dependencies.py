from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db.database import async_session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
