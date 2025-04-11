from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user_model import User


class FirebaseCloudToken(SQLModel, table=True):
    __tablename__ = "firebaseCloudTokens"

    id: int = Field(default=None, primary_key=True)
    token: str = Field(index=True, nullable=False)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")

    # Relationships
    user: "User" = Relationship(back_populates="firebase_cloud_tokens")
