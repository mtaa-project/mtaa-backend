from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.listing_model import Listing
from app.models.user_model import User

AllowedListingDependencies = Literal[
    "favorite_by",
    "address",
    "categories",
    "seller",
    "buyer",
    "renters",
]
DependenciesList = Optional[list[AllowedListingDependencies]]


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
                *[(getattr(Listing, dependency)) for dependency in dependencies]
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

    @classmethod
    async def get_dependency(
        cls,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
    ) -> "ListingService":
        return cls(session, request)
