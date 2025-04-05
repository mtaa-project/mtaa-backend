import asyncio
import random

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.user_model import User
from app.models.user_review_model import UserReview

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 3
LISTINGS_PER_USER = 20


async def seed_users_with_reviews():
    async with async_session() as session:
        result = await session.execute(select(User))
        users: list[User] = result.scalars().all()

        reviews = []
        for reviewer in users:
            num_reviews = random.randint(1, MAX_REVIEWS_PER_USER)
            possible_reviewees = [u for u in users if u.id != reviewer.id]
            for _ in range(num_reviews):
                reviewee = random.choice(possible_reviewees)
                review = UserReview(
                    text=fake.sentence(nb_words=12),
                    rating=random.randint(1, 5),
                    reviewer_id=reviewer.id,
                    reviewee_id=reviewee.id,
                )
                reviews.append(review)
                session.add(review)

        await session.commit()
        print(f"📝 Seeded {len(reviews)} user reviews")


if __name__ == "__main__":
    asyncio.run(seed_users_with_reviews())
