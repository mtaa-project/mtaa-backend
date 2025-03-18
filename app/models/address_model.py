from typing import TYPE_CHECKING

from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .listing_model import Listing
    from .user_model import User


class Address(SQLModel, table=True):
    __tablename__ = "addresses"

    id: int = Field(default=None, primary_key=True)
    is_primary: bool = Field(default=False)  # True = primary, False = secondary
    visibility: bool = Field(default=True)  # True = visible, False = hidden
    country: CountryAlpha2 | None = Field(max_length=2)
    city: str | None = Field(max_length=255)
    zip_code: str | None = Field(max_length=255)
    street: str | None = Field(max_length=255)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    users: "User" = Relationship(back_populates="addresses")
    listings: list["Listing"] = Relationship(back_populates="address")
