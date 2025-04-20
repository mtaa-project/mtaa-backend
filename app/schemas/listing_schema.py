from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic_extra_types.coordinate import Latitude, Longitude
from pydantic_extra_types.country import CountryAlpha2
from sqlmodel import Field, SQLModel

from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.schemas.address_schema import AddressBase
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
    listing_status: ListingStatus
    offer_type: OfferType


# Schema for displaying users own listing data in Profile
class ListingCardProfile(ListingBase):
    id: int

    # extra information for listing cards that can be used to display in profile
    address: Address
    created_at: datetime
    updated_at: datetime
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
    address: Address
    categories: list["Category"]  # list of category ids
    created_at: datetime
    updated_at: datetime | None

    description: Optional[str] = Field(default=None, exclude=True)


# Schema for displaying listing data in medium and big cards
# this is used to read listing data from the database
class ListingCardDetails(ListingCard):
    description: str
    image_paths: list[str]
    distance_from_user: float | None = None  # distance from user location


# schema for listing creation
class ListingCreate(ListingBase):
    description: str
    address: AddressBase | None = None  # address info for creating new address
    category_ids: list[int]  # list of category ids
    image_paths: list[str]


# schema for listing update
class ListingUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    offer_type: OfferType | None = None
    address: AddressBase | None = None  # address info for creating new address
    category_ids: list[int] | None = None
    # image_paths: list[str] | None


class PriceRange(BaseModel):
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)


class AlertQuery(BaseModel):
    offer_type: OfferType  # filter by offer type: RENT, SELL (BOTH is NOT supported)
    category_ids: List[int] | None = None
    # listing_status: ListingStatus = ListingStatus.ACTIVE
    # min_price: int | None = Field(default=None, ge=0)
    # max_price: int | None = Field(default=None, ge=0)
    price_range_rent: PriceRange | None
    price_range_sale: PriceRange | None

    min_rating: float | None = Field(default=None, ge=0)
    time_from: datetime | None = Field(ge=0, le=5, default=None)  # filter by timestamp)

    # sort by options
    sort_by: str = "created_at"  # updated_at, price, rating, location
    sort_order: str = "desc"  # asc, desc
    search: str | None = None

    # location based search
    country: CountryAlpha2 | None = Field(default=None, max_length=2)
    city: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)


class AlertQueryCreate(AlertQuery):
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
