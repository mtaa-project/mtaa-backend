from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, Relationship

from app.models.rent_listing_model import RentListing
from app.schemas.listing_schema import ListingBase
from app.schemas.transaction_schema import ListingTransactionBase

from .category_listing_model import CategoryListing
from .favorite_listing_model import FavoriteListing
from .sale_listing_model import SaleListing

if TYPE_CHECKING:
    from app.models.listing_image import ListingImage

    from .address_model import Address
    from .category_model import Category
    from .user_model import User


class Listing(ListingBase, ListingTransactionBase, table=True):
    __tablename__ = "listings"
    id: int = Field(default=None, primary_key=True)
    seller_id: int = Field(foreign_key="users.id")
    address_id: int = Field(foreign_key="addresses.id")

    images: List["ListingImage"] = Relationship(back_populates="listing")

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

    # Relationships
    favorite_by: List["User"] = Relationship(
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
