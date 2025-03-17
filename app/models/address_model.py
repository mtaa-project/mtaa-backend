from typing import TYPE_CHECKING

from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from .user_model import User


class Address(SQLModel, table=True):
    __tablename__ = "addresses"

    id: int = Field(default=None, primary_key=True)
    is_primary: bool = Field(default=False)  # True = primary, False = secondary
    country: CountryAlpha2 = Field(max_length=2)
    city: str = Field(max_length=255)
    zip_code: str = Field(max_length=255)
    street: str = Field(max_length=255)
    visibility: bool = Field(
        default=True
    )  # True = visible, False = hidden / TODO: check with the team

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    # user has at least one address but can have multiple addresses
    # addresses: "User" = Relationship(back_populates="user")
