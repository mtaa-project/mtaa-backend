from typing import List, Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.user_model import User

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
        # returns email or None
        email = email or self.user_metadata.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found in metadata.",
            )

        query = select(User).where(User.email == email)
        dependencies = dependencies or []
        if dependencies:
            query = query.options(
                *[selectinload(getattr(User, dep)) for dep in dependencies]
            )
        result = await self.session.execute(query)
        db_user = result.scalars().one_or_none()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in the database.",
            )
        return db_user

    async def get_user(self, dependencies: DependenciesList = None) -> User:
        """
        Retrieve the user using the email stored in the request state.
        You can optionally provide a list of relationships to be preloaded.
        """
        return await self.get_user_by_email(dependencies=dependencies)

    @classmethod
    async def get_dependency(
        cls,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
    ) -> "UserService":
        return cls(session, request)
