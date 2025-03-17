from typing import TYPE_CHECKING, List, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.address_model import Address

    from .user_review_model import UserReview
    from .user_search_alert_model import UserSearchAlert


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    firstname: str = Field(min_length=1, max_length=255)
    lastname: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=255)

    # Relationships
    reviews_written: List["UserReview"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "[UserReview.reviewer_id]"},
        default_factory=list,
    )

    reviews_received: List["UserReview"] = Relationship(
        back_populates="reviewee",
        sa_relationship_kwargs={"foreign_keys": "[UserReview.reviewee_id]"},
        default_factory=list,
    )

    search_alerts: List["UserSearchAlert"] = Relationship(
        back_populates="alerts",
        default_factory=list,
        # This configures SQLModel to automatically delete the related
        # records (UserSearchAlert) when the initial one is deleted (a User).
        cascade_delete=True,
    )

    addresses: List["Address"] = Relationship(
        back_populates="users", default_factory=list
    )
