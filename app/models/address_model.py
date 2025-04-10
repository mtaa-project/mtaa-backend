from typing import TYPE_CHECKING

from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field, Relationship, SQLModel

from app.schemas.address_schema import AddressBase

if TYPE_CHECKING:
    from .listing_model import Listing
    from .user_model import User


class Address(AddressBase, table=True):
    __tablename__ = "addresses"

    id: int = Field(default=None, primary_key=True)
    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    users: "User" = Relationship(back_populates="addresses")
    listings: list["Listing"] = Relationship(back_populates="address")
