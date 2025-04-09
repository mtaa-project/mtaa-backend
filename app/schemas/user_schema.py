from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel

from app.schemas.address_schema import AddressBase, AddressUpdate


class UserBase(SQLModel):
    firstname: str = Field(min_length=1, max_length=255)
    lastname: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, max_length=255)
    phone_number: str | None = Field(default=None, max_length=255)


class UserUpdate(SQLModel):
    firstname: str = Field(min_length=1, max_length=255)
    lastname: str = Field(min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, max_length=255)

    model_config = {"extra": "forbid"}


class UserProfileUpdateRequest(BaseModel):
    user_metadata: UserUpdate
    address_metadata: AddressUpdate


class UserProfileUpdateResponse(BaseModel):
    user_metadata: UserBase
    address_metadata: AddressBase
