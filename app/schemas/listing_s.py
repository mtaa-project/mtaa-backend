# from typing import Optional

# from sqlmodel import Field, SQLModel

# from app.models.enums.listing_status import ListingStatus
# from app.models.enums.offer_type import OfferType


# class ListingBaseV2(SQLModel):
#     listing_status: ListingStatus = Field(default=ListingStatus.ACTIVE)
#     offer_type: OfferType

#     seller_id: int = Field(foreign_key="users.id")
#     address_id: Optional[int] = Field(foreign_key="addresses.id", default=None)
