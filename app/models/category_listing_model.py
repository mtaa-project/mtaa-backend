from sqlmodel import Field, SQLModel


class CategoryListing(SQLModel, table=True):
    __tablename__ = "categoriesListing"

    # Foreign keys
    category_id: int = Field(foreign_key="categories.id")
    listing_id: int = Field(foreign_key="listings.id")
