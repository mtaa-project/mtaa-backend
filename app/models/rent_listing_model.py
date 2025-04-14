from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Column
from sqlmodel import Field, Relationship, SQLModel

from app.schemas import ListingTransactionBase

if TYPE_CHECKING:
    from app.models.address_model import Address


class RentListing(SQLModel, ListingTransactionBase, table=True):
    __tablename__ = "rentListings"
    id: int = Field(default=None, primary_key=True)

    # Foreign keys
    buyer_id: int = Field(foreign_key="users.id")
    listing_id: int = Field(foreign_key="listings.id")
    address_id: int = Field(foreign_key="addresses.id")

    start_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    end_date: datetime | None = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    address: "Address" = Relationship(back_populates="rented_listings")
