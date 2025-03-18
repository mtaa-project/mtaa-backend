from sqlmodel import Field, Relationship, SQLModel

from .category_listing_model import CategoryListing
from .listing_model import Listing


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    # description: str = Field(max_length=255) TODO: check with the team
    # TODO: define relationship between Category and Listing (Many-to-Many)
    listings: list["Listing"] = Relationship(
        back_populates="categories", link_model=CategoryListing
    )
