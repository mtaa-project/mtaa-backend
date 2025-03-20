from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SaleListing(SQLModel, table=True):
    __tablename__ = "saleListings"

    listing_id: int = Field(foreign_key="listings.id", primary_key=True, unique=True)
    buyer_id: int = Field(foreign_key="users.id", primary_key=True)
    sold_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )  # TODO: check with team -> date when the listing was sold
