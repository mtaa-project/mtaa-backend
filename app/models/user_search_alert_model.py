from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_model import User


class UserSearchAlert(SQLModel, table=True):
    __tablename__ = "userSearchAlerts"

    id: int = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    product_filters: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_notified_at: datetime | None = Field(
        default=None
    )  # Used to track the last time the user was notified about new listings that match their search alert.

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")

    # Relationships
    user: "User" = Relationship(back_populates="search_alerts")
