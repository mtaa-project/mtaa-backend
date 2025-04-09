from typing import Annotated

from fastapi import APIRouter, Depends
from phonenumbers import PhoneNumberFormat
from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.address_model import Address
from app.schemas.user_schema import (
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
)
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


@router.get("/profile")
async def get_profile(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    query_get_address = select(Address).where(
        Address.user_id == current_user.id, Address.is_primary == True
    )
    user_address = await session.execute(query_get_address)

    return user_address.scalars().one_or_none()


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
