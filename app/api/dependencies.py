from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db.database import engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
