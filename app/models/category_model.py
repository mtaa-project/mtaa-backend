from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .category_listing_model import CategoryListing

if TYPE_CHECKING:
    from .listing_model import Listing


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    # description: str = Field(max_length=255) TODO: check with the team
    listings: list["Listing"] = Relationship(
        back_populates="categories", link_model=CategoryListing
    )
