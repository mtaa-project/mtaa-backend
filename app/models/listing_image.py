from sqlmodel import Field, Relationship, SQLModel

from app.models.listing_model import Listing
from app.models.user_model import User


class ListingImageBase(SQLModel):
    path: str


class ListingImage(ListingImageBase, table=True):
    __tablename__ = "listing_images"

    id: int = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listings.id")

    listing: Listing = Relationship(back_populates="images")
