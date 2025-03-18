from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user_model import User


class SaleListing(SQLModel, table=True):
    __tablename__ = "saleListings"

    listing_id: int = Field(foreign_key="listings.id", primary_key=True)
    buyer_id: int = Field(foreign_key="users.id", primary_key=True)
    sold_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )  # TODO: check with team -> date when the listing was sold
