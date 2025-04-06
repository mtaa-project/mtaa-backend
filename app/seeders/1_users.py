import asyncio

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.user_model import User

fake = Faker()
NUM_USERS = 10


async def seed_users_with_all_data():
    async with async_session() as session:
        users = []

        for _ in range(NUM_USERS):
            email = fake.unique.email()

            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User with email {email} already exists. Skipping.")
                continue

            user = User(
                firstname=fake.first_name(),
                lastname=fake.last_name(),
                email=email,
                phone_number=fake.phone_number(),
            )
            users.append(user)
            session.add(user)

        # Add default user if not present
        default_email = "peter@gmail.com"
        result = await session.execute(select(User).where(User.email == default_email))
        existing_default = result.scalar_one_or_none()

        if existing_default:
            print(f"Default user with email {default_email} already exists. Skipping.")
        else:
            default_user = User(
                firstname="Peter",
                lastname="Griffin",
                email=default_email,
                phone_number=fake.phone_number(),
            )
            users.append(default_user)
            session.add(default_user)

        await session.commit()
        print(f"Seeded {len(users)} users")


if __name__ == "__main__":
    asyncio.run(seed_users_with_all_data())
