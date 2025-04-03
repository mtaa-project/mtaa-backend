from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session, get_user
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.listing_model import Listing
from app.models.user_model import User
from app.schemas.listing_schema import (
    ListingCreate,
    ListingUpdate,
    ListingView,
    getParameters,
)

router = APIRouter(prefix="/listings")


# async def get_listing_from_db(listing_id: int, session: AsyncSession) -> Listing:
#     """
#     Helper function to get a listing from the database.
#     """
#     result = await session.execute(
#         select(Listing)
#         .where(Listing.id == listing_id)
#         .options(
#             selectinload(Listing.address),
#             selectinload(Listing.categories),
#             selectinload(Listing.seller),
#             selectinload(Listing.favorite_by),
#             selectinload(Listing.renters),
#             selectinload(Listing.buyer),
#         )
#     )

#     return result.scalar_one_or_none()


# create listing
@router.post(
    "/",
    response_model=ListingView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
    description="Creates a listing with optional address and category assignments. Requires a valid seller ID.",
)
async def create_listing(
    *,
    new_listing_data: ListingCreate = Body(
        ...,
        example={
            "title": "Electric Scooter",
            "description": "Battery-powered scooter in great condition.",
            "price": 250.00,
            "listing_status": "ACTIVE",
            "offer_type": "SELL",
            "address_id": 2,
            "category_ids": [3, 5],
        },
    ),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_user),
):
    # check that address exists
    if new_listing_data.address_id:
        address = await session.get(Address, new_listing_data.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {new_listing_data.address_id} not found.",
            )

    # check that categories exist and collect them
    category_objs = []
    if new_listing_data.category_ids:
        for category_id in new_listing_data.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )
            category_objs.append(category)

    # create listing instance
    # all fields that are in Listing model are copied to the Listing instance, fields that are not in the model are ignored (category_ids, address_id)
    new_listing = Listing.model_validate(new_listing_data)
    new_listing.seller_id = user.id
    new_listing.categories = category_objs

    # add listing to DB session
    session.add(new_listing)
    await session.commit()
    await session.refresh(new_listing)

    return new_listing


# get current user's listings
@router.get(
    "/my-listings",
    response_model=List[ListingView],
    summary="Get current user's listings",
    description="Fetch all listings created by the current user.",
)
async def get_my_listings(
    *,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_user),
):
    email = user.get("email")
    result = await session.exec(select(User).where(User.email == email))
    db_user = result.first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found in DB")

    listings = await session.exec(
        select(Listing).where(Listing.seller_id == db_user.id)
    )

    return listings.scalars().all()


# get listings with specific categories, price, status, offer type, and (address)
@router.get(
    "/",
    response_model=List[ListingView],
    summary="Filter and list listings",
    description="Retrieve listings by categories, price range, offer type, .... Listings with status REMOVED are excluded.",
)
async def get_listings_by_category(
    *,
    session: AsyncSession = Depends(get_async_session),
    params: getParameters,
):
    # check that categories exists
    if params.category_ids:
        for category_id in params.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )

    # LISTING STATUS FROM FRONTEND CANNOT BE REMOVED
    if params.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing status cannot be REMOVED when filtering listings.",
        )

    # build query
    query = select(Listing)
    if params.category_ids:
        query = query.where(
            Listing.categories.any(Category.id.in_(params.category_ids))
        )
    if params.min_price:
        query = query.where(Listing.price >= params.min_price)
    if params.max_price:
        query = query.where(Listing.price <= params.max_price)
    if params.listing_status:
        query = query.where(Listing.listing_status == params.listing_status)
    if params.offer_type:
        query = query.where(Listing.offer_type == params.offer_type)

    query = query.limit(params.limit)
    query = query.offset(params.offset)

    listings = await session.execute(query)
    listings = listings.scalars().all()

    return listings


# get specific listing by id
@router.get(
    "/{listing_id}",
    response_model=ListingView,
    summary="Get a listing by ID",
    description="Fetch a specific listing by ID unless its status is REMOVED.",
)
async def get_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.favorite_by),
            selectinload(Listing.renters),
            selectinload(Listing.buyer),
        )
    )
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that listing is not removed
    if listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} has been removed.",
        )

    return listing


# update listing
@router.put(
    "/{listing_id}",
    response_model=ListingView,
    summary="Update an existing listing",
    description="Updates listing fields and category relationships. You must provide valid address/category IDs.",
)
async def update_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    updated_listing_data: ListingUpdate,
    user: User = Depends(get_user),
):
    # check that listing exists
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that user is logged in and is the seller of the listing
    if user.id != listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this listing.",
        )

    # check that address exists
    if updated_listing_data.address_id:
        address = await session.get(Address, updated_listing_data.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {updated_listing_data.address_id} not found.",
            )

        listing.address = address

    # check that categories exist
    if updated_listing_data.category_ids:
        category_objs = []
        for category_id in updated_listing_data.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )
            category_objs.append(category)

        listing.categories = category_objs

    # update listing instance
    update_data = updated_listing_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(listing, key, value)

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


# delete listing
@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a listing",
    description="Marks the listing as REMOVED. It will no longer be visible to users.",
)
async def delete_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    # check that listing exists
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # set listing status to removed
    listing.listing_status = ListingStatus.REMOVED
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing
