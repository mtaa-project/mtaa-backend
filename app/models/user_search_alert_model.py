from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Column
from sqlmodel import Field, Relationship

from app.schemas.user_search_alerts import UserSearchAlertBase

if TYPE_CHECKING:
    from .user_model import User


class UserSearchAlert(UserSearchAlertBase, table=True):
    __tablename__ = "userSearchAlerts"

    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    last_notified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )  # Used to track the last time the user was notified about new listings that match their search alert.

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")

    # Relationships
    user: "User" = Relationship(back_populates="search_alerts")
