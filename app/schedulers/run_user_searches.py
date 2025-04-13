from datetime import UTC, datetime, timedelta
from typing import List

from firebase_admin import messaging
from sqlalchemy import Integer, and_, cast, select

from app.db.database import async_session
from app.models import Listing, UserSearchAlert


async def notify_user_search_alerts():
    async with async_session() as session:
        now = datetime.now(UTC)
        time_limits = now - timedelta(hours=2)
        # Fetch user search alerts that haven't been notified in the last 2 hours
        result = await session.execute(
            select(UserSearchAlert).where(
                UserSearchAlert.last_notified_at < time_limits,
                UserSearchAlert.is_active == True,
            )
        )
        search_alerts: List[UserSearchAlert] = result.scalars().all()

        for s_alert in search_alerts:
            # Build the query to find new listings that match the search alert
            query = select(Listing)
            conditions = []

            for key, value in s_alert.product_filters.items():
                if isinstance(value, int):
                    condition = cast(Listing.attributes[key].astext, Integer) == value
                else:
                    condition = Listing.attributes[key].astext == str(value)
                conditions.append(condition)

            if conditions:
                query = query.where(and_(*conditions))

            # Execute the query to find matching listings
            result = await session.execute(query)
            listings: List[Listing] = result.scalars().all()
            if listings:
                # Send notification to the user
                for token in s_alert.user.firebase_cloud_tokens:
                    try:
                        # Send a notification using Firebase Cloud Messaging
                        message = messaging.Message(
                            notification=messaging.Notification(
                                title="New Listings Alert",
                                body=f"New listings matching your search alert: {len(listings)} new listings found.",
                            ),
                            token=token.token,
                            data={
                                "listings": [
                                    # TODO: Serialize listings to a suitable format
                                ],  # Send listings data
                            },
                            android=messaging.AndroidConfig(
                                priority="high",
                                notification=messaging.AndroidNotification(
                                    channel_id="high-priority-alerts",
                                    sound="default",
                                ),
                            ),
                        )
                        response = await messaging.send(message)
                        print(f"Successfully sent message: {response}")
                    except Exception as e:
                        print(f"Error sending message: {e}")

                # Update the last notified time
                s_alert.last_notified_at = now

        await session.commit()
