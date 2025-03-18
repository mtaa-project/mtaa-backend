from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    # description: str = Field(max_length=255) TODO: check with the team
    # TODO: define relationship between Category and Listing (Many-to-Many)
