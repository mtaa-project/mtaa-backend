import asyncio
import random
from decimal import Decimal

from faker import Faker
from sqlmodel import select

from app.db.database import async_session
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.models.listing_model import Listing
from app.models.rent_listing_model import RentListing
from app.models.sale_listing_model import SaleListing
from app.models.user_model import User

fake = Faker()

NUM_USERS = 10
MAX_REVIEWS_PER_USER = 3
LISTINGS_PER_USER = 20


async def seed_users_listings():
    async with async_session() as session:
        result = await session.execute(select(User))
        users: list[User] = result.scalars().all()

        result = await session.execute(select(Category))
        categories: list[Category] = result.scalars().all()
        if not categories:
            print("No categories found. Run the category seeder first.")
            return

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
                offer_type = random.choice(list(OfferType))
                listing_status = random.choice(list(ListingStatus))

                listing = Listing(
                    title=fake.sentence(nb_words=6),
                    description=fake.paragraph(nb_sentences=3),
                    price=Decimal(f"{random.uniform(10, 1000):.2f}"),
                    offer_type=offer_type,
                    seller_id=user.id,
                    address_id=result_address.id,
                    listing_status=listing_status,
                )
                session.add(listing)
                await session.flush()

                random_category = random.choice(categories)
                # listing.categories = [random_category]

                if listing_status == ListingStatus.SOLD:
                    buyer = random.choice(users)
                    sale_entry = SaleListing(
                        listing_id=listing.id,
                        buyer_id=buyer.id,
                        title=listing.title,
                        description=listing.description,
                        price=listing.price,
                        address_id=result_address.id,
                    )
                    session.add(sale_entry)

                if listing_status == ListingStatus.RENTED:
                    renter = random.choice(users)
                    rent_entry = RentListing(
                        listing_id=listing.id,
                        buyer_id=renter.id,
                        title=listing.title,
                        description=listing.description,
                        price=listing.price,
                        address_id=result_address.id,
                    )
                    session.add(rent_entry)

                listings_count += 1

        await session.commit()
        print(
            f"Seeded {listings_count} listings (approx. {LISTINGS_PER_USER} per user)"
        )


if __name__ == "__main__":
    asyncio.run(seed_users_listings())
