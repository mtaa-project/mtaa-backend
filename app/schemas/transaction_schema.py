from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field

from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType

if TYPE_CHECKING:
    from app.models.address_model import Address
    from app.models.category_model import Category


class ListingTransactionBase(BaseModel):
    title: str = Field(max_length=255)
    description: str = Field(max_length=255)
    price: Decimal = Field(max_digits=10, decimal_places=2)


# # Basic schema for listing data
# class ListingBase(SQLModel, ListingTransactionBase):
#     listing_status: ListingStatus
#     offer_type: OfferType
