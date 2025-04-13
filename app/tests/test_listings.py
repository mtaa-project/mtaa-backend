import os

os.environ["TESTING"] = "1"

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.models.user_model import User
from app.tests.conftest import TestSessionLocal

fake = Faker()

user = User(
    firstname="Test",
    lastname="Seller",
    email="test@example.com",
)

address = Address(
    is_primary=True,
    visibility=True,
    country="SK",
    city="Bratislava",
    street="Testova 123",
    postal_code="81101",
    latitude=fake.latitude(),
    longitude=fake.longitude(),
)

category = Category(name="Byty")


@pytest_asyncio.fixture(scope="module", autouse=True)
async def seed_data():
    async with TestSessionLocal() as session:
        user.addresses = [address]
        session.add(user)
        await session.commit()

        await session.refresh(address)
        await session.refresh(user)

        session.add(category)
        await session.commit()
        await session.refresh(category)


@pytest.mark.asyncio
async def test_create_listing(async_client: AsyncClient):
    payload = {
        "title": "Testovací inzerát",
        "description": "Krásny byt v centre",
        "price": "150000.00",
        "listing_status": ListingStatus.ACTIVE.value,
        "offer_type": OfferType.BUY.value,
        "address_id": address.id,
        "category_ids": [category.id],
        "image_paths": ["asd/123"],
    }
    response = await async_client.post("/listings/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["price"] == payload["price"]
    assert data["address"]["id"] == address.id
    assert data["categories"][0]["id"] == category.id


@pytest.mark.asyncio
async def test_get_listing_by_id(async_client: AsyncClient):
    payload = {
        "title": "Testovací inzerát",
        "description": "Krásny byt v centre",
        "price": "150000.00",
        "listing_status": ListingStatus.ACTIVE.value,
        "offer_type": OfferType.BUY.value,
        "address_id": address.id,
        "category_ids": [category.id],
        "image_paths": ["asd/123"],
    }
    response = await async_client.post("/listings/", json=payload)
    if response.status_code != status.HTTP_201_CREATED:
        print("Response error on create:", response.json())

    assert response.status_code == status.HTTP_201_CREATED

    default_listing = response.json()
    default_listing_id = default_listing["id"]
    print("idcko:", default_listing_id)
    response = await async_client.get(f"/listings/{default_listing_id}")
    print(response.json())
    assert response.status_code == status.HTTP_200_OK

    expected_listing_data = response.json()

    assert expected_listing_data["id"] == default_listing_id
    assert expected_listing_data["title"] == payload["title"]
    assert expected_listing_data["description"] == payload["description"]
    assert expected_listing_data["price"] == payload["price"]
    assert expected_listing_data["listing_status"] == payload["listing_status"]
    assert expected_listing_data["offer_type"] == payload["offer_type"]
    assert expected_listing_data["address"]["id"] == payload["address_id"]
    assert expected_listing_data["categories"][0]["id"] == payload["category_ids"][0]
