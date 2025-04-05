from typing import Any, AsyncGenerator, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.user_model import User

from ..db.database import async_session

security = HTTPBearer()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_user(request: Request):
    # this is done by the middleware
    # if not hasattr(request.state, "user"):
    #     raise HTTPException(status_code=401, detail="User not authenticated.")
    return request.state.user


# async def get_user_db(
#     session: AsyncSession = Depends(get_async_session),
#     user: Any = Depends(get_user),
#     preload: List[str] | None = None,
# ) -> User:
#     email = user.get("email")
#     if not email:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated."
#         )

#     query = select(User).where(User.email == email)

#     # Preload related relationships if specified
#     if preload:
#         for relation in preload:
#             query = query.options(selectinload(getattr(User, relation)))

#     result = await session.execute(query)
#     db_user = result.scalars().one_or_none()

#     if not db_user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found in the database.",
#         )

#     return db_user


class GetUserDB:
    def __init__(self, preload: Optional[List[str]] = None):
        self.preload = preload or []

    async def __call__(
        self,
        session: AsyncSession = Depends(get_async_session),
        user: dict = Depends(get_user),
    ) -> User:
        email = user.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated.",
            )

        query = select(User).where(User.email == email)

        # Apply the specified relationships to preload
        for relation in self.preload:
            query = query.options(selectinload(getattr(User, relation)))

        result = await session.execute(query)
        db_user = result.scalars().one_or_none()

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in the database.",
            )

        return db_user
