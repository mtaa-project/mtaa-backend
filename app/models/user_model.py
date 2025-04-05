from typing import TYPE_CHECKING, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from .favorite_listing_model import FavoriteListing
from .rent_listing_model import RentListing
from .sale_lisitng_model import SaleListing

if TYPE_CHECKING:
    from listing_model import Listing

    from app.models.address_model import Address

    from .user_review_model import UserReview
    from .user_search_alert_model import UserSearchAlert


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)

    firstname: str = Field(min_length=1, max_length=255)
    lastname: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, max_length=255)
    phone_number: str | None = Field(default=None, max_length=255)

    # Relationships
    reviews_written: List["UserReview"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "[UserReview.reviewer_id]"},
    )

    reviews_received: List["UserReview"] = Relationship(
        back_populates="reviewee",
        sa_relationship_kwargs={"foreign_keys": "UserReview.reviewee_id"},
    )

    search_alerts: List["UserSearchAlert"] = Relationship(
        back_populates="user",
        # This configures SQLModel to automatically delete the related
        # records (UserSearchAlert) when the initial one is deleted (a User).
        cascade_delete=True,
    )

    addresses: List["Address"] = Relationship(
        back_populates="users",
    )

    favorite_listings: list["Listing"] = Relationship(
        back_populates="favorite_by", link_model=FavoriteListing
    )

    posted_listings: list["Listing"] = Relationship(back_populates="seller")

    purchased_listings: list["Listing"] = Relationship(
        back_populates="buyer", link_model=SaleListing
    )

    rented_listings: list["Listing"] = Relationship(
        back_populates="renters", link_model=RentListing
    )
