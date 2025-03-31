from decimal import Decimal

from sqlmodel import SQLModel

from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType


# TODO: add field validators for ListingBase
# schema for listing
class ListingBase(SQLModel):
    title: str
    description: str
    price: Decimal
    listing_status: ListingStatus
    offer_type: OfferType


# schema for listing creation
class ListingCreate(ListingBase):
    address_id: int  # address visibility is handled in the address model
    category_ids: list[int]  # list of category ids
    visibility: bool  # address visibility is used to set address visibility in address model  # if true, address is visible to all users


# schema for listing view
# this is used to read listing data from the database
class ListingView(ListingBase):
    address_id: int
    category_ids: list[int]  # list of category ids
    visibility: bool


class ListingUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    address_id: int | None = None
    category_ids: list[int] | None = None
    visibility: bool | None = None
