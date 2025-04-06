import os

os.environ["TESTING"] = "1"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.api.dependencies import get_async_session, get_user
from app.api.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    DATABASE_URL,
    # echo=False,
    connect_args={"check_same_thread": False},
    # ensure that we are connecting to the same
    # in memory database
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_async_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


async def override_get_user():
    return {"email": "test@example.com"}


app.dependency_overrides[get_async_session] = override_get_async_session
app.dependency_overrides[get_user] = override_get_user


@pytest_asyncio.fixture(scope="module", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture()
async def async_client() -> AsyncClient:
    headers = {"Authorization": "Bearer fake"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers=headers
    ) as client:
        yield client
