from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin import GoogleAuthCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.dependencies import get_async_session, get_firebase_user_from_token
from app.models.user_model import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginUser(BaseModel):
    email: EmailStr
    password: str


class RegisterFormRequest(BaseModel):
    username: str
    firstname: str
    lastname: str
    phone_number: str | None


@router.post("/register")
async def register_user(
    *,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_firebase_user_from_token),
    register_form: RegisterFormRequest,
):
    print(user)
    user_uid = user.get("uid")
    user_email = user.get("email")

    print(user_uid)

    db_user = await session.execute(
        select(User).where(User.username == register_form.username)
    )
    db_user = db_user.scalar_one_or_none()

    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{register_form.username}' is already taken.",
        )

    new_user = User(
        username=register_form.username,
        firstname=register_form.firstname,
        lastname=register_form.lastname,
        email=user_email,
        phone_number=register_form.phone_number or "",
        firebase_uid=user_uid,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/google")
async def google_auth(
    *,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_firebase_user_from_token),
):
    user_uid = user.get("uid")

    db_user = await session.execute(select(User).where(User.firebase_uid == user_uid))
    db_user = db_user.scalar_one_or_none()
    if not db_user:
        user = User()
        user_email = user.get("email")
        phone_number = user.get("phone_number")
        # user_email = user.get("photoURL")
        user_email = user.get("email")
        firstname, lastname = user.get("displayName").split(" ")
        print(user_email, phone_number, user_email, firstname, lastname)
