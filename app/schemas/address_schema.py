from pydantic import ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field
from sqlmodel.main import SQLModel


class AddressBase(SQLModel):
    model_config = ConfigDict(extra="forbid")
    is_primary: bool = Field(default=False)
    visibility: bool = Field(default=True)
    country: CountryAlpha2 | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str = Field(max_length=10)
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class AddressUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")
    visibility: bool = Field(default=True)
    country: CountryAlpha2 | None = None
    city: str | None = None
    postal_code: str | None = None
    street: str | None = None
