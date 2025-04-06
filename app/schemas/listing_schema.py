from datetime import datetime
from decimal import Decimal
from typing import List

from sqlmodel import SQLModel

from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType


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


# Schema for images of listings used in listing cards and listing details
# class ListingImage(SQLModel):
#     id: int
#     url: str
#     description: str | None = None
#     listing_id: int
#     is_primary: bool = True


# Basic schema for listing data
class ListingBase(SQLModel):
    title: str
    price: Decimal
    listing_status: ListingStatus
    offer_type: OfferType


# Schema for displaying users own listing data in Profile
class ListingCardProfile(ListingBase):
    id: int
    description: str

    # extra information for listing cards that can be used to display in profile
    address: Address
    created_at: datetime
    updated_at: datetime


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


# Schema for displaying listing data in medium and big cards
# this is used to read listing data from the database
class ListingCardDetails(ListingCard):
    description: str


# schema for listing creation
class ListingCreate(ListingBase):
    description: str
    address_id: int  # address visibility is handled in the address model
    category_ids: list[int]  # list of category ids


# schema for listing update
class ListingUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    listing_status: ListingStatus | None = None
    offer_type: OfferType | None = None
    address_id: int | None = None
    category_ids: list[int] | None = None


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
    search_location: str | None = None
    search_radius: int | None = None


class ProfileStatistics(SQLModel):
    total_lent: int = 0
    total_sold: int = 0
