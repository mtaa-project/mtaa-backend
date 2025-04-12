import asyncio

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.address_model import Address
from app.models.user_model import User

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 3
LISTINGS_PER_USER = 20


async def seed_addresses():
    async with async_session() as session:
        result = await session.execute(select(User))
        users: list[User] = result.scalars().all()

        user_addresses = {}
        for user in users:
            address = Address(
                is_primary=True,
                visibility=True,
                country=fake.country_code(representation="alpha-2"),
                city=fake.city(),
                street=fake.street_address(),
                user_id=user.id,
                latitude=1.2,
                longitude=2.2,
                postal_code=fake.postcode(),
            )
            session.add(address)
            user_addresses[user.id] = address

        await session.commit()
        print("🏠 Added 1 primary address per user")


if __name__ == "__main__":
    asyncio.run(seed_addresses())
