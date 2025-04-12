from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import relationship as sa_relationship
from sqlmodel import Field, Relationship

from app.schemas.address_schema import AddressBase

if TYPE_CHECKING:
    from app.models.rent_listing_model import RentListing
    from app.models.sale_listing_model import SaleListing

    from .listing_model import Listing
    from .user_model import User


class Address(AddressBase, table=True):
    __tablename__ = "addresses"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    users: "User" = Relationship(back_populates="addresses")
    sale: List["Listing"] = Relationship(back_populates="address")
    listings: List["Listing"] = Relationship(back_populates="address")

    sold_listings: List["SaleListing"] = Relationship(
        back_populates="address",
        sa_relationship_kwargs={"foreign_keys": "[SaleListing.address_id]"},
    )
    rented_listings: List["RentListing"] = Relationship(
        back_populates="address",
        sa_relationship_kwargs={"foreign_keys": "[RentListing.address_id]"},
    )
