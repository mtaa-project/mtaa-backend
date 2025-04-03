from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlmodel import SQLModel

from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType


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


# schema for listing view
# this is used to read listing data from the database
class ListingView(ListingBase):
    address: Address
    categories: list["Category"]  # list of category ids


# schema for listing update
class ListingUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    address_id: int | None = None
    category_ids: list[int] | None = None


class getParameters(SQLModel):
    limit: int = 10
    offset: int = 0
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    category_ids: List[int] | None = None
    min_price: int | None = None
    max_price: int | None = None
