from enum import Enum


class OfferType(str, Enum):
    RENT = "rent"
    SELL = "sell"
    BOTH = "both"
