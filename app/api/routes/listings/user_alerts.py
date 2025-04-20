from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import desc, select

from app.api.dependencies import get_async_session
from app.models.category_model import Category
from app.models.firebase_cloud_token_model import FirebaseCloudToken
from app.models.user_search_alert_model import UserSearchAlert
from app.schemas.listing_schema import AlertQuery, AlertQueryCreate
from app.schemas.user_search_alerts import (
    Categories,
    UserSearchAlertDetail,
    UserSearchAlertGet,
)
from app.services.user.user_service import UserService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "/my-alerts",
    response_model=list[UserSearchAlertGet],
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
        select(UserSearchAlert)
        .where(
            UserSearchAlert.user_id == current_user.id,
            # UserSearchAlert.is_active == True,
        )
        .order_by(desc(UserSearchAlert.id))  # zoradenie zostupne
    )

    alerts: list[UserSearchAlert] = result.scalars().all()
    print(alerts)
    return [
        UserSearchAlertGet(
            id=current_search_term.id,
            search=current_search_term.product_filters["search"],
            is_active=current_search_term.is_active,
        )
        for current_search_term in alerts
    ]


@router.get(
    "/my-alerts/{id}",
    response_model=UserSearchAlertDetail,
    summary="Get current user's alert by ID",
    description="Fetch alert created by the current user.",
)
async def get_my_alert(
    *,
    id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()
    alert_response = await session.execute(
        select(UserSearchAlert).where(
            UserSearchAlert.user_id == current_user.id,
            UserSearchAlert.id == id,
        )
    )

    # verify alert existence
    alert_response = alert_response.scalar_one_or_none()
    if alert_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f'Alert not "{id}" found.'
        )

    # select selected categories
    selectedCategoryIds = alert_response.product_filters.get("category_ids", [])
    if len(selectedCategoryIds) > 0:
        categories = (
            await session.scalars(
                select(Category).where(Category.id.in_(selectedCategoryIds))
            )
        ).all()
    else:
        categories = []

    # select not selected categories

    return UserSearchAlertDetail(
        id=alert_response.id,
        is_active=alert_response.is_active,
        search=alert_response.product_filters["search"],
        categoryIds=selectedCategoryIds,
        offer_type=alert_response.product_filters["offer_type"],
        price_range_rent=alert_response.product_filters.get("price_range_rent"),
        price_range_sale=alert_response.product_filters.get("price_range_sale"),
    )


@router.put(
    "/my-alerts/{alert_id}",
    response_model=UserSearchAlertDetail,
    summary="Update an existing alert",
    description="Update only the provided fields of an existing alert.",
)
async def update_alert(
    *,
    alert_id: int,
    updated: AlertQuery,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    alert = await session.get(UserSearchAlert, alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found.",
        )

    # re-validate categories if provided
    if updated.category_ids is not None:
        for cid in updated.category_ids:
            cat = await session.get(Category, cid)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {cid} not found.",
                )

    # re-validate sort_by if provided
    if updated.sort_by is not None and updated.sort_by not in {
        "created_at",
        "updated_at",
        "price",
        "rating",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sort_by parameter. Allowed: created_at, updated_at, price, rating.",
        )

    # Merge only the fields client actually sent
    incoming = updated.model_dump(exclude_unset=True)
    new_filters = {**alert.product_filters, **incoming}
    alert.product_filters = new_filters

    session.add(alert)
    await session.commit()
    await session.refresh(alert)

    # Build same detail DTO as GET /my‐alerts/{id}
    selected_ids = alert.product_filters.get("category_ids", [])
    return UserSearchAlertDetail(
        id=alert.id,
        is_active=alert.is_active,
        search=alert.product_filters["search"],
        categoryIds=selected_ids,
        offer_type=alert.product_filters.get("offer_type"),
        # if your Detail schema includes nested categories,
        # you can load them here exactly like your GET handler.
    )


@router.post(
    "/",
    response_model=UserSearchAlert,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
    description="Creates a new alert for the current user. The alert will be triggered when a new listing matches the specified criteria.",
)
async def create_alert(
    *,
    new_alert_data: AlertQueryCreate,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user(
        dependencies=["firebase_cloud_tokens"]
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
        # is_active=True,
    )

    new_token = True
    for token in current_user.firebase_cloud_tokens:
        if token == new_alert_data.device_push_token:
            new_token = False
            break

    # Register new FCM device token
    if new_token:
        print(f"Token: {new_alert_data.device_push_token} is already registered.")

        current_user.firebase_cloud_tokens.append(
            FirebaseCloudToken(token=new_alert_data.device_push_token)
        )
    else:
        print(f"Registering new device token: {new_alert_data.device_push_token}.")

    session.add_all([current_user, alert])
    await session.commit()
    await session.refresh(alert)

    return alert


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
