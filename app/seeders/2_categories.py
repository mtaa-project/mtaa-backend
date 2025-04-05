import asyncio

from sqlmodel import select

from app.db.database import async_session
from app.models.category_model import Category

CATEGORIES_TO_SEED = [
    {"id": 1, "name": "Real Estate"},
    {"id": 2, "name": "Vehicles"},
    {"id": 3, "name": "Electronics"},
    {"id": 4, "name": "Home & Garden"},
    {"id": 5, "name": "Fashion"},
    {"id": 6, "name": "Sports & Outdoors"},
]


async def seed_categories():
    async with async_session() as session:
        for cat in CATEGORIES_TO_SEED:
            result = await session.execute(
                select(Category).where(Category.id == cat["id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Category with ID {cat['id']} already exists: {existing.name}")
                continue

            category = Category(id=cat["id"], name=cat["name"])
            session.add(category)
            print(f"Added category: {cat['name']}")

        await session.commit()
        print("Category seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
