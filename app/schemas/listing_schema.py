from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import File, UploadFile
from pydantic import conlist
from sqlmodel import Field, SQLModel
from typing_extensions import Annotated

from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.schemas.address_schema import AddressBase
from app.schemas.transaction_schema import ListingTransactionBase


# Seller info schema
# this is used to display seller info in listing cards
class SellerInfoCard(SQLModel):
    id: int
    firstname: str
    lastname: str
    rating: float | None = None


class SellerInfoExpanded(SellerInfoCard):
    phone_number: str | None = None
    email: str


# Basic schema for listing data
class ListingBase(SQLModel, ListingTransactionBase):
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
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    offer_type: OfferType | None = None
    address: AddressBase | None = None  # address info for creating new address
    category_ids: list[int] | None = None
    # image_paths: list[str] | None


class ListingQueryParameters(SQLModel):
    limit: int = 10
    offset: int = 0
    category_ids: List[int] | None = None
    offer_type: OfferType  # filter by offer type: RENT, SELL (BOTH is NOT supported)
    listing_status: ListingStatus = ListingStatus.ACTIVE
    min_price: int | None = None
    max_price: int | None = None
    min_rating: float | None = None

    # sort by options
    sort_by: str = "created_at"  # updated_at, price, rating, location
    sort_order: str = "desc"  # asc, desc
    search: str | None = None

    # location based search
    user_latitude: float | None = None
    user_longitude: float | None = None
    max_distance: float | None = None  # same as radius, in km


class ProfileStatistics(SQLModel):
    total_lent: int = 0
    total_sold: int = 0
