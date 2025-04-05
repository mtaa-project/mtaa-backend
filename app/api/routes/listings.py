from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import asc, desc, select

from app.api.dependencies import get_async_session, get_user, get_user_db
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.favorite_listing_model import FavoriteListing
from app.models.listing_model import Listing
from app.models.user_model import User
from app.schemas.listing_schema import (
    ListingCardDetails,
    ListingCardProfile,
    ListingCreate,
    ListingUpdate,
    SellerInfoCard,
    listingQueryParameters,
)

router = APIRouter(prefix="/listings", tags=["listings"])


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


# TODO: change this so that pictures can be uploaded, change response model, and change ListingCreate schema to take pictures
# create listing
@router.post(
    "/",
    response_model=ListingCardDetails,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
    description="Creates a listing with optional address and category assignments. Requires a valid seller ID.",
)
async def create_listing(
    *,
    new_listing_data: ListingCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_user_db),
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
    new_listing = Listing(
        title=new_listing_data.title,
        description=new_listing_data.description,
        price=new_listing_data.price,
        listing_status=new_listing_data.listing_status,
        offer_type=new_listing_data.offer_type,
        address=address,
        seller=user,
        categories=category_objs,
    )

    # add listing to DB session
    session.add(new_listing)
    await session.commit()
    await session.refresh(new_listing)

    return new_listing


# get current user's listings in profile/listings
@router.get(
    "/my-listings",
    response_model=List[ListingCardProfile],
    summary="Get current user's listings",
    description="Fetch all listings created by the current user.",
)
async def get_my_listings(
    *,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_user_db),
):
    # return only posted listings that are not removed
    result = await session.execute(
        select(Listing)
        .where(Listing.seller_id == user.id)
        .where(Listing.listing_status != ListingStatus.REMOVED)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
    )

    listings = result.scalars().all()
    return listings


# TODO: MOVE THIS TO SERVICE CLASS
async def calculate_seller_rating(
    seller_id: int, session: AsyncSession
) -> float | None:
    """
    Helper function to get the seller's rating.
    """
    # return None if seller has no reviews and round the rating to 2 decimal places if the seller has reviews
    statement = (
        select(User)
        .where(User.id == seller_id)
        .options(selectinload(User.reviews_received))
    )

    result = await session.execute(statement)
    seller: User | None = result.scalars().one_or_none()

    if not seller:
        return None

    if len(seller.reviews_received) == 0:
        return None

    rating_total = sum(review.rating for review in seller.reviews_received)
    average_rating = round(rating_total / len(seller.reviews_received), 2)
    return average_rating


# get listings with specific categories, price, status, offer type, and (address)
@router.get(
    "/",
    response_model=List[ListingCardDetails],
    summary="Filter and list listings",
    description="Retrieve listings by categories, price range, offer type, .... Listings with status REMOVED are excluded.",
)
async def get_listings_by_params(
    *,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_user_db),
    params: listingQueryParameters,
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
    # Remove REMOVED & HIDDEN listings
    query = query.where(Listing.listing_status == ListingStatus.ACTIVE)

    if params.category_ids:
        query = query.where(
            Listing.categories.any(Category.id.in_(params.category_ids))
        )
    if params.offer_type:
        query = query.where(Listing.offer_type == params.offer_type)
    if params.listing_status:
        query = query.where(Listing.listing_status == params.listing_status)
    if params.min_price:
        query = query.where(Listing.price >= params.min_price)
    if params.max_price:
        query = query.where(Listing.price <= params.max_price)
    if params.min_rating:
        query = query.where(Listing.rating >= params.min_rating)

    # Searching:
    if params.search:
        query = query.where(Listing.title.ilike(f"%{params.search}%"))

    # Sorting:
    # TODO: sort by updated_at, price, rating, location
    sort_columns = {
        "created_at": Listing.created_at,
        "updated_at": Listing.updated_at,
        "price": Listing.price,
        # "rating": will be done through code
    }

    if params.sort_order == "asc":
        query = query.order_by(
            asc(sort_columns.get(params.sort_by, Listing.updated_at))
        )
    else:
        query = query.order_by(
            desc(sort_columns.get(params.sort_by, Listing.updated_at))
        )

    # Limiting:
    query = query.limit(params.limit)
    query = query.offset(params.offset)

    listings = await session.execute(query)
    listings = listings.scalars().all()

    output_listings: List[ListingCardDetails] = []

    seller_review_dict = {}
    for listing in listings:
        if listing.seller_id not in seller_review_dict:
            seller_review_dict[listing.seller.id] = await calculate_seller_rating(
                listing.seller_id, session=session
            )

    if params.sort_by == "rating":
        listings.sort(
            key=lambda listing: seller_review_dict.get(listing.seller_id) or 0,
            reverse=params.sort_order == "desc",
        )

    for listing in listings:
        output_listings.append(
            ListingCardDetails(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                price=listing.price,
                listing_status=listing.listing_status,
                offer_type=listing.offer_type,
                liked=user.favorite_listings.get(listing.id, False),
                seller=SellerInfoCard(
                    id=listing.seller.id,
                    firstname=listing.seller.firstname,
                    lastname=listing.seller.lastname,
                    rating=seller_review_dict.get(listing.seller_id),
                ),
                address=listing.address,
                categories=listing.categories,
                created_at=listing.created_at,
                updated_at=listing.updated_at,
            )
        )

    return output_listings


# get specific listing by id
@router.get(
    "/{listing_id}",
    # response_model=ListingCardDetails,
    summary="Get a listing by ID",
    description="Fetch a specific listing by ID unless its status is REMOVED.",
)
async def get_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user=Depends(get_user_db),
):
    result = await session.execute(
        select(Listing)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
        .where(Listing.id == listing_id)
    )
    listing = result.scalars().one_or_none()

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

    seller_rating = await calculate_seller_rating(listing.seller_id, session)

    query_is_favorite_listing = select(FavoriteListing).where(
        FavoriteListing.user_id == user.id, FavoriteListing.listing_id == listing.id
    )
    fav_listing_result = await session.execute(query_is_favorite_listing)
    fav_listing_result = fav_listing_result.scalars().one_or_none()
    fav_listing_result = fav_listing_result is not None

    output_listing = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=fav_listing_result,
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
    )

    return output_listing


# update listing
@router.put(
    "/{listing_id}",
    response_model=ListingCardDetails,
    summary="Update an existing listing",
    description="Updates listing fields and category relationships. You must provide valid address/category IDs.",
)
async def update_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    updated_listing_data: ListingUpdate,
    user: User = Depends(get_user_db),
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
    user: User = Depends(get_user_db),
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

    # set listing status to removed
    listing.listing_status = ListingStatus.REMOVED
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


# TODO: make more routes for listing and make them more personalized, and personalized response scheme for every route
