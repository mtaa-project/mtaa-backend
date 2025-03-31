from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship

from app.models.category_listing_model import CategoryListing
from app.models.favorite_listing_model import FavoriteListing
from app.models.rent_listing_model import RentListing
from app.models.sale_lisitng_model import SaleListing
from app.schemas.listing_schema import ListingBase  # shared base from schema

if TYPE_CHECKING:
    from .address_model import Address
    from .category_model import Category
    from .user_model import User


class Listing(ListingBase, table=True):
    __tablename__ = "listings"

    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("UTC")))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC")),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )

    # Foreign keys
    seller_id: int = Field(foreign_key="users.id")
    address_id: int | None = Field(default=None, foreign_key="addresses.id")

    # Relationships
    favorite_by: List["User"] = Relationship(
        back_populates="favorite_listings", link_model=FavoriteListing
    )
    address: Optional["Address"] = Relationship(back_populates="listings")
    categories: List["Category"] = Relationship(
        back_populates="listings", link_model=CategoryListing
    )
    seller: Optional["User"] = Relationship(back_populates="posted_listings")
    buyer: Optional["User"] = Relationship(
        back_populates="purchased_listings", link_model=SaleListing
    )
    renters: Optional["User"] = Relationship(
        back_populates="rented_listings", link_model=RentListing
    )
