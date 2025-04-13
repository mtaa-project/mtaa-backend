from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.schemas import ListingTransactionBase

if TYPE_CHECKING:
    from app.models.address_model import Address


class SaleListing(SQLModel, ListingTransactionBase, table=True):
    __tablename__ = "saleListings"
    id: int = Field(default=None, primary_key=True)

    buyer_id: int = Field(foreign_key="users.id")
    listing_id: int = Field(foreign_key="listings.id")
    # Foreign keys
    address_id: int = Field(foreign_key="addresses.id")

    sold_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )  # TODO: check with team -> date when the listing was sold
    address: "Address" = Relationship(back_populates="sold_listings")

    __table_args__ = (
        UniqueConstraint("buyer_id", "listing_id", name="uix_buyer_listing"),
    )
