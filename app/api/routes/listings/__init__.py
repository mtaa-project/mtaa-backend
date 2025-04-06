from fastapi import APIRouter

from .base import router as crud_router
from .favorites import router as favorites_router

router = APIRouter(prefix="/listings", tags=["Listings"])
router.include_router(
    crud_router,
)
router.include_router(
    favorites_router,
)
