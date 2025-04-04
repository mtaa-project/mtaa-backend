from datetime import datetime, timezone

from sqlalchemy import TIMESTAMP, Column
from sqlmodel import Field, SQLModel


class RentListing(SQLModel, table=True):
    __tablename__ = "rentListings"

    listing_id: int = Field(foreign_key="listings.id", primary_key=True)
    renter_id: int = Field(foreign_key="users.id", primary_key=True)
    start_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    end_date: datetime | None = Field(default=None)  # default to None
