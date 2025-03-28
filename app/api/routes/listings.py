from api.dependencies import get_async_session
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/listings")


@router.post("/")
async def create_post(
    *,
    session: AsyncSession = Depends(get_async_session),
):
    pass
