from ast import Dict
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Json
from sqlalchemy import JSON, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_model import User


class UserSearchAlert(SQLModel, table=True):
    __tablename__ = "userSearchAlerts"

    id: int = Field(default=None, primary_key=True)

    # data: dict = Field(sa_column=Column(JSON), default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime]

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    user: Optional["User"] = Relationship(back_populates="search_alerts")
