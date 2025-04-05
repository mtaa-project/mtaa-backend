from enum import Enum


class OfferType(str, Enum):
    RENT = "rent"
    BUY = "buy"
    BOTH = "both"
