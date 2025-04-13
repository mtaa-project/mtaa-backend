from typing import Optional

from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field
from sqlmodel.main import SQLModel


class AddressBase(SQLModel):
    is_primary: bool = Field(default=False)
    visibility: bool = Field(default=True)
    country: CountryAlpha2 | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str = Field(max_length=10)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)


class AddressUpdate(SQLModel):
    visibility: bool
    country: Optional[CountryAlpha2] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    street: Optional[str] = None
