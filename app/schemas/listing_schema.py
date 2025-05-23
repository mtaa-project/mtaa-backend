from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional, Union

from pydantic import BaseModel, ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field, SQLModel

from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.schemas.address_schema import AddressGet, NewAddress, ProfileAddressRef
from app.schemas.transaction_schema import ListingTransactionBase


# Seller info schema
# this is used to display seller info in listing cards
class SellerInfoCard(SQLModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    firstname: str
    lastname: str
    rating: float | None = None


class SellerInfoExpanded(SellerInfoCard):
    phone_number: str | None = None
    email: str


# Basic schema for listing data
class ListingBase(SQLModel, ListingTransactionBase):
    model_config = ConfigDict(extra="forbid")
    listing_status: ListingStatus = Field(default=ListingStatus.ACTIVE)
    offer_type: OfferType


# Schema for displaying users own listing data in Profile
class ListingCardProfile(ListingBase):
    id: int
    # extra information for listing cards that can be used to display in profile
    image_path: str


class ListingCardCreate(ListingBase):
    id: int
    image_paths: list[str]


# Schema for displaying listing data in medium and big cards
# this is used to read listing data from the database
class ListingCard(ListingBase):
    id: int

    # user specific information
    liked: bool
    seller: SellerInfoCard
    # images: List[ListingImage]

    # extra information for listing cards that can be used for filtering and sorting
    address: AddressGet
    category_ids: list[int]  # list of category ids
    created_at: datetime
    description: Optional[str] = Field(default=None, exclude=True)


# Schema for displaying listing data in medium and big cards
# this is used to read listing data from the database
class ListingCardDetails(ListingCard):
    description: str
    image_paths: list[str]
    distance_from_user: float | None = None  # distance from user location


AddressUnion = Annotated[
    Union[ProfileAddressRef, NewAddress],
    Field(..., discriminator="address_type"),
]


# schema for listing creation
class ListingCreate(ListingBase):
    address: AddressUnion
    category_ids: list[int]
    image_paths: list[str]


# schema for listing update
class ListingUpdate(ListingBase):
    # model_config = ConfigDict(extra="forbid")
    title: str
    description: str
    price: Decimal
    offer_type: OfferType
    address: AddressUnion
    category_ids: list[int]
    image_paths: list[str]


class AlertQuery(BaseModel):
    offer_type: OfferType = (
        OfferType.BOTH
    )  # filter by offer type: RENT, SELL (BOTH is NOT supported)
    category_ids: List[int] | None = None
    sale_min: int | None = Field(None, ge=0)
    sale_max: int | None = Field(None, ge=0)
    rent_min: int | None = Field(None, ge=0)
    rent_max: int | None = Field(None, ge=0)

    min_rating: float | None = Field(default=None, ge=0)
    time_from: datetime | None = Field(default=None)  # filter by timestamp)

    # sort by options
    sort_by: str = "created_at"  # updated_at, price, rating, location
    sort_order: str = "desc"  # asc, desc
    search: str | None = None

    # location based search
    country: CountryAlpha2 | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)


class AlertQueryCreate(AlertQuery):
    # time_from: None = Field(
    #     default=None, exclude=True
    # )  # Forbid setting this field when creating an alert
    device_push_token: str


class ListingQueryParameters(AlertQuery):
    limit: int = 10
    offset: int = 0

    user_latitude: Latitude | None = None
    user_longitude: Longitude | None = None
    max_distance: float | None = None  # same as radius, in km


class ProfileStatistics(SQLModel):
    model_config = ConfigDict(extra="forbid")
    total_lent: int = Field(default=0, ge=0)
    total_sold: int = Field(default=0, ge=0)
