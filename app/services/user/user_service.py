from typing import List, Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.user_model import User
from app.services.user.exceptions import UserEmailNotFound, UserNotFound

AllowedUserDependencies = Literal[
    "reviews_written",
    "reviews_received",
    "search_alerts",
    "addresses",
    "favorite_listings",
    "posted_listings",
    "purchased_listings",
    "rented_listings",
]
DependenciesList = Optional[List[AllowedUserDependencies]]


class UserService:
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

    async def get_user_by_email(
        self, email: Optional[str] = None, dependencies: DependenciesList = None
    ) -> User:
        if not email:
            raise UserEmailNotFound("User email not found in metadata.")

        query = select(User).where(User.email == email)
        dependencies = dependencies or []
        if dependencies:
            query = query.options(
                *[selectinload(getattr(User, dep)) for dep in dependencies]
            )
        result = await self.session.execute(query)
        db_user = result.scalars().one_or_none()
        if not db_user:
            raise UserNotFound("User not found in the database.")

        return db_user

    async def get_user_by_id(
        self, user_id: int = None, dependencies: DependenciesList = None
    ) -> User:
        query = select(User).where(User.id == user_id)
        dependencies = dependencies or []
        if dependencies:
            query = query.options(
                *[selectinload(getattr(User, dep)) for dep in dependencies]
            )

        result = await self.session.execute(query)
        db_user = result.scalars().one_or_none()
        if not db_user:
            raise UserNotFound("User not found in the database.")

        return db_user

    async def get_current_user(self, dependencies: DependenciesList = None) -> User:
        """
        Retrieve the user using the email stored in the request state.
        You can optionally provide a list of relationships to be preloaded.
        """
        return await self.get_user_by_email(
            self.user_metadata.get("email"), dependencies=dependencies
        )

    async def get_seller_rating(self, seller_id: int) -> float | None:
        """
        Calculates the seller's rating based on received reviews.

        :param seller_id: The ID of the seller.
        :return: The average rating rounded to 2 decimal places or None if no reviews exist.
        :raises UserNotFound: If the seller is not found in the database.
        """
        seller: User | None = await self.get_user_by_id(
            seller_id, dependencies=["reviews_received"]
        )

        if len(seller.reviews_received) == 0:
            return None

        rating_total = sum(review.rating for review in seller.reviews_received)
        average_rating = round(rating_total / len(seller.reviews_received), 2)
        return average_rating

    @classmethod
    async def get_dependency(
        cls,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
    ) -> "UserService":
        return cls(session, request)
