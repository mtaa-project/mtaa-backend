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
    # username: str
    firstname: str
    lastname: str
    email: EmailStr


@router.post("/register")
async def register_user(
    *,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_firebase_user_from_token),
    register_form: RegisterFormRequest,
):
    user_uid = user.get("uid")
    user_email = user.get("email")

    print(register_form)

    db_user = await session.execute(
        select(User).where(User.email == register_form.email)
    )
    db_user = db_user.scalar_one_or_none()

    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{register_form.email}' is already taken.",
        )

    new_user = User(
        # username=register_form.username,
        firstname=register_form.firstname,
        lastname=register_form.lastname,
        email=register_form.email,
        phone_number=None,
        # firebase_uid=user_uid,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/google")
async def google_auth(
    *,
    session: AsyncSession = Depends(get_async_session),
    firebase_user: dict = Depends(get_firebase_user_from_token),
    data: RegisterFormRequest,
):
    firebase_uid = firebase_user.get("uid")
    firebase_email = firebase_user.get("email")
    print(firebase_user)

    result = await session.execute(select(User).where(User.email == firebase_email))
    db_user = result.scalar_one_or_none()

    print("data:")
    print(data)
    print(8 * "-")

    if not db_user:
        new_user = User(
            firstname=data.firstname,
            lastname=data.lastname,
            phone_number=data.phone_number,
            email=firebase_email,
        )
        session.add(new_user)
        await session.commit()
        return {"message": "User created", "user": new_user}

    return {"message": "User already exist", "user": db_user}
