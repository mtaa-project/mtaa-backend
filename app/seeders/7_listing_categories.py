import asyncio
import random

from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.db.database import async_session
from app.models.category_model import Category
from app.models.listing_model import Listing

LISTING_MIN_CATEGORIES = 0
LISTING_MAX_CATEGORIES = 2


async def seed_listings_categories():
    async with async_session() as session:
        # Retrieve all listings from the database
        result = await session.execute(
            select(Listing).options(selectinload(Listing.categories))
        )
        listings: list[Listing] = result.scalars().all()

        # Retrieve all categories from the database
        result = await session.execute(select(Category))
        categories: list[Category] = result.scalars().all()

        if not categories:
            print("No categories found. Please run the category seeder first.")
            return

        total_assigned = 0

        # For each listing, assign a random number of categories (0, 1, or 2)
        for listing in listings:
            # Decide how many categories to assign for this listing (0-2)
            num_categories = random.randint(
                LISTING_MIN_CATEGORIES, LISTING_MAX_CATEGORIES
            )
            # Make sure not to request more categories than are available
            num_categories = min(num_categories, len(categories))
            # Randomly select unique categories for the listing
            selected_categories = random.sample(categories, num_categories)

            # Assign each selected category using the relationship
            for category in selected_categories:
                if category not in listing.categories:
                    listing.categories.append(category)
                    total_assigned += 1

        # Commit all changes to the database
        await session.commit()
        print(
            f"Assigned categories to listings: {total_assigned} category relationships created."
        )


if __name__ == "__main__":
    asyncio.run(seed_listings_categories())
