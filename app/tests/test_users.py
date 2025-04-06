import os

os.environ["TESTING"] = "1"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, create_engine

from app.api.dependencies import get_async_session, get_user
from app.api.main import app
from app.models.user_model import User

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


# initialize database
@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with TestSessionLocal() as session:
        session.add(
            User(
                firstname="Test",
                lastname="User",
                email="test@example.com",
            )
        )
        await session.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.mark.asyncio
async def test_get_users():
    headers = {"Authorization": "Bearer dummy_token"}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/users/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"
