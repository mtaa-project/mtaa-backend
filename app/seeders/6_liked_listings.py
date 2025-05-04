import asyncio
import random

from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.db.database import async_session
from app.models.listing_model import Listing
from app.models.user_model import User

PER_USER_MIN_LISTING_COUNT = 15
PER_USER_MAX_LISTING_COUNT = 20


async def seed_users_favorite_listings_with_relationship():
    async with async_session() as session:
        # Retrieve all users and eagerly load their favorite_listings
        result = await session.execute(
            select(User).options(selectinload(User.favorite_listings))
        )
        users: list[User] = result.scalars().all()

        # Retrieve all listings from the database
        result = await session.execute(select(Listing))
        listings: list[Listing] = result.scalars().all()

        if not listings:
            print("No listings found. Run the listing seeder first.")
            return

        total_favorites = 0

        for user in users:
            # Filter out listings that belong to the user (users can't like their own listings)
            candidate_listings = [
                listing for listing in listings if listing.seller_id != user.id
            ]
            if not candidate_listings:
                continue

            # Randomly decide how many listings the user will like (0 to 15, but no more than available)
            num_favorites = random.randint(
                PER_USER_MIN_LISTING_COUNT,
                min(PER_USER_MAX_LISTING_COUNT, len(candidate_listings)),
            )
            # Randomly select unique listings from the candidate list
            selected_listings = random.sample(candidate_listings, num_favorites)

            # Use the relationship to assign favorites
            # Since favorite_listings is already loaded, we avoid lazy-loading issues
            for listing in selected_listings:
                if listing not in user.favorite_listings:
                    user.favorite_listings.append(listing)
                    total_favorites += 1

        await session.commit()
        print(f"Seeded {total_favorites} favorite listings using relationships.")


if __name__ == "__main__":
    asyncio.run(seed_users_favorite_listings_with_relationship())
