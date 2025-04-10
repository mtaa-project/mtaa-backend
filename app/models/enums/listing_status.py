from enum import Enum


# https://github.com/fastapi/sqlmodel/issues/96#issuecomment-921179607
class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    HIDDEN = "hidden"
    REMOVED = "removed"
    RENTED = "rented"
