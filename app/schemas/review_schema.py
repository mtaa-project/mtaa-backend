from pydantic import BaseModel


class ReviewerInfo(BaseModel):
    id: int
    firstname: str
    lastname: str


class ReviewResponse(BaseModel):
    rating: int
    reviewer: ReviewerInfo
