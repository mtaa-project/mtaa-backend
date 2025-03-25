from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session, get_user
from app.models.user_model import User

router = APIRouter(prefix="/users", tags=["users"])


# Example Route
@router.get("/")
async def get_users(
    *, session: AsyncSession = Depends(get_async_session), user=Depends(get_user)
):
    db_user = await session.execute(select(User))
    db_user = db_user.scalars().all()
    return db_user
