import asyncio
import random
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

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 3
LISTINGS_PER_USER = 20


async def seed_users_listings():
    async with async_session() as session:
        result = await session.execute(select(User))
        users: list[User] = result.scalars().all()
        # 4) Load existing categories (created by another seeder)
        result = await session.execute(select(Category))
        categories: list[Category] = result.scalars().all()
        if not categories:
            print("⚠️  No categories found. Run the category seeder first.")
            return

        # 5) Generate listings
        listings_count = 0
        for user in users:
            query = select(Address).where(
                Address.is_primary.is_(True), Address.user_id == user.id
            )
            result_address = await session.execute(query)
            result_address: Address | None = result_address.scalars().one_or_none()
            if not result_address:
                raise Exception(
                    f"User <{user.id}> has no primary address. Exiting script."
                )

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
                    address_id=result_address.id,
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
    asyncio.run(seed_users_listings())
