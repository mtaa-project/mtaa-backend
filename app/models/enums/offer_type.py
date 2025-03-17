from enum import Enum


class OfferType(str, Enum):
    LEND = "lend"
    SELL = "sell"
    BOTH = "both"
