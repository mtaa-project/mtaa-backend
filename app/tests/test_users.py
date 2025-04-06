import pytest
import pytest_asyncio

from app.models.user_model import User
from app.tests.conftest import TestSessionLocal


@pytest_asyncio.fixture(scope="module", autouse=True)
async def seed_data():
    async with TestSessionLocal() as session:
        user = User(firstname="Test", lastname="User", email="test@example.com")
        session.add(user)
        await session.commit()
        yield user


@pytest.mark.asyncio
async def test_get_users(async_client):
    response = await async_client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"
