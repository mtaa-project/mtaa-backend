import asyncio

from faker import Faker

from app.db.database import async_session
from app.models.user_model import User

fake = Faker()

NUM_USERS = 10


async def seed_users_with_all_data():
    async with async_session() as session:
        # 1) Seed users
        users = []
        for _ in range(NUM_USERS):
            user = User(
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                email=fake.unique.email(),
                phone_number=fake.phone_number(),
            )
            users.append(user)
            session.add(user)

        await session.commit()
        print(f"Seeded {NUM_USERS} users")


if __name__ == "__main__":
    asyncio.run(seed_users_with_all_data())
