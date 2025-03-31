from datetime import datetime
from decimal import Decimal

from pydantic.alias_generators import to_camel
from sqlmodel import SQLModel

from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType


class ListingBase(SQLModel):
    title: str
    description: str
    price: Decimal
    listing_status: ListingStatus = ListingStatus.ACTIVE
    offer_type: OfferType
    visibility: bool = True


class ListingCreate(ListingBase):
    seller_id: int
    address_id: int | None = None


class ListingRead(ListingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    seller_id: int
    address_id: int | None = None
    categories: list[str] | None = None

    # Setup to use camelCase for frontend compatibility
    # TODO: check with @svato
    class Config:
        populate_by_name = True
        alias_generator = to_camel


class ListingUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    visibility: bool | None = None
    address_id: int | None = None
