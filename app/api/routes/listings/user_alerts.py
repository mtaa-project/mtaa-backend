from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.user_search_alert_model import UserSearchAlert
from app.schemas.listing_schema import AlertQuery
from app.services.user.user_service import UserService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post(
    "/",
    response_model=UserSearchAlert,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
    description="Creates a new alert for the current user. The alert will be triggered when a new listing matches the specified criteria.",
)
async def create_alert(
    *,
    new_alert_data: AlertQuery,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that listing status is not removed or sold
    if new_alert_data.listing_status in [
        ListingStatus.REMOVED,
        ListingStatus.SOLD,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing status cannot be REMOVED or SOLD when alerting for a listing.",
        )

    # check that categories exist
    if new_alert_data.category_ids is not None:
        for category_id in new_alert_data.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )

    # check that sort_by is valid
    if new_alert_data.sort_by not in ["created_at", "updated_at", "price", "rating"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_by parameter. Allowed values are: created_at, updated_at, price, rating.",
        )

    # create the alert and add it to the session (type JSONB)
    product_filters = new_alert_data.model_dump(exclude_unset=True)

    alert = UserSearchAlert(
        user_id=current_user.id,
        product_filters=product_filters,
        is_active=True,
    )

    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return alert


@router.get(
    "/my-alerts",
    response_model=List[UserSearchAlert],
    summary="Get current user's alerts",
    description="Fetch all alerts created by the current user.",
)
async def get_my_alerts(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # return only posted listings that are not removed
    result = await session.execute(
        select(UserSearchAlert).where(
            UserSearchAlert.user_id == current_user.id,
            UserSearchAlert.is_active == True,
        )
    )

    alerts: list[UserSearchAlert] = result.scalars().all()

    return alerts


# enable alert
@router.put(
    "/{alert_id}/enable",
    response_model=UserSearchAlert,
    summary="Enable an alert",
    description="Enable an alert by ID. The alert will be triggered when a new listing matches the specified criteria.",
)
async def enable_alert(
    *,
    alert_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that alert exists
    alert = await session.get(UserSearchAlert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found.",
        )

    # check that user is logged in and is the owner of the alert
    if current_user.id != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to enable this alert.",
        )

    # enable the alert
    alert.is_active = True
    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return alert


# disable alert
@router.put(
    "/{alert_id}/disable",
    response_model=UserSearchAlert,
    summary="Disable an alert",
    description="Disable an alert by ID. The alert will no longer be triggered.",
)
async def disable_alert(
    *,
    alert_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that alert exists
    alert = await session.get(UserSearchAlert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found.",
        )

    # check that user is logged in and is the owner of the alert
    if current_user.id != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to disable this alert.",
        )

    # disable the alert
    alert.is_active = False
    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    return alert


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert",
    description="Delete an alert by ID. The alert will no longer be triggered and will be removed from database.",
)
async def delete_alert(
    *,
    alert_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that alert exists
    alert = await session.get(UserSearchAlert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found.",
        )

    # check that user is logged in and is the owner of the alert
    if current_user.id != alert.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this alert.",
        )

    # remove alert from db
    await session.delete(alert)
    await session.commit()
