from datetime import UTC, datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel

from .enums.listing_status import ListingStatus
from .enums.offer_type import OfferType

# if TYPE_CHECKING:
#     from .user_model import User


class Listing(SQLModel, table=True):
    __tablename__ = "listings"

    id: int = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, unique=True)
    description: str = Field(max_length=255)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    listing_status: ListingStatus = Field(default=ListingStatus.ACTIVE)
    offer_type: OfferType
    visibility: bool = Field(default=True)  # True = visible, False = hidden
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    # Foreign keys
    seller_id: int = Field(foreign_key="users.id")
    buyer_id: int | None = Field(foreign_key="users.id")
    address_id: int | None = Field(foreign_key="addresses.id")

    # Relationships
    # user has at least one address but can have multiple addresses
    # addresses: "User" = Relationship(back_populates="user")
