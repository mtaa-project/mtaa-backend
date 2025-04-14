import math
from datetime import timedelta
from typing import List, Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from firebase_admin import storage
from pydantic_extra_types.coordinate import Latitude, Longitude
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.address_model import Address
from app.models.listing_image import ListingImage
from app.models.listing_model import Listing

AllowedListingDependencies = Literal[
    "favorite_by", "address", "categories", "seller", "buyer", "renters", "images"
]
DependenciesList = Optional[List[AllowedListingDependencies]]


def generate_signed_url(image_path: str) -> str:
    bucket = storage.bucket()
    blob = bucket.blob(image_path)
    signed_url = blob.generate_signed_url(
        version="v4", expiration=timedelta(seconds=20), method="GET"
    )
    return signed_url


class ListingService:
    def __init__(self, session: AsyncSession, request: Request) -> None:
        self.session = session
        self.request = request

        # getattr get attribute from class
        # if attribute does not exist it returns second parameter (None)
        self.user_metadata = getattr(request.state, "user", None)
        if not self.user_metadata:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated.",
            )

    async def get_listing_by_id(
        self,
        listing_id,
        dependencies: Optional[list[AllowedListingDependencies]] = None,
    ) -> Listing | None:
        query = select(Listing).where(Listing.id == listing_id)
        if dependencies:
            query = query.options(
                *[selectinload(getattr(Listing, dep)) for dep in dependencies]
            )

        result = await self.session.execute(query)
        return result.scalars().one_or_none()

    async def get_listings_by_seller_id(
        self,
        seller_id: int,
        dependencies: Optional[list[AllowedListingDependencies]] = None,
    ) -> list[Listing]:
        """
        Returns active listings posted by a seller with the given ID.

        :param seller_id: ID of the seller.
        :param dependencies: Optional list of relationships to eager load.
        :return: List of active listings.
        """
        query = select(Listing).where(
            Listing.seller_id == seller_id,
        )

        if dependencies:
            query = query.options(
                *[selectinload(getattr(Listing, dep)) for dep in dependencies]
            )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_current_user_listings(
        self,
        dependencies: Optional[list[AllowedListingDependencies]] = None,
    ) -> list[Listing]:
        """
        Returns active listings posted by the currently authenticated user.

        :param dependencies: Optional list of relationships to eager load.
        :return: List of active listings.
        :raises HTTPException: If user metadata does not contain an ID.
        """
        seller_id = self.user_metadata.get("id")
        if not seller_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current user ID not found in metadata.",
            )

        return await self.get_listings_by_seller_id(
            seller_id=seller_id, dependencies=dependencies
        )

    # generate presigned urls for listing images
    def get_presigned_urls(self, images: list[ListingImage]) -> list[str]:
        # TODO: implement error handling
        return [generate_signed_url(image.path) for image in images]

    def get_listing_distance_subquery(self, user_lat: float, user_lng: float):
        """
        Returns a subquery that computes the distance (in kilometers) from a provided
        (user_lat, user_lng) point to the listing's address using the haversine formula.
        It assumes that a Listing is associated with an Address having 'latitude' and 'longitude' fields.
        """
        # Haversine formula:
        # distance = 2 * R * asin(sqrt(
        #    sin^2((lat2 - lat1)/2) + cos(lat1) * cos(lat2) * sin^2((lng2 - lng1)/2)
        # ))
        #
        # where R is the earth's radius (we use 6371 km)
        distance_expr = (
            2
            * 6371
            * func.asin(
                func.sqrt(
                    func.pow(func.sin(func.radians(Address.latitude - user_lat) / 2), 2)
                    + func.cos(func.radians(user_lat))
                    * func.cos(func.radians(Address.latitude))
                    * func.pow(
                        func.sin(func.radians(Address.longitude - user_lng) / 2), 2
                    )
                )
            )
        ).label("distance")

        distance_subquery = (
            select(
                Listing.id.label("listing_id"),
                distance_expr,
            )
            .join(Address, Listing.address_id == Address.id)
            .subquery()
        )
        return distance_subquery

    def get_user_listing_distance(
        self,
        user_latitude: Latitude | None = None,
        user_longitude: Longitude | None = None,
        listing_latitude: Latitude | None = None,
        listing_longitude: Longitude | None = None,
    ) -> float:
        """
        Calculates the great-circle distance between two points on the Earth using the haversine formula.
        Returns the distance in kilometers.
        """
        # Convert decimal degrees to radians.
        user_latitude, user_longitude, listing_latitude, listing_longitude = map(
            math.radians,
            [user_latitude, user_longitude, listing_latitude, listing_longitude],
        )

        dlat = listing_latitude - user_latitude
        dlon = listing_longitude - user_longitude

        # Haversine formula
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(user_latitude)
            * math.cos(listing_latitude)
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        radius_km = 6371  # Earth's radius in kilometers
        return c * radius_km

    @classmethod
    async def get_dependency(
        cls,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
    ) -> "ListingService":
        return cls(session, request)
