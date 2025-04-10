from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from phonenumbers import PhoneNumberFormat
from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.address_model import Address
from app.models.enums.listing_status import ListingStatus
from app.models.listing_model import Listing
from app.models.sale_lisitng_model import SaleListing
from app.schemas.user_schema import (
    ProfileUser,
    UserGet,
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
)
from app.services.user.exceptions import UserNotFound
from app.services.user.user_service import UserService

router = APIRouter(tags=["Profile"])


class UserMetadata(BaseModel):
    firstname: str | None = Field(default=None, min_length=1, max_length=255)
    lastname: str | None = Field(default=None, min_length=1, max_length=255)
    phone: Annotated[
        PhoneNumber | None,
        PhoneNumberValidator(
            default_region=None, number_format="E164", supported_regions=None
        ),
    ]
    address_visibility: bool | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "firstname": "Alice",
                "lastname": "Smith",
                "phone": "+421912345678",
                "address_visibility": True,
            }
        }
    }


@router.get("/profile", response_model=ProfileUser)
async def get_profile(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user(
        dependencies=["addresses", "purchased_listings", "rented_listings"]
    )

    user_rating = await user_service.get_seller_rating(current_user.id)
    user_address = await session.execute(
        select(Address).where(
            Address.user_id == current_user.id, Address.is_primary == True
        )
    )

    sold_listings = await user_service.get_sold_listings(current_user.id)
    user_address = user_address.scalars().one_or_none()

    return ProfileUser(
        firstname=current_user.firstname,
        lastname=current_user.lastname,
        phone_number=current_user.phone_number,
        rating=user_rating,
        amount_rent_listing=len(current_user.rented_listings),
        amount_sold_listing=len(sold_listings),
        address=user_address,
    )


@router.put("/", response_model=UserProfileUpdateResponse)
async def update_profile(
    *,
    update_data: UserProfileUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    user_data = update_data.user_metadata.model_dump(exclude_none=True)
    address_data = update_data.address_metadata.model_dump(exclude_none=True)

    current_user = await user_service.get_current_user()

    async with session.begin():
        user_address = await session.execute(
            select(Address).where(
                Address.user_id == current_user.id, Address.is_primary == True
            )
        )
        db_address = user_address.scalars().one_or_none()
        # create user address
        if db_address is None:
            address_data["is_primary"] = True
            address_data["user_id"] = current_user.id
            db_address = Address.model_validate(address_data)
        # update user address
        else:
            db_address.sqlmodel_update(address_data)

        db_user = current_user.sqlmodel_update(user_data)
        session.add_all([db_address, db_user])

    await session.commit()
    await session.refresh(db_address)
    await session.refresh(db_user)
    print(f"userdata: {db_user.firstname}")
    return UserProfileUpdateResponse(user_metadata=db_user, address_metadata=db_address)


@router.get("/profile/{id}", response_model=ProfileUser)
async def get_profile(
    *,
    id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    try:
        user = await user_service.get_user_by_id(
            id, dependencies=["addresses", "purchased_listings", "rented_listings"]
        )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user profile does not exist.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not get user.",
        )

    user_rating = await user_service.get_seller_rating(user.id)
    user_address = await session.execute(
        select(Address).where(Address.user_id == user.id, Address.is_primary == True)
    )

    sold_listings = await user_service.get_sold_listings(user.id)
    user_address = user_address.scalars().one_or_none()

    return ProfileUser(
        firstname=user.firstname,
        lastname=user.lastname,
        phone_number=user.phone_number,
        rating=user_rating,
        amount_rent_listing=len(user.rented_listings),
        amount_sold_listing=len(sold_listings),
        address=user_address,
    )
