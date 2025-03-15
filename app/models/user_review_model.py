from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_model import User


class UserReview(SQLModel, table=True):
    __tablename__ = "userReviews"

    id: int = Field(default=None, primary_key=True)

    text: str = Field(max_length=500)
    rating: int = Field(ge=1, le=5)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None

    # Foreign keys
    reviewer_id: int = Field(foreign_key="users.id", nullable=False)
    reviewee_id: int = Field(foreign_key="users.id", nullable=False)

    # Relationships
    reviewer: Optional["User"] = Relationship(
        back_populates="reviews_written",
        sa_relationship_kwargs={"primaryjoin": "UserReview.reviewer_id == User.id"},
    )
    reviewee: Optional["User"] = Relationship(
        back_populates="reviews_received",
        sa_relationship_kwargs={"primaryjoin": "UserReview.reviewee_id == User.id"},
    )
