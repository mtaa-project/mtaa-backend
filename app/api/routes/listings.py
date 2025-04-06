from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import asc, desc, select

from app.api.dependencies import get_async_session
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
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
from app.services.user_service import UserService

router = APIRouter(prefix="/listings", tags=["listings"])


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

    if not seller or len(seller.reviews_received) == 0:
        return None

    rating_total = sum(review.rating for review in seller.reviews_received)
    average_rating = round(rating_total / len(seller.reviews_received), 2)
    return average_rating


# TODO: change this so that pictures can be uploaded, change response model, and change ListingCreate schema to take pictures
# TESTED for listing creation
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
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_user()

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
    listing = Listing(
        title=new_listing_data.title,
        description=new_listing_data.description,
        price=new_listing_data.price,
        listing_status=new_listing_data.listing_status,
        offer_type=new_listing_data.offer_type,
        address=address,
        seller=current_user,
        categories=category_objs,
    )

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        # liked=listing in current_user.favorite_listings,
        liked=False,
        seller=SellerInfoCard(
            id=current_user.id,
            firstname=current_user.firstname,
            lastname=current_user.lastname,
            rating=await calculate_seller_rating(current_user.id, session),
        ),
        address=address,
        categories=category_objs,
        # HAVE TO USE THE OBJECTS, OTHERWISE IT WILL TRY TO LAZY LOAD IT FROM listings AND FAIL
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )

    return response


# TESTED for getting listings of user that has listings
# TODO: add test for user that has no listings
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
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_user()

    # return only posted listings that are not removed
    result = await session.execute(
        select(Listing)
        .where(Listing.seller_id == current_user.id)
        .where(Listing.listing_status != ListingStatus.REMOVED)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
    )

    listings = result.scalars().all()
    return listings


# get favorite listings
@router.get(
    "/my-favorites",
    response_model=List[ListingCardDetails],
    summary="Get favorite listings of current user",
    description="Fetch all favorite listings of the current user.",
)
async def get_favorite_listings(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_user(dependencies=["favorite_listings"])

    # return only posted listings that are not removed
    result = await session.execute(
        select(Listing)
        .where(Listing.favorite_by.any(User.id == current_user.id))
        .where(Listing.listing_status != ListingStatus.REMOVED)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.favorite_by),
        )
    )

    listings = result.scalars().all()

    seller_review_dict = {}
    for listing in listings:
        if listing.seller_id not in seller_review_dict:
            seller_review_dict[listing.seller_id] = await calculate_seller_rating(
                listing.seller_id, session=session
            )

    output_listings: List[ListingCardDetails] = []
    for listing in listings:
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
                    rating=seller_review_dict.get(listing.seller_id),
                ),
                address=listing.address,
                categories=listing.categories,
                created_at=listing.created_at,
                updated_at=listing.updated_at,
            )
        )

    return output_listings


# TESTED for using limit, offset, offer_types, listing_status
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
    user_service: UserService = Depends(UserService.get_dependency),
    params: Annotated[listingQueryParameters, Depends()],
):
    current_user = await user_service.get_user(dependencies=["favorite_listings"])

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
    query = select(Listing).options(
        selectinload(Listing.seller),
        selectinload(Listing.categories),
        selectinload(Listing.address),
    )
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

    # Searching:
    if params.search:
        query = query.where(Listing.title.ilike(f"%{params.search}%"))

    # Sorting:
    # TODO: sort by location
    sort_columns = {
        "created_at": Listing.created_at,
        "updated_at": Listing.updated_at,
        "price": Listing.price,
    }

    if params.sort_order == "asc":
        query = query.order_by(
            asc(sort_columns.get(params.sort_by, Listing.updated_at))
        )
    else:
        query = query.order_by(
            desc(sort_columns.get(params.sort_by, Listing.updated_at))
        )

    listings = await session.execute(query)
    listings = listings.scalars().all()

    output_listings: List[ListingCardDetails] = []

    seller_review_dict = {}
    for listing in listings:
        if listing.seller_id not in seller_review_dict:
            seller_review_dict[listing.seller_id] = await calculate_seller_rating(
                listing.seller_id, session=session
            )

    # Treats None in listing as 0
    if params.min_rating:
        listings = [
            listing
            for listing in listings
            if (seller_review_dict.get(listing.seller_id) or 0) >= params.min_rating
        ]

    if params.sort_by == "rating":
        listings.sort(
            key=lambda listing: seller_review_dict.get(listing.seller_id),
            reverse=(params.sort_order == "desc"),
        )

    # TODO: Check if this can be done faster for better performance
    # Limiting + Offset for pagination:
    listings = listings[params.offset : params.offset + params.limit]

    favorites_dict = {fav.id: fav for fav in current_user.favorite_listings}

    for listing in listings:
        output_listings.append(
            ListingCardDetails(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                price=listing.price,
                listing_status=listing.listing_status,
                offer_type=listing.offer_type,
                liked=listing.id in favorites_dict,
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


# TESTED for getting specific listing by id
# get specific listing by id
@router.get(
    "/{listing_id}",
    response_model=ListingCardDetails,
    summary="Get a listing by ID",
    description="Fetch a specific listing by ID unless its status is REMOVED.",
)
async def get_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_user(dependencies=["favorite_listings"])

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

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=listing in current_user.favorite_listings,
        seller=SellerInfoCard(
            id=listing.seller.id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=await calculate_seller_rating(listing.seller_id, session),
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )

    return response


# TESTED title, description, price, listing_status, offer)type, address_id, category_ids
# update listing
@router.put(
    "/update/{listing_id}",
    response_model=ListingCardDetails,
    summary="Update an existing listing",
    description="Updates listing fields and category relationships. You must provide valid address/category IDs.",
)
async def update_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    updated_listing_data: ListingUpdate,
):
    current_user = await user_service.get_user(dependencies=["favorite_listings"])

    # check that listing exists
    result = await session.execute(
        select(Listing)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
        .where(Listing.id == listing_id)
        .where(Listing.listing_status != ListingStatus.REMOVED)
    )

    listing = result.scalars().one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found",
        )

    # check that user is logged in and is the seller of the listing
    if current_user.id != listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this listing.",
        )

    # check that address exists
    if updated_listing_data.address_id is not None:
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
    update_data = updated_listing_data.model_dump(
        exclude_unset=True, exclude={"category_ids"}
    )

    for key, value in update_data.items():
        setattr(listing, key, value)

    # TEMP NEEDS TO BE HERE AS updated_at will be marked as expired and lazy loaded otherwise
    temp = listing.updated_at
    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=listing in current_user.favorite_listings,
        seller=SellerInfoCard(
            id=listing.seller.id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=await calculate_seller_rating(listing.seller_id, session),
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=temp,
    )

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)

    return response


# TESTED for adding existing listing to favorites
# add listing to favorites
@router.put(
    "/add-favorite/{listing_id}",
    response_model=ListingCardDetails,
    summary="Add a specific listing to users favorites",
    description="Updates users favorite_listings relationship. You must provide valid listing ID",
)
async def add_favorite(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    # check that listing exists
    result = await session.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
    )
    listing = result.scalars().one_or_none()

    if not listing or listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    current_user = await user_service.get_user(dependencies=["favorite_listings"])

    # check that listing is not already in favorites
    if listing in current_user.favorite_listings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Listing with ID {listing_id} is already in your favorites.",
        )

    current_user.favorite_listings.append(listing)

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
            rating=await calculate_seller_rating(listing.seller_id, session),
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )

    # add user to DB session
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return response


# remove listing from favorites
@router.delete(
    "/remove-favorite/{listing_id}",
    response_model=ListingCardDetails,
    summary="Remove a specific listing from users favorites",
    description="Updates users favorite_listings relationship. You must provide valid listing ID",
)
async def remove_favorite(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    # check that listing exists
    result = await session.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
        )
    )
    listing = result.scalars().one_or_none()

    # check that listing exists
    if not listing or listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    current_user = await user_service.get_user(dependencies=["favorite_listings"])

    # check that listing is in favorites
    if listing not in current_user.favorite_listings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} is not in your favorites.",
        )

    current_user.favorite_listings.remove(listing)

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
            rating=await calculate_seller_rating(listing.seller_id, session),
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )

    # add user to DB session
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return response


# TESTED removing
# delete listing
@router.delete(
    "/delete/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a listing",
    description="Marks the listing as REMOVED. It will no longer be visible to users.",
)
async def delete_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_user()

    # check that listing exists
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that user is logged in and is the seller of the listing
    if current_user.id != listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this listing.",
        )

    # set listing status to removed
    listing.listing_status = ListingStatus.REMOVED
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing
