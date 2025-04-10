from typing import Optional

from pydantic import BaseModel
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field
from sqlmodel.main import SQLModel


class AddressBase(SQLModel):
    is_primary: bool = Field(default=False)
    visibility: bool = Field(default=True)
    country: CountryAlpha2 | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=255)
    zip_code: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)


class AddressUpdate(SQLModel):
    visibility: bool
    country: Optional[CountryAlpha2] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
