from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_extra_types.coordinate import Latitude, Longitude
from sqlalchemy import func, null
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.dependencies import get_async_session
from app.models.enums.listing_status import ListingStatus
from app.models.listing_model import Listing
from app.models.user_model import User
from app.schemas.listing_schema import ListingCardDetails, SellerInfoCard
from app.services.listing.listing_service import ListingService
from app.services.user.user_service import UserService

router = APIRouter()


# get favorite listings
@router.get(
    "/favorites/my",
    response_model=List[ListingCardDetails],
    summary="Get favorite listings of current user",
    description="Fetch all favorite listings of the current user.",
)
async def get_favorite_listings(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    listing_service: ListingService = Depends(ListingService.get_dependency),
    user_latitude: Latitude | None = None,
    user_longitude: Longitude | None = None,
):
    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    # Get the rating subquery from user_service
    rating_subquery = user_service.get_seller_rating_subquery()
    rating_val = func.coalesce(rating_subquery.c.avg_rating, 0).label("seller_rating")

    query = (
        select(Listing, rating_val)
        .outerjoin(rating_subquery, rating_subquery.c.seller_id == Listing.seller_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.favorite_by),
            selectinload(Listing.images),
        )
        .where(
            Listing.favorite_by.any(User.id == current_user.id),
            Listing.listing_status != ListingStatus.REMOVED,
        )
    )

    if user_latitude is not None or user_longitude is not None:
        if user_latitude is None or user_longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both user latitude and longitude must be provided for location-based filtering.",
            )

        distance_subquery = listing_service.get_listing_distance_subquery(
            user_latitude, user_longitude
        )
        query = query.add_columns(distance_subquery.c.distance).outerjoin(
            distance_subquery,
            distance_subquery.c.listing_id == Listing.id,
        )
    else:
        query = query.add_columns(null().label("distance"))

    result = await session.execute(query)
    listings = result.all()

    output_listings: List[ListingCardDetails] = []
    for listing, seller_rating, distance in listings:
        presigned_urls = listing_service.get_presigned_urls(listing.images)
        output_listings.append(
            ListingCardDetails(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                price=listing.price,
                listing_status=listing.listing_status,
                offer_type=listing.offer_type,
                liked=True,
                seller=SellerInfoCard(
                    id=listing.seller.id,
                    firstname=listing.seller.firstname,
                    lastname=listing.seller.lastname,
                    rating=seller_rating,
                ),
                address=listing.address,
                categories=listing.categories,
                created_at=listing.created_at,
                updated_at=listing.updated_at,
                image_paths=presigned_urls,
                distance_from_user=distance,
            )
        )
    return output_listings


# TESTED for adding listing to favorites and listing already in favorites and not existing
# add listing to favorites
@router.put(
    "/{listing_id}/favorite",
    response_model=ListingCardDetails,
    summary="Add a specific listing to users favorites",
    description="Updates users favorite_listings relationship. You must provide valid listing ID",
)
async def add_favorite(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    listing_service: ListingService = Depends(ListingService.get_dependency),
    user_latitude: Latitude | None = None,
    user_longitude: Longitude | None = None,
):
    # check that listing exists
    result = await session.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.images),
        )
    )
    listing = result.scalars().one_or_none()

    if listing is None or listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that both latitude and longitude are provided
    distance = None
    if user_latitude is not None or user_longitude is not None:
        if user_latitude is None or user_longitude is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both user latitude and longitude must be provided for location-based filtering.",
            )
        distance = listing_service.get_user_listing_distance(
            listing.address.latitude,
            listing.address.longitude,
            user_latitude,
            user_longitude,
        )

    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    # check if listing is already in favorites
    if any(fav.id == listing.id for fav in current_user.favorite_listings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing with ID {listing_id} is already in your favorites.",
        )

    current_user.favorite_listings.append(listing)
    seller_rating = await user_service.get_seller_rating(listing.seller_id)
    presigned_urls = listing_service.get_presigned_urls(listing.images)

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=listing in current_user.favorite_listings,
        seller=SellerInfoCard(
            id=listing.seller_id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=seller_rating,
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        image_paths=presigned_urls,
        distance_from_user=distance,
    )

    # add user to DB session
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return response


# TESTED for removing existing listing from favorites and listing not in favorites and not existing
# remove listing from favorites
@router.delete(
    "/{listing_id}/favorite",
    response_model=ListingCardDetails,
    summary="Remove a specific listing from users favorites",
    description="Updates users favorite_listings relationship. You must provide valid listing ID",
)
async def remove_favorite(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    listing_service: ListingService = Depends(ListingService.get_dependency),
):
    # check that listing exists
    result = await session.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.images),
        )
    )
    listing = result.scalars().one_or_none()

    # check that listing exists
    if not listing or listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    # check that listing is not in favorites
    if not any(fav.id == listing.id for fav in current_user.favorite_listings):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing with ID {listing_id} is not in your favorites.",
        )

    current_user.favorite_listings.remove(listing)
    seller_rating = await user_service.get_seller_rating(listing.seller_id)
    presigned_urls = listing_service.get_presigned_urls(listing.images)
    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=False,
        seller=SellerInfoCard(
            id=listing.seller_id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=seller_rating,
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        image_paths=presigned_urls,
    )

    # add user to DB session
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return response
