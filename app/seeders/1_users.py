import asyncio
import random
from datetime import datetime, timezone
from decimal import Decimal

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.offer_type import OfferType
from app.models.listing_model import Listing
from app.models.rent_listing_model import RentListing
from app.models.sale_lisitng_model import SaleListing
from app.models.user_model import User
from app.models.user_review_model import UserReview

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 3
LISTINGS_PER_USER = 20


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
        print(f"✅ Seeded {NUM_USERS} users")

        # Refresh users to get their IDs
        for user in users:
            await session.refresh(user)

        # 2) Assign a primary address to each user
        user_addresses = {}
        for user in users:
            address = Address(
                is_primary=True,
                visibility=True,
                country=fake.country_code(representation="alpha-2"),
                city=fake.city(),
                zip_code=fake.postcode(),
                street=fake.street_address(),
                user_id=user.id,
            )
            session.add(address)
            user_addresses[user.id] = address

        await session.commit()
        print("🏠 Added 1 primary address per user")

        for address in user_addresses.values():
            await session.refresh(address)

        # 3) Reviews for each user
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

        # 4) Load existing categories (created by another seeder)
        result = await session.execute(select(Category))
        categories: list[Category] = result.scalars().all()
        if not categories:
            print("⚠️  No categories found. Run the category seeder first.")
            return

        # 5) Generate listings
        listings_count = 0
        for user in users:
            for _ in range(LISTINGS_PER_USER):
                # Select a random OfferType
                offer_type = random.choice(list(OfferType))
                # Create a listing
                listing = Listing(
                    title=fake.sentence(nb_words=6),
                    description=fake.paragraph(nb_sentences=3),
                    price=Decimal(f"{random.uniform(10, 1000):.2f}"),
                    offer_type=offer_type,
                    seller_id=user.id,
                    address_id=user_addresses[user.id].id,
                    # listing_status remains ACTIVE by default
                )
                session.add(listing)
                await session.flush()

                # We need to flush so that listing.id is available

                # Assign one random category (or you can assign more)
                random_category = random.choice(categories)
                # listing.categories = [random_category]

                # If it's SALE or BOTH, 50% chance the listing will be "sold"
                if offer_type in [OfferType.SELL, OfferType.BOTH]:
                    if random.random() < 0.5:
                        buyer = random.choice(users)
                        sale_entry = SaleListing(
                            listing_id=listing.id,
                            buyer_id=buyer.id,
                            # sold_date default => datetime.now(UTC), or custom
                        )
                        session.add(sale_entry)

                # If it's RENT or BOTH, 50% chance the listing will be "rented"
                if offer_type in [OfferType.LEND, OfferType.BOTH]:
                    if random.random() < 0.5:
                        renter = random.choice(users)
                        rent_entry = RentListing(
                            listing_id=listing.id,
                            renter_id=renter.id,
                            # start_date default => datetime.now()
                            # end_date = ...
                        )
                        session.add(rent_entry)

                listings_count += 1

        await session.commit()
        print(
            f"🏷️ Seeded {listings_count} listings (approx. {LISTINGS_PER_USER} per user)"
        )


if __name__ == "__main__":
    asyncio.run(seed_users_with_all_data())
