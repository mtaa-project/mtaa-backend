from sqlmodel import Field, SQLModel


class FavoriteListing(SQLModel, table=True):
    __tablename__ = "favoriteListings"

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    listing_id: int = Field(foreign_key="listings.id", primary_key=True)
