from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.category_model import Category

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[Category])
async def get_categories(
    *,
    session: AsyncSession = Depends(get_async_session),
):
    response = await session.execute(select(Category))
    return response.scalars().all()
