from typing import List

from api.dependencies import get_async_session
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.address_model import Address
from app.models.category_listing_model import CategoryListing
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.enums.offer_type import OfferType
from app.models.listing_model import Listing
from app.models.user_model import User
from app.schemas.listing_schema import ListingCreate, ListingRead, ListingUpdate

router = APIRouter(prefix="/listings")


# create listing
@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    *,
    listing_create: ListingCreate,
    session: AsyncSession = Depends(get_async_session),
):
    # check that seller exists
    seller = await session.get(User, listing_create.seller_id)
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seller with ID {listing_create.seller_id} not found.",
        )

    # check that address exists
    if listing_create.address_id:
        address = await session.get(Address, listing_create.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {listing_create.address_id} not found.",
            )

    # check that categories exist
    if listing_create.category_ids:
        for category_id in listing_create.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )

    # create listing instance
    new_listing = Listing.model_validate(listing_create)

    # add listing to DB session
    session.add(new_listing)
    await session.commit()
    await session.refresh(new_listing)

    return new_listing


# get listings with specific categories, price, status, offer type, and (address) visibility
@router.get("/", response_model=List[ListingRead])
async def get_listings_by_category(
    *,
    session: AsyncSession = Depends(get_async_session),
    limit: int = 10,
    category_ids: List[int] | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    listing_status: ListingStatus | None = None,
    offer_type: OfferType | None = None,
    visibility: bool | None = None,
):
    # check that categories exists
    if category_ids:
        for category_id in category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )

    # LISTING STATUS FROM FRONTEND CANNOT BE REMOVED
    assert listing_status != ListingStatus.REMOVED

    # build query
    query = select(Listing)
    if category_ids:
        query = query.where(Listing.categories.any(Category.id.in_(category_ids)))
    if min_price:
        query = query.where(Listing.price >= min_price)
    if max_price:
        query = query.where(Listing.price <= max_price)
    if listing_status:
        query = query.where(Listing.listing_status == listing_status)
    if offer_type:
        query = query.where(Listing.offer_type == offer_type)
    if visibility:
        query = query.join(Address).where(Address.visibility == visibility)

    query = query.limit(limit)

    listings = await session.execute(query)
    listings = listings.scalars().all()

    return listings


# get specific listing by id
@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    listing = await session.get(Listing, listing_id)
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
@router.put("/{listing_id}", response_model=ListingRead)
async def update_listing(
    *,
    listing_id: int,
    listing_update: ListingUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    # check that listing exists
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that address exists
    if listing_update.address_id:
        address = await session.get(Address, listing_update.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {listing_update.address_id} not found.",
            )

    # check that categories exist
    if listing_update.category_ids:
        category_objs = []
        for category_id in listing_update.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )
            category_objs.append(category)

        # Clear existing category links
        await session.exec(
            select(CategoryListing)
            .where(CategoryListing.listing_id == listing.id)
            .delete()
        )

        # Add new category links
        for category in category_objs:
            session.add(CategoryListing(listing_id=listing.id, category_id=category.id))

    # update listing instance
    update_data = listing_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(listing, key, value)

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


# delete listing
@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
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
