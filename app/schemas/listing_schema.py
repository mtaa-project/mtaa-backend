from datetime import datetime
from decimal import Decimal

from sqlmodel import SQLModel

from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType


class ListingBase(SQLModel):
    title: str
    description: str
    price: Decimal
    listing_status: ListingStatus = ListingStatus.ACTIVE
    offer_type: OfferType
    category_ids: list[int] | None = None


class ListingCreate(ListingBase):
    seller_id: int
    address_id: int | None = None  # address visibility is handled in the address model


class ListingRead(ListingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    seller_id: int
    address_id: int | None = None


class ListingUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    visibility: bool = (
        True  # address visibility is used to set address visibility in address model
    )
    address_id: int | None = None
    category_ids: list[int] | None = None
