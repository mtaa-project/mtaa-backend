import asyncio
import random

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.user_model import User
from app.models.user_review_model import UserReview

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 30
LISTINGS_PER_USER = 20


async def seed_users_with_reviews():
    async with async_session() as session:
        # Fetch all users from the database
        result = await session.execute(select(User))
        users: list[User] = result.scalars().all()

        reviews = []
        for reviewer in users:
            # Determine a random number of reviews for each user
            num_reviews = random.randint(1, MAX_REVIEWS_PER_USER)
            # Create a list of possible users to review, excluding the reviewer
            possible_reviewees = [u for u in users if u.id != reviewer.id]
            for _ in range(num_reviews):
                # Select a random user to review
                reviewee = random.choice(possible_reviewees)
                # Create a new review
                review = UserReview(
                    text=fake.sentence(nb_words=12),  # Generate a random review text
                    rating=random.randint(
                        1, 5
                    ),  # Assign a random rating between 1 and 5
                    reviewer_id=reviewer.id,
                    reviewee_id=reviewee.id,
                )
                reviews.append(review)
                session.add(review)  # Add the review to the session

        await session.commit()  # Commit all changes to the database
        print(
            f"📝 Seeded {len(reviews)} user reviews"
        )  # Output the number of reviews created


if __name__ == "__main__":
    asyncio.run(seed_users_with_reviews())  # Run the seeding function
