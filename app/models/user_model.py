from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.schemas.user_schema import UserBase

from app.models.firebase_cloud_token_model import FirebaseCloudToken

from .favorite_listing_model import FavoriteListing
from .rent_listing_model import RentListing
from .sale_listing_model import SaleListing

if TYPE_CHECKING:
    from listing_model import Listing

    from app.models.address_model import Address

    from .user_review_model import UserReview
    from .user_search_alert_model import UserSearchAlert


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)

    # Relationships
    addresses: List["Address"] = Relationship(
        back_populates="users",
    )

    reviews_written: List["UserReview"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "[UserReview.reviewer_id]"},
    )

    reviews_received: List["UserReview"] = Relationship(
        back_populates="reviewee",
        sa_relationship_kwargs={"foreign_keys": "UserReview.reviewee_id"},
    )

    firebase_cloud_tokens: List["FirebaseCloudToken"] = Relationship(
        back_populates="user"
    )

    search_alerts: List["UserSearchAlert"] = Relationship(
        back_populates="user",
        # This configures SQLModel to automatically delete the related
        # records (UserSearchAlert) when the initial one is deleted (a User).
        cascade_delete=True,
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
