from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field


class ListingTransactionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(max_length=255)
    description: str = Field(max_length=5000)
    price: Decimal = Field(max_digits=10, decimal_places=2, ge=0)


# # Basic schema for listing data
# class ListingBase(SQLModel, ListingTransactionBase):
#     listing_status: ListingStatus
#     offer_type: OfferType
