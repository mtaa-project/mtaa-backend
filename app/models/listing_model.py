from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, Relationship, SQLModel

from app.models.rent_listing_model import RentListing

from .category_listing_model import CategoryListing
from .enums.listing_status import ListingStatus
from .enums.offer_type import OfferType
from .favorite_listing_model import FavoriteListing
from .sale_lisitng_model import SaleListing

if TYPE_CHECKING:
    from .address_model import Address
    from .category_model import Category
    from .user_model import User


class Listing(SQLModel, table=True):
    __tablename__ = "listings"

    id: int = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    description: str = Field(max_length=255)
    price: Decimal = Field(max_digits=10, decimal_places=2)
    listing_status: ListingStatus = Field(default=ListingStatus.ACTIVE)
    offer_type: OfferType
    # visibility: bool = Field(default=True)  # True = visible, False = hidden
    # visibility is handled in the listing status as HIDDEN
    # address visibility is handled in the address model
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
    # Foreign keys
    seller_id: int = Field(foreign_key="users.id")
    address_id: int | None = Field(foreign_key="addresses.id")

    # Relationships
    favorite_by: list["User"] = Relationship(
        back_populates="favorite_listings", link_model=FavoriteListing
    )

    address: "Address" = Relationship(back_populates="listings")

    categories: List["Category"] = Relationship(
        back_populates="listings", link_model=CategoryListing
    )

    seller: Optional["User"] = Relationship(back_populates="posted_listings")

    buyer: Optional["User"] | None = Relationship(
        back_populates="purchased_listings", link_model=SaleListing
    )

    renters: Optional["User"] = Relationship(
        back_populates="rented_listings", link_model=RentListing
    )
