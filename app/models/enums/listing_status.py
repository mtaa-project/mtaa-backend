from enum import Enum


# https://github.com/fastapi/sqlmodel/issues/96#issuecomment-921179607
class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    HIDDEN = "hidden"
    REMOVED = "removed"
    # ked pride end date cas vratenia presunie sa do stavu active
    RENTED = "rented"
