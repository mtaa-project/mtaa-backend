from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.category_model import Category
from app.models.enums.offer_type import OfferType


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
    sale_min: int | None = Field(None, ge=0)
    sale_max: int | None = Field(None, ge=0)
    rent_min: int | None = Field(None, ge=0)
    rent_max: int | None = Field(None, ge=0)


class UserSearchAlertGet(BaseModel):
    id: int
    search: str
    is_active: bool


class UserSearchAlertCreate(UserSearchAlertBase):
    id: int
