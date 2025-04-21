from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.category_model import Category
from app.models.enums.offer_type import OfferType
from app.schemas.listing_schema import PriceRange


class DeviceToken(BaseModel):
    token: str


class UserSearchAlertBase(SQLModel):
    is_active: bool = Field(default=True)
    product_filters: Dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))


class Categories(BaseModel):
    selected: list[Category]
    not_selected: list[Category]


class UserSearchAlertDetail(BaseModel):
    id: int
    search: str
    is_active: bool
    categoryIds: list[int]
    offer_type: OfferType
    price_range_rent: Optional[PriceRange] = None
    price_range_sale: Optional[PriceRange] = None


class UserSearchAlertGet(BaseModel):
    id: int
    search: str
    is_active: bool


class UserSearchAlertCreate(UserSearchAlertBase):
    id: int
