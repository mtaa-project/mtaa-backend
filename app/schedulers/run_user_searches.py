import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import List

from firebase_admin import exceptions, messaging
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import selectinload

from app.db.database import async_session
from app.models import Listing, UserSearchAlert
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.user_model import User
from app.services.user.user_service import UserService


async def notify_user_search_alerts():
    async with async_session() as session:
        now = datetime.now(UTC)
        time_limits = now - timedelta(minutes=1)
        # Fetch user search alerts that haven't been notified in the last 2 hours
        result = await session.execute(
            select(UserSearchAlert)
            .options(
                selectinload(UserSearchAlert.user).selectinload(
                    User.firebase_cloud_tokens
                )
            )
            .where(
                UserSearchAlert.last_notified_at < time_limits,
                UserSearchAlert.is_active == True,
            )
        )
        search_alerts: List[UserSearchAlert] = result.scalars().all()

        for s_alert in search_alerts:
            if not s_alert.is_active:
                s_alert.last_notified_at = now
                continue
            # Build the query to find new listings that match the search alert
            rating_subquery = UserService.get_seller_rating_subquery()
            rating_val = func.coalesce(rating_subquery.c.avg_rating, 0).label(
                "seller_rating"
            )

            query = (
                select(Listing, rating_val)
                .outerjoin(
                    rating_subquery,
                    rating_subquery.c.seller_id == Listing.seller_id,
                )
                .options(
                    selectinload(Listing.address),
                    selectinload(Listing.categories),
                    selectinload(Listing.seller),
                )
                .where(
                    Listing.listing_status == ListingStatus.ACTIVE,
                    func.date_trunc("second", Listing.created_at)
                    >= func.date_trunc(
                        "second", s_alert.last_notified_at
                    ),  # Listing created after last notified time
                )
            )

            # Iterate over each key in product_filters and build a condition based on the key name
            for key, value in s_alert.product_filters.items():
                if key == "category_ids":
                    # Filter listings that have at least one category with the given IDs.
                    if isinstance(value, list) and value:
                        query = query.where(
                            Listing.categories.any(Category.id.in_(value))
                        )
                elif key == "offer_type":
                    query = query.where(Listing.offer_type == value)
                elif key == "listing_status":
                    query = query.where(Listing.listing_status == value)
                elif key == "min_price":
                    query = query.where(Listing.price >= value)
                elif key == "max_price":
                    query = query.where(Listing.price <= value)
                elif key == "search":
                    # Assuming Listing has title and description fields
                    query = query.where(
                        or_(
                            Listing.title.ilike(f"%{value}%"),
                            Listing.description.ilike(f"%{value}%"),
                        )
                    )

                elif key == "min_rating":
                    query = query.where(rating_val >= value)
                elif key == "country":
                    query = query.where(Listing.address.has(Address.country == value))
                elif key == "city":
                    query = query.where(Listing.address.has(Address.city == value))
                elif key == "street":
                    query = query.where(Listing.address.has(Address.street == value))

                # Sorting:
                sort_columns = {
                    "created_at": Listing.created_at,
                    "updated_at": Listing.updated_at,
                    "price": Listing.price,
                    "rating": rating_val,
                }
                if key == "sort_by":
                    if value == "asc":
                        query = query.order_by(
                            asc(sort_columns.get(value, Listing.updated_at))
                        )
                    elif value == "desc":
                        query = query.order_by(
                            desc(sort_columns.get(value, Listing.updated_at))
                        )

            # Execute the query to find matching listings
            result = await session.execute(query)
            listings: List[Listing] = result.scalars().all()
            print("----------------------------------")
            print(f"Found {len(listings)} listings matching the search alert.")
            print(f"Search Alert ID: {s_alert.id}")
            print(f"Search Alert Filters: {s_alert.product_filters}")
            print(listings)
            print("----------------------------------")

            if listings:
                # Generate a URL for the listings
                base_url = "mtaa-frotnend://home"
                # query_string = urllib.parse.urlencode(
                #     s_alert.product_filters, doseq=True
                # )
                # Add time filters to the query string
                # query_string += f"&time_from={s_alert.last_notified_at.isoformat()}"
                # deep_link_url = f"{base_url}/listings?{query_string}"
                deep_link_url = base_url
                # deep_link_url = base_url + "/home"
                print(f"URL: {deep_link_url}")

                token_strings = [
                    t.token
                    for t in s_alert.user.firebase_cloud_tokens
                    if isinstance(t.token, str) and t.token
                ]
                messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        channel_id="default",
                        sound="default",
                    ),
                )
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title="New Listings Alert",
                        body=f"{len(listings)} new listings match your search criteria. Tap to view details.",
                    ),
                    data={
                        "deep_link": deep_link_url,
                        # "offer_type": s_alert.product_filters.get(
                        #     "offer_type", "Unknown offer type"
                        # ),
                    },
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="high-priority-alerts",
                            sound="default",
                        ),
                    ),
                    tokens=token_strings,
                )
                try:
                    # https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging
                    response = messaging.send_each_for_multicast(message)
                    print(
                        f"Successfully sent multicast: {response.success_count} messages"
                    )
                    s_alert.last_notified_at = now
                except exceptions.FirebaseError as firebase_error:
                    print(f"Error sending to FCM: {firebase_error}")
                # Update the last notified time
                except ValueError as value_error:
                    print("Invalid message parameters: ", value_error)

        await session.commit()
