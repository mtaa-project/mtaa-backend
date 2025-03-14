from typing import TYPE_CHECKING, List, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
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
    )
    reviews_received: List["UserReview"] = Relationship(
        back_populates="reviewee",
        sa_relationship_kwargs={"foreign_keys": "[UserReview.reviewee_id]"},
    )

    search_alerts: List["UserSearchAlert"] = Relationship(
        back_populates="alerts", cascade_delete=True
    )
