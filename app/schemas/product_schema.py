from sqlmodel import SQLModel


class ProductBase(SQLModel):
    name: str
    secret_name: str | None = None
    description: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None


class ProductPublic(ProductBase):
    id: int
